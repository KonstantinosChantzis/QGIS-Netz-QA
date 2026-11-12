"""Einfache Übersetzung von Netz-QA (Deutsch / Englisch).

Die Texte im Code sind deutsch. Ist QGIS nicht auf Deutsch eingestellt,
wird die englische Übersetzung aus EN verwendet.
"""
from qgis.core import QgsSettings

EN = {
    # Dialog
    "Netz-QA – Qualitätsprüfung für Netzdaten": "Netz-QA – Quality checks for network data",
    "Layer:": "Layer:",
    "Ungültige / leere Geometrien": "Invalid / empty geometries",
    "Doppelte Geometrien": "Duplicate geometries",
    "Lücken zwischen Leitungen (nur Linien)": "Gaps between pipes (lines only)",
    "Leere Pflichtfelder": "Empty required fields",
    "Armaturen auf Leitung (nur Punkte)": "Valves on pipe (points only)",
    "Toleranz für Lücken:": "Gap tolerance:",
    "Leitungslayer:": "Pipe layer:",
    "Toleranz für Armaturen:": "Valve tolerance:",
    "Pflichtfelder:": "Required fields:",
    "Prüfung starten": "Start check",
    "Fehlerliste exportieren…": "Export error list…",
    "Schließen": "Close",
    "Fehlertyp": "Error type",
    "Objekt-ID": "Feature ID",
    "Beschreibung": "Description",
    "Doppelklick auf eine Zeile zoomt zum Fehler.": "Double-click a row to zoom to the error.",
    # Meldungen
    "Bitte zuerst einen Layer auswählen.": "Please select a layer first.",
    "Bitte einen Leitungslayer auswählen.": "Please select a pipe layer.",
    "{n} Fehler in {total} Objekten – {parts}": "{n} errors in {total} features – {parts}",
    "Keine Fehler gefunden ({total} Objekte geprüft).": "No errors found ({total} features checked).",
    "Netz-QA Fehler – {name}": "Netz-QA errors – {name}",
    "Keine Fehler zum Exportieren.": "No errors to export.",
    "Fehlerliste exportieren": "Export error list",
    "{n} Fehler exportiert: {path}": "{n} errors exported: {path}",
    "Export fehlgeschlagen: {msg}": "Export failed: {msg}",
    # Fehlertypen und Beschreibungen
    "Leere Geometrie": "Empty geometry",
    "Ungültige Geometrie": "Invalid geometry",
    "Doppelte Geometrie": "Duplicate geometry",
    "Lücke im Netz": "Gap in network",
    "Leeres Pflichtfeld": "Empty required field",
    "Armatur nicht auf Leitung": "Valve not on pipe",
    "Objekt hat keine Geometrie": "Feature has no geometry",
    "Geometrie ist nach GEOS ungültig": "Geometry is invalid according to GEOS",
    "Gleiche Geometrie wie Objekt {fid}": "Same geometry as feature {fid}",
    "Ende liegt {d:.2f} m neben Objekt {other}, ist aber nicht verbunden":
        "End lies {d:.2f} m from feature {other} but is not connected",
    "Leer: {names}": "Empty: {names}",
    "Armatur liegt {d:.2f} m neben Leitung {line}": "Valve lies {d:.2f} m from pipe {line}",
    # Processing
    "Netzdaten prüfen": "Check network data",
    "Eingabelayer (Linien oder Punkte)": "Input layer (lines or points)",
    "Ungültige / leere Geometrien prüfen": "Check invalid / empty geometries",
    "Doppelte Geometrien prüfen": "Check duplicate geometries",
    "Lücken zwischen Leitungen prüfen (nur Linien)": "Check gaps between pipes (lines only)",
    "Toleranz für Lücken (m)": "Gap tolerance (m)",
    "Leere Pflichtfelder prüfen": "Check empty required fields",
    "Pflichtfelder": "Required fields",
    "Armaturen auf Leitung prüfen (nur Punkte)": "Check valves on pipe (points only)",
    "Leitungslayer (für die Armaturen-Prüfung)": "Pipe layer (for the valve check)",
    "Toleranz für Armaturen (m)": "Valve tolerance (m)",
    "Netz-QA Fehler": "Netz-QA errors",
    "Anzahl Fehler": "Number of errors",
    "Eingabelayer fehlt.": "Input layer is missing.",
    "Prüfe ungültige / leere Geometrien …": "Checking invalid / empty geometries …",
    "Prüfe doppelte Geometrien …": "Checking duplicate geometries …",
    "Prüfe Lücken zwischen Leitungen …": "Checking gaps between pipes …",
    "Lückenprüfung übersprungen (kein Linienlayer).": "Gap check skipped (not a line layer).",
    "Prüfe Pflichtfelder: {names}": "Checking required fields: {names}",
    "keine gewählt": "none selected",
    "Für die Armaturen-Prüfung bitte einen Leitungslayer wählen.":
        "Please select a pipe layer for the valve check.",
    "Prüfe Armaturen auf Leitung …": "Checking valves on pipe …",
    "Armaturen-Prüfung übersprungen (kein Punktlayer).": "Valve check skipped (not a point layer).",
    "Ausgabelayer konnte nicht erstellt werden.": "Output layer could not be created.",
    "{n} Fehler in {total} Objekten gefunden.": "{n} errors found in {total} features.",
    "HELP": ("Checks a line or point layer of a utility network for typical data errors: "
             "invalid/empty and duplicate geometries, gaps between pipes (lines only), "
             "empty required fields and valves that do not lie on a pipe (points only). "
             "The result is a point layer with all errors."),
    "HELP_DE": ("Prüft einen Linien- oder Punktlayer eines Versorgungsnetzes auf typische "
                "Datenfehler: ungültige/leere und doppelte Geometrien, Lücken zwischen Leitungen "
                "(nur Linien), leere Pflichtfelder und Armaturen, die nicht auf einer Leitung "
                "liegen (nur Punkte). Ergebnis ist ein Punktlayer mit allen Fehlern."),
}


def is_german():
    loc = QgsSettings().value("locale/userLocale", "") or ""
    if not loc:
        from qgis.PyQt.QtCore import QLocale
        loc = QLocale.system().name()
    return str(loc).lower().startswith("de")


def tr(text, **kwargs):
    """Text übersetzen und Platzhalter wie {n} ausfüllen."""
    if not is_german():
        text = EN.get(text, text)
    return text.format(**kwargs) if kwargs else text
