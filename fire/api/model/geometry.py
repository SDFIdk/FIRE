# from_wkt and to_wkt are taken from geoalchemy
# Otherwise based on
# https://github.com/zzzeek/sqlalchemy/blob/master/examples/postgis/postgis.py
import re

from sqlalchemy.sql import expression
from fire.api.model import columntypes

__all__ = ["Geometry", "Point", "Bbox"]


class Geometry(expression.Function):
    """Represents a geometry value."""

    def __init__(self, geometry, srid=4326):
        if isinstance(geometry, str):
            self._geom = from_wkt(geometry)
            self._wkt = geometry
        elif isinstance(geometry, dict) and "type" in geometry:
            self._geom = geometry
            self._wkt = None
        else:
            raise TypeError(
                "must be either a coordinate, a WKT string or a geojson like dictionary"
            )

        self.srid = srid
        expression.Function.__init__(
            self, "SDO_GEOMETRY", self.wkt, srid, type_=columntypes.Geometry
        )

    def __str__(self):
        return self.wkt

    def __repr__(self):
        return "<%s at 0x%x; %r>" % (self.__class__.__name__, id(self), self.wkt)

    @property
    def wkt(self):
        if self._wkt:
            return self._wkt
        return to_wkt(self._geom)

    @property
    def __geo_interface__(self):
        """Dictionary representation of the geometry"""
        return self._geom


class Point(Geometry):
    def __init__(self, p, srid=4326):
        if isinstance(p, (list, tuple)):
            geom = dict(type="Point", coordinates=[p[0], p[1]])
        elif isinstance(p, (str, dict)):
            geom = p
        else:
            raise TypeError(
                "must be either a coordinate, a WKT string or a geojson like dictionary"
            )
        super(Point, self).__init__(geom, srid)


class Bbox(Geometry):
    def __init__(self, bounds, srid=4326):
        """
        Create a bounding box polygon.

        Input:

            bounds: list/tuple of corner coordinates (west, south, east, north)
            srid:   number part of a CRS EPSG-code, e.g. the 4326 in EPSG:4326
        """
        geom = dict(
            type="Polygon",
            coordinates=[
                [
                    [bounds[0], bounds[1]],
                    [bounds[2], bounds[1]],
                    [bounds[2], bounds[3]],
                    [bounds[0], bounds[3]],
                    [bounds[0], bounds[1]],
                ]
            ],
        )
        super(Bbox, self).__init__(geom, srid)


def geometry_factory(geom, srid=4326):
    if isinstance(geom, str):
        if geom.startswith("POINT"):
            return Point(geom, srid)
        else:
            return Geometry(geom, srid)
    if isinstance(geom, dict) and "type" in geom:
        if geom["type"] == "Point":
            return Point(geom, srid)
        else:
            return Geometry(geom, srid)
    raise TypeError(f"Unknown geometry format: {geom}")


def from_wkt(geom):
    """wkt helper: converts from WKT to a GeoJSON-like geometry."""
    wkt_linestring_match = re.compile(r"\(([^()]+)\)")
    re_space = re.compile(r"\s+")

    coords = []
    for line in wkt_linestring_match.findall(geom):
        rings = [[]]
        for pair in line.split(","):

            if not pair.strip():
                rings.append([])
                continue
            rings[-1].append(list(map(float, re.split(re_space, pair.strip()))))

        coords.append(rings[0])

    if geom.startswith("MULTIPOINT"):
        geomtype = "MultiPoint"
        coords = coords[0]
    elif geom.startswith("POINT"):
        geomtype = "Point"
        coords = coords[0][0]

    elif geom.startswith("MULTILINESTRING"):
        geomtype = "MultiLineString"
    elif geom.startswith("LINESTRING"):
        geomtype = "LineString"
        coords = coords[0]

    elif geom.startswith("MULTIPOLYGON"):
        geomtype = "MultiPolygon"
    elif geom.startswith("POLYGON"):
        geomtype = "Polygon"
    else:
        geomtype = geom[: geom.index("(")]
        raise Exception("Unsupported geometry type %s" % geomtype)

    return {"type": geomtype, "coordinates": coords}


def to_wkt(geom):
    """Converts a GeoJSON-like geometry to WKT."""

    def coords_to_wkt(coords):
        format_str = " ".join(("%f",) * len(coords[0]))
        return ",".join([format_str % tuple(c) for c in coords])

    coords = geom["coordinates"]
    if geom["type"] == "Point":
        return "POINT (%s)" % coords_to_wkt((coords,))
    elif geom["type"] == "LineString":
        return "LINESTRING (%s)" % coords_to_wkt(coords)
    elif geom["type"] == "Polygon":
        rings = ["(" + coords_to_wkt(ring) + ")" for ring in coords]
        rings = ",".join(rings)
        return "POLYGON (%s)" % rings

    elif geom["type"] == "MultiPoint":
        pts = ",".join(coords_to_wkt((ring,)) for ring in coords)
        return "MULTIPOINT (%s)" % str(pts)

    elif geom["type"] == "MultiLineString":
        pts = ",".join("(" + coords_to_wkt(ring) + ")" for ring in coords)
        return "MultiLineString (%s)" % str(pts)

    elif geom["type"] == "MultiPolygon":
        poly_str = []
        for coord_list in coords:
            poly_str.append(
                "((" + ",".join(coords_to_wkt((ring,)) for ring in coord_list) + "))"
            )
        return "MultiPolygon (%s)" % ", ".join(poly_str)

    else:
        raise Exception(
            (
                f"Couldn't create WKT from geometry of type {geom['type']} ({geom}). "
                "Only Point, Line, Polygon are supported."
            )
        )
