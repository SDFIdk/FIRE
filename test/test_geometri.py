import pytest

from fire.api.model import Geometry, Point, Bbox, geometry

WKT_POINT = "POINT (10.200000 56.100000)"
DICT_POINT = {
    "coordinates": [10.2, 56.1],
    "type": "Point",
}

WKT_POLYGON = (
    "POLYGON ((10.000000 55.000000,"
    "12.000000 55.000000,"
    "12.000000 56.000000,"
    "10.000000 56.000000,"
    "10.000000 55.000000))"
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
