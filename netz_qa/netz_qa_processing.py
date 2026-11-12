"""Processing-Anbindung von Netz-QA: die Prüfungen als Algorithmus in der
Processing-Toolbox, im Grafischen Modellierer und in der Stapelverarbeitung."""
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingProvider, QgsProcessingException,
    QgsProcessingParameterVectorLayer, QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber, QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink, QgsProcessingOutputNumber,
    QgsFields, QgsField, QgsFeature, QgsFeatureSink, QgsGeometry, QgsWkbTypes,
)

from . import checks
from .i18n import tr, is_german, EN

# Kompatibel mit QGIS 3.x und 4.x
try:
    from qgis.core import Qgis
    TYPE_ANY = Qgis.ProcessingSourceType.VectorAnyGeometry
    TYPE_LINE = Qgis.ProcessingSourceType.VectorLine
    NUM_DOUBLE = Qgis.ProcessingNumberParameterType.Double
    FIELD_ANY = Qgis.ProcessingFieldParameterDataType.Any
    WKB_POINT = Qgis.WkbType.Point
except AttributeError:
    TYPE_ANY = QgsProcessing.TypeVectorAnyGeometry
    TYPE_LINE = QgsProcessing.TypeVectorLine
    NUM_DOUBLE = QgsProcessingParameterNumber.Double
    FIELD_ANY = QgsProcessingParameterField.Any
    WKB_POINT = QgsWkbTypes.Point
try:
    FAST_INSERT = QgsFeatureSink.Flag.FastInsert
except AttributeError:
    FAST_INSERT = QgsFeatureSink.FastInsert

ICON = os.path.join(os.path.dirname(__file__), "icon.png")


class NetzQAAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    CHECK_INVALID = "CHECK_INVALID"
    CHECK_DUPLICATES = "CHECK_DUPLICATES"
    CHECK_GAPS = "CHECK_GAPS"
    GAP_TOLERANCE = "GAP_TOLERANCE"
    CHECK_FIELDS = "CHECK_FIELDS"
    REQUIRED_FIELDS = "REQUIRED_FIELDS"
    CHECK_POINTS = "CHECK_POINTS"
    LINE_LAYER = "LINE_LAYER"
    POINT_TOLERANCE = "POINT_TOLERANCE"
    OUTPUT = "OUTPUT"
    ERROR_COUNT = "ERROR_COUNT"

    def name(self):
        return "netzdaten_pruefen"

    def displayName(self):
        return tr("Netzdaten prüfen")

    def icon(self):
        return QIcon(ICON)

    def shortHelpString(self):
        if is_german():
            return EN["HELP_DE"] + "\n\n" + EN["HELP"]
        return EN["HELP"]

    def createInstance(self):
        return NetzQAAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT, tr("Eingabelayer (Linien oder Punkte)"), [TYPE_ANY]))
        self.addParameter(QgsProcessingParameterBoolean(
            self.CHECK_INVALID, tr("Ungültige / leere Geometrien prüfen"), defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.CHECK_DUPLICATES, tr("Doppelte Geometrien prüfen"), defaultValue=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.CHECK_GAPS, tr("Lücken zwischen Leitungen prüfen (nur Linien)"), defaultValue=True))
        self.addParameter(QgsProcessingParameterNumber(
            self.GAP_TOLERANCE, tr("Toleranz für Lücken (m)"), type=NUM_DOUBLE,
            defaultValue=1.0, minValue=0.0))
        self.addParameter(QgsProcessingParameterBoolean(
            self.CHECK_FIELDS, tr("Leere Pflichtfelder prüfen"), defaultValue=False))
        self.addParameter(QgsProcessingParameterField(
            self.REQUIRED_FIELDS, tr("Pflichtfelder"), parentLayerParameterName=self.INPUT,
            type=FIELD_ANY, allowMultiple=True, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(
            self.CHECK_POINTS, tr("Armaturen auf Leitung prüfen (nur Punkte)"), defaultValue=False))
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.LINE_LAYER, tr("Leitungslayer (für die Armaturen-Prüfung)"), [TYPE_LINE],
            optional=True))
        self.addParameter(QgsProcessingParameterNumber(
            self.POINT_TOLERANCE, tr("Toleranz für Armaturen (m)"), type=NUM_DOUBLE,
            defaultValue=0.01, minValue=0.0))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, tr("Netz-QA Fehler")))
        self.addOutput(QgsProcessingOutputNumber(self.ERROR_COUNT, tr("Anzahl Fehler")))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        if layer is None:
            raise QgsProcessingException(tr("Eingabelayer fehlt."))

        errors = []
        if self.parameterAsBoolean(parameters, self.CHECK_INVALID, context):
            feedback.pushInfo(tr("Prüfe ungültige / leere Geometrien …"))
            errors += checks.check_invalid(layer)
        if self.parameterAsBoolean(parameters, self.CHECK_DUPLICATES, context):
            feedback.pushInfo(tr("Prüfe doppelte Geometrien …"))
            errors += checks.check_duplicates(layer)
        if self.parameterAsBoolean(parameters, self.CHECK_GAPS, context):
            if layer.geometryType() == checks.GT_LINE:
                feedback.pushInfo(tr("Prüfe Lücken zwischen Leitungen …"))
                tol = self.parameterAsDouble(parameters, self.GAP_TOLERANCE, context)
                errors += checks.check_gaps(layer, tol)
            else:
                feedback.pushInfo(tr("Lückenprüfung übersprungen (kein Linienlayer)."))
        if self.parameterAsBoolean(parameters, self.CHECK_FIELDS, context):
            names = self.parameterAsFields(parameters, self.REQUIRED_FIELDS, context)
            feedback.pushInfo(tr("Prüfe Pflichtfelder: {names}",
                                 names=", ".join(names) or tr("keine gewählt")))
            errors += checks.check_empty_fields(layer, names)
        if self.parameterAsBoolean(parameters, self.CHECK_POINTS, context):
            if layer.geometryType() == checks.GT_POINT:
                line_layer = self.parameterAsVectorLayer(parameters, self.LINE_LAYER, context)
                if line_layer is None:
                    raise QgsProcessingException(
                        tr("Für die Armaturen-Prüfung bitte einen Leitungslayer wählen."))
                feedback.pushInfo(tr("Prüfe Armaturen auf Leitung …"))
                tol = self.parameterAsDouble(parameters, self.POINT_TOLERANCE, context)
                errors += checks.check_points_on_lines(layer, line_layer, tol)
            else:
                feedback.pushInfo(tr("Armaturen-Prüfung übersprungen (kein Punktlayer)."))

        fields = QgsFields()
        fields.append(QgsField("fehler_typ", QVariant.String))
        fields.append(QgsField("objekt_id", QVariant.Int))
        fields.append(QgsField("beschreibung", QVariant.String))
        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT, context, fields,
                                             WKB_POINT, layer.sourceCrs())
        if sink is None:
            raise QgsProcessingException(tr("Ausgabelayer konnte nicht erstellt werden."))

        for typ, fid, geom, text in errors:
            if feedback.isCanceled():
                break
            f = QgsFeature(fields)
            if geom is not None:
                f.setGeometry(QgsGeometry(geom))
            f.setAttributes([typ, int(fid), text])
            sink.addFeature(f, FAST_INSERT)

        feedback.pushInfo(tr("{n} Fehler in {total} Objekten gefunden.",
                             n=len(errors), total=layer.featureCount()))
        return {self.OUTPUT: dest_id, self.ERROR_COUNT: len(errors)}


class NetzQAProvider(QgsProcessingProvider):
    def id(self):
        return "netzqa"

    def name(self):
        return "Netz-QA"

    def icon(self):
        return QIcon(ICON)

    def loadAlgorithms(self):
        self.addAlgorithm(NetzQAAlgorithm())
