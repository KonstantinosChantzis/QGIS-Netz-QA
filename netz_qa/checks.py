"""Pruefroutinen von Netz-QA. Jede Funktion gibt eine Liste von Fehlern zurueck:
(fehler_typ, feature_id, QgsGeometry fuer die Fehlerstelle, beschreibung)
"""
from qgis.core import (
    QgsFeatureRequest, QgsGeometry, QgsPointXY, QgsSpatialIndex, QgsWkbTypes,
)

# Kompatibel mit QGIS 3.x und 4.x
try:
    from qgis.core import Qgis
    GT_POINT, GT_LINE, GT_POLYGON = (Qgis.GeometryType.Point, Qgis.GeometryType.Line,
                                     Qgis.GeometryType.Polygon)
except AttributeError:
    GT_POINT, GT_LINE, GT_POLYGON = (QgsWkbTypes.PointGeometry, QgsWkbTypes.LineGeometry,
                                     QgsWkbTypes.PolygonGeometry)


def _point_of(geom):
    """Punkt, an dem ein Fehler im Fehlerlayer angezeigt wird."""
    if geom is None or geom.isEmpty():
        return None
    if geom.type() == GT_POINT:
        return QgsGeometry(geom)
    return geom.pointOnSurface() if geom.type() == GT_POLYGON \
        else geom.interpolate(geom.length() / 2.0)


def check_invalid(layer, feedback=None):
    errors = []
    for f in layer.getFeatures():
        g = f.geometry()
        if g is None or g.isEmpty():
            errors.append(("Leere Geometrie", f.id(), None, "Objekt hat keine Geometrie"))
            continue
        if not g.isGeosValid():
            errors.append(("Ungültige Geometrie", f.id(), _point_of(g),
                           "Geometrie ist nach GEOS ungültig"))
    return errors


def check_duplicates(layer, feedback=None):
    errors = []
    index = QgsSpatialIndex(layer.getFeatures())
    geoms = {f.id(): f.geometry() for f in layer.getFeatures()}
    reported = set()
    for fid, g in geoms.items():
        if g is None or g.isEmpty() or fid in reported:
            continue
        for other in index.intersects(g.boundingBox()):
            if other <= fid or other in reported:
                continue
            og = geoms.get(other)
            if og is not None and g.isGeosEqual(og):
                reported.add(other)
                errors.append(("Doppelte Geometrie", other, _point_of(og),
                               f"Gleiche Geometrie wie Objekt {fid}"))
    return errors


def _endpoints(geom):
    pts = []
    if geom.isMultipart():
        parts = geom.asMultiPolyline()
    else:
        parts = [geom.asPolyline()]
    for line in parts:
        if len(line) >= 2:
            pts.append(QgsPointXY(line[0]))
            pts.append(QgsPointXY(line[-1]))
    return pts


def check_gaps(layer, tolerance, feedback=None):
    """Linienenden, die nah an einer anderen Leitung liegen, sie aber nicht beruehren."""
    errors = []
    if layer.geometryType() != GT_LINE:
        return errors
    feats = {f.id(): f.geometry() for f in layer.getFeatures()
             if f.geometry() is not None and not f.geometry().isEmpty()}
    index = QgsSpatialIndex()
    for fid, g in feats.items():
        index.addFeature(fid, g.boundingBox())
    eps = 1e-6
    seen_pairs = set()
    for fid, g in feats.items():
        for p in _endpoints(g):
            pg = QgsGeometry.fromPointXY(p)
            rect = pg.buffer(tolerance, 4).boundingBox()
            touching = False
            nearest = None
            for other in index.intersects(rect):
                if other == fid:
                    continue
                d = feats[other].distance(pg)
                if d <= eps:
                    touching = True
                    break
                if d <= tolerance and (nearest is None or d < nearest[1]):
                    nearest = (other, d)
            if not touching and nearest is not None:
                pair = frozenset((fid, nearest[0]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                errors.append(("Lücke im Netz", fid, pg,
                               f"Ende liegt {nearest[1]:.2f} m neben Objekt {nearest[0]}, "
                               f"ist aber nicht verbunden"))
    return errors


def check_empty_fields(layer, field_names, feedback=None):
    errors = []
    if not field_names:
        return errors
    req = QgsFeatureRequest()
    for f in layer.getFeatures(req):
        empty = []
        for name in field_names:
            v = f[name]
            if v is None or (hasattr(v, "isNull") and v.isNull()) or str(v).strip() in ("", "NULL"):
                empty.append(name)
        if empty:
            errors.append(("Leeres Pflichtfeld", f.id(), _point_of(f.geometry()),
                           "Leer: " + ", ".join(empty)))
    return errors
