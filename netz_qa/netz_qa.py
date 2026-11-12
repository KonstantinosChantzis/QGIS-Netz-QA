"""Hauptklasse des Plugins: Menüeintrag, Werkzeugleisten-Knopf, Ablauf der Prüfung."""
import os
from collections import Counter

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsField, QgsFields,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol, QgsGeometry,
)
from qgis.PyQt.QtCore import QVariant

from . import checks
from .dialog import NetzQADialog

FARBEN = {
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

    # --- QGIS ruft diese beiden Methoden beim Laden/Entladen auf ---
    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
        self.action = QAction(icon, "Netz-QA", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("&Netz-QA", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginVectorMenu("&Netz-QA", self.action)

    # --- Ablauf ---
    def run(self):
        if self.dialog is None:
            self.dialog = NetzQADialog(self.iface.mainWindow())
            self.dialog.run_button.clicked.connect(self.start_check)
            self.dialog.table.cellDoubleClicked.connect(self.zoom_to_error)
        self.dialog.show()
        self.dialog.raise_()

    def start_check(self):
        d = self.dialog
        layer = d.layer_combo.currentLayer()
        if layer is None:
            d.summary.setText("Bitte zuerst einen Layer auswählen.")
            return

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
                d.summary.setText("Bitte einen Leitungslayer auswählen.")
                return
            errors += checks.check_points_on_lines(layer, line_layer,
                                                   d.point_tolerance.value())

        self.errors = errors
        d.show_errors(errors)
        n = layer.featureCount()
        if errors:
            teile = ", ".join(f"{k}: {v}" for k, v in Counter(e[0] for e in errors).items())
            d.summary.setText(f"{len(errors)} Fehler in {n} Objekten – {teile}")
        else:
            d.summary.setText(f"Keine Fehler gefunden ({n} Objekte geprüft).")
        self.write_error_layer(layer, errors)

    def write_error_layer(self, layer, errors):
        if self.error_layer is not None:
            try:
                QgsProject.instance().removeMapLayer(self.error_layer.id())
            except RuntimeError:
                pass
            self.error_layer = None
        if not errors:
            return

        crs = layer.crs().authid()
        vl = QgsVectorLayer(f"Point?crs={crs}", f"Netz-QA Fehler – {layer.name()}", "memory")
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

        cats = []
        for typ in sorted({e[0] for e in errors}):
            sym = QgsSymbol.defaultSymbol(vl.geometryType())
            sym.setColor(QColor(FARBEN.get(typ, "#000000")))
            sym.setSize(3.5)
            cats.append(QgsRendererCategory(typ, sym, typ))
        vl.setRenderer(QgsCategorizedSymbolRenderer("fehler_typ", cats))

        QgsProject.instance().addMapLayer(vl)
        self.error_layer = vl

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
