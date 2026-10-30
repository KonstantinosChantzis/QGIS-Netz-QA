# QGIS Netz-QA – Quality Checks for Utility Network Data

[English](#qgis-netz-qa--quality-checks-for-utility-network-data) | [Deutsch](#deutsch)

**Netz-QA** is a QGIS plugin (Python / PyQGIS) that checks line and point layers of utility networks – water and gas pipes, cables, poles – for typical data errors with one click. All errors are listed in a table, shown as a coloured point layer on the map, and each error can be zoomed to with a double click.

![Netz-QA result: error layer on the map and error table](images/01_netz_qa_result.png)

---

## Checks

| Check | What it finds |
|---|---|
| **Invalid / empty geometries** | Features without geometry or with geometries that are invalid according to GEOS |
| **Duplicate geometries** | Two or more features with exactly the same geometry (e.g. a pipe digitised twice) |
| **Gaps in the network** (lines only) | Line ends that lie closer than a tolerance (e.g. 1 m) to another line but do not touch it – typical digitising errors. Real network ends further away are **not** reported. |
| **Empty required fields** | Features where selected attributes (e.g. material, diameter) are empty |

## Test result

The repository contains a test network (13 pipes in Essen, EPSG:25832) with built-in errors. Netz-QA found exactly the **6 expected errors** and no false positives:

| Error type | Count | Details |
|---|---|---|
| Duplicate geometry | 1 | Pipe 10 = copy of pipe 6 |
| Gap in the network | 2 | 0.60 m and 0.40 m |
| Empty required field | 3 | material and/or diameter missing |

---

## Installation

1. Download this repository as ZIP (**Code → Download ZIP**) and unpack it
2. Zip only the folder `netz_qa` (so that the ZIP contains `netz_qa/…`)
3. QGIS → **Plugins → Manage and Install Plugins → Install from ZIP** → select the ZIP
4. A green Netz-QA icon appears in the toolbar and under **Vector → Netz-QA**

Requirements: QGIS 3.28 or newer (prepared for QGIS 4 / Qt6).

## Usage

1. Load a network layer (or `testdata/netz_testdaten.gpkg`)
2. Open Netz-QA, choose the layer, the checks, the gap tolerance and the required fields
3. Click **Prüfung starten** (start check)
4. Double-click a row in the table to zoom to the error

---

## Technical details

- **PyQGIS**: QgsSpatialIndex for fast neighbour search, GEOS-based validity and equality checks
- **Gap detection**: for each line end, the nearest other line within the tolerance is searched; if it is not touched, a gap is reported (each pair only once)
- **User interface**: Qt dialog written in Python (QgsMapLayerComboBox, QgsCheckableComboBox, QTableWidget)
- **Output**: temporary memory point layer with categorised symbols per error type
- Compatible with QGIS 3.x and 4.x (enum handling for both versions)

## Roadmap

- Topology checks for point layers (nodes / valves not on a pipe)
- Export of the error list to Excel / GeoPackage
- Processing algorithm so the checks can be used in models and batch runs
- Publication in the official QGIS Plugin Repository

---

## Repository structure

```
QGIS-Netz-QA/
├── netz_qa/
│   ├── __init__.py      # plugin entry point
│   ├── netz_qa.py       # main class: menu, toolbar, workflow, error layer
│   ├── checks.py        # check functions
│   ├── dialog.py        # user interface
│   ├── metadata.txt     # plugin metadata
│   └── icon.png
├── testdata/
│   └── netz_testdaten.gpkg
├── images/
│   └── 01_netz_qa_result.png
├── LICENSE
└── README.md
```

## Tools

QGIS 3.44 · Python · PyQGIS · Qt (PyQt) · GEOS · GeoPackage

## License

MIT License – see [LICENSE](LICENSE)

---
---

# Deutsch

[English](#qgis-netz-qa--quality-checks-for-utility-network-data) | [Deutsch](#deutsch)

**Netz-QA** ist ein QGIS-Plugin (Python / PyQGIS), das Linien- und Punktlayer von Versorgungsnetzen – Wasser- und Gasleitungen, Kabel, Masten – mit einem Klick auf typische Datenfehler prüft. Alle Fehler werden in einer Tabelle aufgelistet, als farbiger Punktlayer in der Karte angezeigt und lassen sich per Doppelklick anzoomen.

![Netz-QA Ergebnis: Fehlerlayer in der Karte und Fehlertabelle](images/01_netz_qa_result.png)

---

## Prüfungen

| Prüfung | Was gefunden wird |
|---|---|
| **Ungültige / leere Geometrien** | Objekte ohne Geometrie oder mit nach GEOS ungültiger Geometrie |
| **Doppelte Geometrien** | Zwei oder mehr Objekte mit exakt gleicher Geometrie (z. B. doppelt digitalisierte Leitung) |
| **Lücken im Netz** (nur Linien) | Leitungsenden, die näher als eine Toleranz (z. B. 1 m) an einer anderen Leitung liegen, sie aber nicht berühren – typische Digitalisierfehler. Echte, weiter entfernte Netzenden werden **nicht** gemeldet. |
| **Leere Pflichtfelder** | Objekte, bei denen ausgewählte Attribute (z. B. Material, Durchmesser) leer sind |

## Testergebnis

Das Repository enthält ein Testnetz (13 Leitungen in Essen, EPSG:25832) mit eingebauten Fehlern. Netz-QA hat genau die **6 erwarteten Fehler** gefunden, ohne Fehlalarme:

| Fehlertyp | Anzahl | Details |
|---|---|---|
| Doppelte Geometrie | 1 | Leitung 10 = Kopie von Leitung 6 |
| Lücke im Netz | 2 | 0,60 m und 0,40 m |
| Leeres Pflichtfeld | 3 | Material und/oder Durchmesser fehlt |

---

## Installation

1. Repository als ZIP herunterladen (**Code → Download ZIP**) und entpacken
2. Nur den Ordner `netz_qa` zippen (die ZIP-Datei muss `netz_qa/…` enthalten)
3. QGIS → **Erweiterungen → Erweiterungen verwalten und installieren → Aus ZIP installieren** → ZIP auswählen
4. In der Werkzeugleiste erscheint ein grünes Netz-QA-Symbol, außerdem unter **Vektor → Netz-QA**

Voraussetzung: QGIS 3.28 oder neuer (vorbereitet für QGIS 4 / Qt6).

## Bedienung

1. Netzlayer laden (oder `testdata/netz_testdaten.gpkg`)
2. Netz-QA öffnen, Layer, Prüfungen, Toleranz für Lücken und Pflichtfelder wählen
3. **Prüfung starten** klicken
4. Doppelklick auf eine Zeile der Tabelle zoomt zum Fehler

---

## Technische Details

- **PyQGIS**: QgsSpatialIndex für schnelle Nachbarsuche, GEOS-basierte Gültigkeits- und Gleichheitsprüfung
- **Lückenerkennung**: Für jedes Leitungsende wird die nächste andere Leitung innerhalb der Toleranz gesucht; wird sie nicht berührt, wird eine Lücke gemeldet (jedes Paar nur einmal)
- **Benutzeroberfläche**: Qt-Dialog in Python (QgsMapLayerComboBox, QgsCheckableComboBox, QTableWidget)
- **Ausgabe**: temporärer Punktlayer mit kategorisierten Symbolen je Fehlertyp
- Kompatibel mit QGIS 3.x und 4.x

## Weiterentwicklung

- Topologieprüfung für Punktlayer (Knoten / Armaturen nicht auf einer Leitung)
- Export der Fehlerliste nach Excel / GeoPackage
- Processing-Algorithmus für Modelle und Stapelverarbeitung
- Veröffentlichung im offiziellen QGIS-Plugin-Repository

---

## Werkzeuge

QGIS 3.44 · Python · PyQGIS · Qt (PyQt) · GEOS · GeoPackage

## Lizenz

MIT-Lizenz – siehe [LICENSE](LICENSE)
