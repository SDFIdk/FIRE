# from_wkt and to_wkt are taken from geoalchemy
# Otherwise based on
# https://github.com/zzzeek/sqlalchemy/blob/master/examples/postgis/postgis.py
import re
from typing import (
    Tuple,
)

from sqlalchemy.sql import expression
from pyproj import Proj
import pandas as pd

from fire.api.model import columntypes

__all__ = ["Geometry", "Point", "Bbox"]


class Geometry(expression.Function):
    """Repræsenterer en geometri værdi."""

    inherit_cache = True

    def __init__(self, geometry, srid=4326):
        if isinstance(geometry, str):
            self._geom = from_wkt(geometry)
            self._wkt = geometry
        elif isinstance(geometry, dict) and "type" in geometry:
            self._geom = geometry
            self._wkt = None
        else:
            raise TypeError(
                "Skal være enten en koordinat, en WKT streng eller en GeoJSON-agtig dictionary"
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
        """Geometri repræsenteret som en dictionary."""
        return self._geom


class Point(Geometry):

    inherit_cache = True

    def __init__(self, p, srid=4326):
        if isinstance(p, (list, tuple)):
            geom = dict(type="Point", coordinates=[p[0], p[1]])
        elif isinstance(p, (str, dict)):
            geom = p
        else:
            raise TypeError(
                "Skal være enten en koordinat, en WKT streng eller en GeoJSON-agtig dictionary"
            )
        super(Point, self).__init__(geom, srid)


class Bbox(Geometry):
    def __init__(self, bounds, srid=4326):
        """
        Bounding box polygon.

        Parameters
        ----------
        bounds:
            List/tuple of corner coordinates (west, south, east, north)
        srid:
            Number part of a CRS EPSG-code, e.g. the 4326 in EPSG:4326
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
    raise TypeError(f"Ukendt geometri format: {geom}")


def from_wkt(geom):
    """Konverter fra WKT streng til GeoJSON-agtig geometry."""
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
        raise Exception("Usupporteret geometritype %s" % geomtype)

    return {"type": geomtype, "coordinates": coords}


def to_wkt(geom):
    """Konverter en GeoJSON-agtig geometri til WKT."""

    def coords_to_wkt(coords):
        format_str = " ".join(("%.8f",) * len(coords[0]))
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
                f"Kan ikke lave WKT fra geometritypen {geom['type']} ({geom}). "
                "Kun Point, Line og Polygon er understøttet."
            )
        )


utm32 = None
"Globalt transformationsobjekt til normaliser_lokationskoordinat"


def normaliser_lokationskoordinat(
    λ: float, φ: float, region: str = "DK", invers: bool = False
) -> Tuple[float, float]:
    """Check op på lokationskoordinaterne.
    En normaliseret lokationskoordinat er en koordinat der egner sig som
    WKT- og/eller geojson-geometriobjekt. Dvs. en koordinat anført i en
    afart af WGS84 og med akseorden længde, bredde (λ, φ).

    Hvis det ser ud som om akseordenen er gal, så bytter vi om på dem.

    Hvis input ligner UTM, så regner vi om til geografiske koordinater.
    NaN og 0 flyttes ud i Kattegat, så man kan få øje på dem.

    Disse korrektioner udføres med brug af bredt gyldige heuristikker,
    der dog er nødt til at gøre antagelser om hvor i verden vi befinder os.
    Dette kan eksplicit anføres med argumentet `region`, der som standard
    sættes til `"DK"`.

    Den omvendte vej (`invers==True`, input: geografiske koordinater,
    output: UTM-koordinater i traditionel lokationskoordinatorden)
    er indtil videre kun understøttet for `region=="DK"`.

    Parameters
    ----------
        λ
            Antaget længdegrad (Easting)
        φ
            Antaget breddegrad (Northing)
        region
            Region. Hvis ikke denne er kendt af programmet, returneres koordinaterne uændret.
        invers
            Koordinaterne i omvendt rækkefølge. Se docstring for mere.

    """
    # Gem kopi af oprindeligt input til brug i fejlmelding
    x, y = λ, φ

    global utm32
    if utm32 is None:
        utm32 = Proj("proj=utm zone=32 ellps=GRS80", preserve_units=False)
        assert utm32 is not None, "Kan ikke initialisere projektionselelement utm32"

    # Begrænset understøttelse af FO, GL, hvor UTM32 er meningsløst.
    # Der er gjort plads til indførelse af UTM24 og UTM29 hvis der skulle
    # vise sig behov, men det kræver en væsentlig algoritmeudvidelse.
    if region not in ("DK", ""):
        return (λ, φ)

    # Geometri-til-lokationskoordinat
    if invers:
        return utm32(λ, φ, inverse=False)

    if pd.isna(λ) or pd.isna(φ) or 0 == λ or 0 == φ:
        return (11.0, 56.0)

    # Heuristik til at skelne mellem UTM og geografiske koordinater.
    # Heuristikken fejler kun for UTM-koordinater fra et lille
    # område på 6 hektar ca. 500 km syd for Ghanas hovedstad, Accra.
    # Det er langt ude i Atlanterhavet, så det lever vi med.
    if abs(λ) > 181 and abs(φ) > 91:
        λ, φ = utm32(λ, φ, inverse=True)

    if region == "DK":
        if λ < 3.0 or λ > 15.5 or φ < 54.5 or φ > 58.0:
            raise ValueError(f"Koordinat ({x}, {y}) uden for dansk territorie.")

    return (λ, φ)
