"""Dialogfenster von Netz-QA (ohne .ui-Datei, damit alles in Python nachvollziehbar ist)."""
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QCheckBox, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QHeaderView, QAbstractItemView,
)
from qgis.gui import QgsMapLayerComboBox, QgsCheckableComboBox, QgsDoubleSpinBox
from qgis.core import QgsMapLayerProxyModel, QgsSettings

from .i18n import tr

try:  # QGIS >= 3.34
    from qgis.core import Qgis
    VECTOR_FILTER = Qgis.LayerFilter.VectorLayer
    LINE_FILTER = Qgis.LayerFilter.LineLayer
except AttributeError:
    VECTOR_FILTER = QgsMapLayerProxyModel.VectorLayer
    LINE_FILTER = QgsMapLayerProxyModel.LineLayer


class NetzQADialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Netz-QA – Qualitätsprüfung für Netzdaten"))
        self.resize(720, 560)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(VECTOR_FILTER)
        form.addRow(tr("Layer:"), self.layer_combo)

        self.chk_invalid = QCheckBox(tr("Ungültige / leere Geometrien"))
        self.chk_dupl = QCheckBox(tr("Doppelte Geometrien"))
        self.chk_gaps = QCheckBox(tr("Lücken zwischen Leitungen (nur Linien)"))
        self.chk_fields = QCheckBox(tr("Leere Pflichtfelder"))
        self.chk_points = QCheckBox(tr("Armaturen auf Leitung (nur Punkte)"))
        for c in (self.chk_invalid, self.chk_dupl, self.chk_gaps, self.chk_fields,
                  self.chk_points):
            c.setChecked(True)
            form.addRow(c)

        self.tolerance = QgsDoubleSpinBox()
        self.tolerance.setDecimals(2)
        self.tolerance.setRange(0.01, 100.0)
        self.tolerance.setValue(1.0)
        self.tolerance.setSuffix(" m")
        form.addRow(tr("Toleranz für Lücken:"), self.tolerance)

        self.line_combo = QgsMapLayerComboBox()
        self.line_combo.setFilters(LINE_FILTER)
        form.addRow(tr("Leitungslayer:"), self.line_combo)

        self.point_tolerance = QgsDoubleSpinBox()
        self.point_tolerance.setDecimals(3)
        self.point_tolerance.setRange(0.0, 100.0)
        self.point_tolerance.setValue(0.01)
        self.point_tolerance.setSuffix(" m")
        form.addRow(tr("Toleranz für Armaturen:"), self.point_tolerance)

        self.field_combo = QgsCheckableComboBox()
        form.addRow(tr("Pflichtfelder:"), self.field_combo)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.run_button = QPushButton(tr("Prüfung starten"))
        self.export_button = QPushButton(tr("Fehlerliste exportieren…"))
        self.export_button.setEnabled(False)
        self.close_button = QPushButton(tr("Schließen"))
        buttons.addStretch()
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.export_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.summary = QLabel("")
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([tr("Fehlertyp"), tr("Objekt-ID"), tr("Beschreibung")])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        layout.addWidget(QLabel(tr("Doppelklick auf eine Zeile zoomt zum Fehler.")))

        self.close_button.clicked.connect(self.close)
        self.layer_combo.layerChanged.connect(self.update_fields)
        self.update_fields(self.layer_combo.currentLayer())
        self.load_settings()

    # --- Einstellungen merken (bleiben nach Neustart von QGIS erhalten) ---
    def _checkboxes(self):
        return {"invalid": self.chk_invalid, "duplicates": self.chk_dupl, "gaps": self.chk_gaps,
                "fields": self.chk_fields, "points": self.chk_points}

    def load_settings(self):
        s = QgsSettings()
        for key, box in self._checkboxes().items():
            box.setChecked(s.value(f"netz_qa/check_{key}", box.isChecked(), type=bool))
        self.tolerance.setValue(s.value("netz_qa/gap_tolerance", self.tolerance.value(), type=float))
        self.point_tolerance.setValue(
            s.value("netz_qa/point_tolerance", self.point_tolerance.value(), type=float))

    def save_settings(self):
        s = QgsSettings()
        for key, box in self._checkboxes().items():
            s.setValue(f"netz_qa/check_{key}", box.isChecked())
        s.setValue("netz_qa/gap_tolerance", self.tolerance.value())
        s.setValue("netz_qa/point_tolerance", self.point_tolerance.value())

    def update_fields(self, layer):
        self.field_combo.clear()
        if layer is None:
            return
        self.field_combo.addItems([f.name() for f in layer.fields()])
        from .checks import GT_LINE, GT_POINT
        is_line = layer.geometryType() == GT_LINE
        is_point = layer.geometryType() == GT_POINT
        self.chk_gaps.setEnabled(is_line)
        self.chk_points.setEnabled(is_point)
        self.line_combo.setEnabled(is_point)
        self.point_tolerance.setEnabled(is_point)

    def show_errors(self, errors):
        self.table.setRowCount(len(errors))
        for row, (typ, fid, _geom, text) in enumerate(errors):
            self.table.setItem(row, 0, QTableWidgetItem(typ))
            self.table.setItem(row, 1, QTableWidgetItem(str(fid)))
            self.table.setItem(row, 2, QTableWidgetItem(text))
        self.table.resizeColumnToContents(0)
        self.export_button.setEnabled(len(errors) > 0)
