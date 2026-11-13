"""Hauptklasse des Plugins: Menüeintrag, Werkzeugleisten-Knopf, Ablauf der Prüfung."""
import os
from collections import Counter

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsField, QgsFields,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol, QgsGeometry,
    QgsVectorFileWriter, QgsWkbTypes, QgsApplication,
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import sip

from . import checks
from .dialog import NetzQADialog
from .i18n import tr
from .netz_qa_processing import NetzQAProvider

# Kompatibel mit QGIS 3.x und 4.x
try:
    WRITER_OK = QgsVectorFileWriter.WriterError.NoError
except AttributeError:
    WRITER_OK = QgsVectorFileWriter.NoError
try:
    from qgis.core import Qgis
    NO_GEOMETRY = Qgis.WkbType.NoGeometry
except AttributeError:
    NO_GEOMETRY = QgsWkbTypes.NoGeometry

EXPORT_FORMATE = {".gpkg": "GPKG", ".xlsx": "XLSX", ".csv": "CSV"}

FARBEN_DE = {
    "Ungültige Geometrie": "#8e44ad",
    "Leere Geometrie": "#7f8c8d",
    "Doppelte Geometrie": "#e74c3c",
    "Lücke im Netz": "#f39c12",
    "Leeres Pflichtfeld": "#2980b9",
    "Armatur nicht auf Leitung": "#c0392b",
}


class NetzQAPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self.errors = []
        self.error_layer = None
        self.provider = None

    # --- QGIS ruft diese beiden Methoden beim Laden/Entladen auf ---
    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
        self.action = QAction(icon, "Netz-QA", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("&Netz-QA", self.action)
        self.provider = NetzQAProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginVectorMenu("&Netz-QA", self.action)
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    # --- Ablauf ---
    def run(self):
        if self.dialog is None:
            self.dialog = NetzQADialog(self.iface.mainWindow())
            self.dialog.run_button.clicked.connect(self.start_check)
            self.dialog.export_button.clicked.connect(self.export_errors)
            self.dialog.table.cellDoubleClicked.connect(self.zoom_to_error)
        self.dialog.show()
        self.dialog.raise_()

    def start_check(self):
        d = self.dialog
        layer = d.layer_combo.currentLayer()
        if layer is None:
            d.summary.setText(tr("Bitte zuerst einen Layer auswählen."))
            return

        d.save_settings()
        errors = []
        if d.chk_invalid.isChecked():
            errors += checks.check_invalid(layer)
        if d.chk_dupl.isChecked():
            errors += checks.check_duplicates(layer)
        if d.chk_gaps.isChecked() and d.chk_gaps.isEnabled():
            errors += checks.check_gaps(layer, d.tolerance.value())
        if d.chk_fields.isChecked():
            errors += checks.check_empty_fields(layer, d.field_combo.checkedItems())
        if d.chk_points.isChecked() and d.chk_points.isEnabled():
            line_layer = d.line_combo.currentLayer()
            if line_layer is None:
                d.summary.setText(tr("Bitte einen Leitungslayer auswählen."))
                return
            errors += checks.check_points_on_lines(layer, line_layer,
                                                   d.point_tolerance.value())

        self.errors = errors
        d.show_errors(errors)
        n = layer.featureCount()
        if errors:
            teile = ", ".join(f"{k}: {v}" for k, v in Counter(e[0] for e in errors).items())
            d.summary.setText(tr("{n} Fehler in {total} Objekten – {parts}",
                                 n=len(errors), total=n, parts=teile))
        else:
            d.summary.setText(tr("Keine Fehler gefunden ({total} Objekte geprüft).", total=n))
        self.write_error_layer(layer, errors)

    def write_error_layer(self, layer, errors):
        if self.error_layer is not None:
            # Layer nur entfernen, wenn er noch im Projekt ist (Nutzer kann ihn gelöscht haben)
            layer_id = self.error_layer.id() if not sip.isdeleted(self.error_layer) else None
            if layer_id and QgsProject.instance().mapLayer(layer_id) is not None:
                QgsProject.instance().removeMapLayer(layer_id)
            self.error_layer = None
        if not errors:
            return

        crs = layer.crs().authid()
        vl = QgsVectorLayer(f"Point?crs={crs}", tr("Netz-QA Fehler – {name}", name=layer.name()), "memory")
        fields = QgsFields()
        fields.append(QgsField("fehler_typ", QVariant.String))
        fields.append(QgsField("objekt_id", QVariant.Int))
        fields.append(QgsField("beschreibung", QVariant.String))
        vl.dataProvider().addAttributes(fields)
        vl.updateFields()

        feats = []
        for typ, fid, geom, text in errors:
            if geom is None:
                continue
            f = QgsFeature(vl.fields())
            f.setGeometry(QgsGeometry(geom))
            f.setAttributes([typ, int(fid), text])
            feats.append(f)
        vl.dataProvider().addFeatures(feats)
        vl.updateExtents()

        farben = {tr(k): v for k, v in FARBEN_DE.items()}
        cats = []
        for typ in sorted({e[0] for e in errors}):
            sym = QgsSymbol.defaultSymbol(vl.geometryType())
            sym.setColor(QColor(farben.get(typ, "#000000")))
            sym.setSize(3.5)
            cats.append(QgsRendererCategory(typ, sym, typ))
        vl.setRenderer(QgsCategorizedSymbolRenderer("fehler_typ", cats))

        QgsProject.instance().addMapLayer(vl)
        self.error_layer = vl

    def export_errors(self):
        """Fehlerliste als GeoPackage, Excel oder CSV speichern."""
        d = self.dialog
        if not self.errors:
            d.summary.setText(tr("Keine Fehler zum Exportieren."))
            return
        path, filt = QFileDialog.getSaveFileName(
            d, tr("Fehlerliste exportieren"), "netz_qa_fehler",
            "GeoPackage (*.gpkg);;Excel (*.xlsx);;CSV (*.csv)")
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in EXPORT_FORMATE:
            ext = ".xlsx" if "xlsx" in filt else ".csv" if "csv" in filt else ".gpkg"
            path += ext
        driver = EXPORT_FORMATE[ext]

        layer = d.layer_combo.currentLayer()
        crs = layer.crs().authid() if layer is not None else ""
        vl = QgsVectorLayer(f"Point?crs={crs}", "netz_qa_fehler", "memory")
        fields = QgsFields()
        fields.append(QgsField("fehler_typ", QVariant.String))
        fields.append(QgsField("objekt_id", QVariant.Int))
        fields.append(QgsField("beschreibung", QVariant.String))
        fields.append(QgsField("x", QVariant.Double))
        fields.append(QgsField("y", QVariant.Double))
        vl.dataProvider().addAttributes(fields)
        vl.updateFields()

        feats = []
        for typ, fid, geom, text in self.errors:
            f = QgsFeature(vl.fields())
            x = y = None
            if geom is not None and not geom.isEmpty():
                p = geom.centroid().asPoint()
                x, y = round(p.x(), 3), round(p.y(), 3)
                f.setGeometry(QgsGeometry(geom))
            f.setAttributes([typ, int(fid), text, x, y])
            feats.append(f)
        vl.dataProvider().addFeatures(feats)

        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = driver
        opts.fileEncoding = "UTF-8"
        opts.layerName = "netz_qa_fehler"
        if driver != "GPKG":
            opts.overrideGeometryType = NO_GEOMETRY
        res = QgsVectorFileWriter.writeAsVectorFormatV3(
            vl, path, QgsProject.instance().transformContext(), opts)
        if res[0] == WRITER_OK:
            d.summary.setText(tr("{n} Fehler exportiert: {path}", n=len(self.errors), path=path))
        else:
            d.summary.setText(tr("Export fehlgeschlagen: {msg}", msg=res[1]))

    def zoom_to_error(self, row, _col):
        if row >= len(self.errors):
            return
        geom = self.errors[row][2]
        if geom is None:
            return
        canvas = self.iface.mapCanvas()
        layer = self.dialog.layer_combo.currentLayer()
        g = QgsGeometry(geom)
        dest = canvas.mapSettings().destinationCrs()
        if layer is not None and layer.crs() != dest:
            from qgis.core import QgsCoordinateTransform
            g.transform(QgsCoordinateTransform(layer.crs(), dest, QgsProject.instance()))
        dist = 0.0005 if dest.isGeographic() else 50
        rect = g.buffer(dist, 4).boundingBox()
        canvas.setExtent(rect)
        canvas.refresh()
        if layer is not None:
            layer.selectByIds([int(self.errors[row][1])])
