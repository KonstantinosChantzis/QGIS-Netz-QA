"""Dialogfenster von Netz-QA (ohne .ui-Datei, damit alles in Python nachvollziehbar ist)."""
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QCheckBox, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QHeaderView, QAbstractItemView,
)
from qgis.gui import QgsMapLayerComboBox, QgsCheckableComboBox, QgsDoubleSpinBox
from qgis.core import QgsMapLayerProxyModel

try:  # QGIS >= 3.34
    from qgis.core import Qgis
    VECTOR_FILTER = Qgis.LayerFilter.VectorLayer
except AttributeError:
    VECTOR_FILTER = QgsMapLayerProxyModel.VectorLayer


class NetzQADialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Netz-QA – Qualitätsprüfung für Netzdaten")
        self.resize(720, 560)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(VECTOR_FILTER)
        form.addRow("Layer:", self.layer_combo)

        self.chk_invalid = QCheckBox("Ungültige / leere Geometrien")
        self.chk_dupl = QCheckBox("Doppelte Geometrien")
        self.chk_gaps = QCheckBox("Lücken zwischen Leitungen (nur Linien)")
        self.chk_fields = QCheckBox("Leere Pflichtfelder")
        for c in (self.chk_invalid, self.chk_dupl, self.chk_gaps, self.chk_fields):
            c.setChecked(True)
            form.addRow(c)

        self.tolerance = QgsDoubleSpinBox()
        self.tolerance.setDecimals(2)
        self.tolerance.setRange(0.01, 100.0)
        self.tolerance.setValue(1.0)
        self.tolerance.setSuffix(" m")
        form.addRow("Toleranz für Lücken:", self.tolerance)

        self.field_combo = QgsCheckableComboBox()
        form.addRow("Pflichtfelder:", self.field_combo)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.run_button = QPushButton("Prüfung starten")
        self.close_button = QPushButton("Schließen")
        buttons.addStretch()
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.summary = QLabel("")
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Fehlertyp", "Objekt-ID", "Beschreibung"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        layout.addWidget(QLabel("Doppelklick auf eine Zeile zoomt zum Fehler."))

        self.close_button.clicked.connect(self.close)
        self.layer_combo.layerChanged.connect(self.update_fields)
        self.update_fields(self.layer_combo.currentLayer())

    def update_fields(self, layer):
        self.field_combo.clear()
        if layer is None:
            return
        self.field_combo.addItems([f.name() for f in layer.fields()])
        is_line = False
        try:
            from .checks import GT_LINE
            is_line = layer.geometryType() == GT_LINE
        except Exception:
            pass
        self.chk_gaps.setEnabled(is_line)

    def show_errors(self, errors):
        self.table.setRowCount(len(errors))
        for row, (typ, fid, _geom, text) in enumerate(errors):
            self.table.setItem(row, 0, QTableWidgetItem(typ))
            self.table.setItem(row, 1, QTableWidgetItem(str(fid)))
            self.table.setItem(row, 2, QTableWidgetItem(text))
        self.table.resizeColumnToContents(0)
