import pytest

from fire.api import FireDb
from fire.api.model import (
    Sag,
    Sagsevent,
    SagseventInfo,
    EventType,
    GeometriObjekt,
    Geometry,
    Point,
    Bbox,
    geometry,
)

WKT_POINT = "POINT (10.20000000 56.10000000)"
DICT_POINT = {
    "coordinates": [10.2, 56.1],
    "type": "Point",
}

WKT_POLYGON = (
    "POLYGON ((10.00000000 55.00000000,"
    "12.00000000 55.00000000,"
    "12.00000000 56.00000000,"
    "10.00000000 56.00000000,"
    "10.00000000 55.00000000))"
)

DICT_POLYGON = {
    "coordinates": [
        [[10.0, 55.0], [12.0, 55.0], [12.0, 56.0], [10.0, 56.0], [10.0, 55.0]]
    ],
    "type": "Polygon",
}


def test_geometry():
    g_wkt = Geometry(WKT_POINT)

    assert g_wkt.wkt == WKT_POINT
    assert str(g_wkt) == WKT_POINT
    assert g_wkt.__geo_interface__ == DICT_POINT

    g_dict = Geometry(DICT_POINT)

    assert g_dict.wkt == WKT_POINT
    assert str(g_dict) == WKT_POINT
    assert g_dict.__geo_interface__ == DICT_POINT

    with pytest.raises(TypeError):
        Geometry([])


def test_point():
    p_wkt = Point(WKT_POINT)
    assert p_wkt.__geo_interface__ == DICT_POINT
    assert p_wkt.wkt == WKT_POINT

    p_dict = Point(DICT_POINT)
    assert p_dict.__geo_interface__ == DICT_POINT
    assert p_dict.wkt == WKT_POINT

    p_list = Point([10.2, 56.1])
    assert p_list.wkt == WKT_POINT
    assert p_list.__geo_interface__ == DICT_POINT

    with pytest.raises(TypeError):
        Point(55.5)


def test_bbox():
    bbox = Bbox((10.0, 55.0, 12.0, 56.0))
    assert bbox.wkt == WKT_POLYGON
    assert bbox.__geo_interface__ == DICT_POLYGON


def test_geometry_factory():
    from_wkt_point = geometry.geometry_factory(WKT_POINT)
    assert from_wkt_point.__geo_interface__ == DICT_POINT

    from_wkt_polygon = geometry.geometry_factory(WKT_POLYGON)
    assert from_wkt_polygon.__geo_interface__ == DICT_POLYGON

    from_dict_point = geometry.geometry_factory(DICT_POINT)
    assert from_dict_point.wkt == WKT_POINT

    from_dict_polygon = geometry.geometry_factory(DICT_POLYGON)
    assert from_dict_polygon.wkt == WKT_POLYGON

    with pytest.raises(TypeError):
        geometry.geometry_factory(55)


def test_from_wkt():
    """
    Testes ikke fyldestgørende, da store dele af funktionen ikke er benyttet i
    FIRE på nuværende tidspunkt. De primære områder er dækket af ovenstående
    tests.
    """
    with pytest.raises(Exception):
        geometry.from_wkt("PUNKT (10.0 55.5)")


def test_to_wkt():
    """
    Tilsvarende test_from_wkt()
    """
    with pytest.raises(Exception):
        geometry.to_wkt({"coordinates": [10.2, 56.1], "type": "Punkt"})


def test_geometriobjekt_afregistrering(firedb: FireDb, sag: Sag):
    """
    Test at forudgående geometrier afregistreres korrekt ved indsættelse af ny.
    """

    p = firedb.hent_punkt("SKEJ")
    n = len(p.geometriobjekter)
    go = GeometriObjekt()
    go.geometri = Point([10.17983, 56.18759])
    go.punkt = p

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            sagseventinfos=[SagseventInfo(beskrivelse="Opdater geometri")],
            eventtype=EventType.PUNKT_OPRETTET,
            geometriobjekter=[go],
        )
    )

    geom = p.geometriobjekter
    assert n + 1 == len(p.geometriobjekter)
    assert geom[-2].registreringtil == geom[-1].registreringfra
    assert geom[-2].sagseventtilid == geom[-1].sagseventfraid


def test_to_wkt_precision():
    """Test at der medtages 8 koordinatdecimaler ved oprettelse af WKT-strenge"""
    x = 0.9876543210
    y = 1.9876543210
    wkt = geometry.to_wkt({"coordinates": [x, y], "type": "Point"})
    print(wkt)

    assert wkt == f"POINT (0.98765432 1.98765432)"
