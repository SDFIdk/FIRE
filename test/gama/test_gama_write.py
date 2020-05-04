import configparser
import datetime
import os

import pytest

from fire.api import FireDb
from fire.api.model import Geometry
from fire.api.gama import GamaWriter


@pytest.mark.skip("Undlades indtil et bedre test datasæt er indlæst i databasen")
def test_all_points():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open("output/all_points.xml", "w")
    writer = GamaWriter(fireDb, output)

    writer.take_all_points()
    writer.set_fixed_point_ids(["7CA9F53D-DAE9-59C0-E053-1A041EAC5678"])

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test/all_points.py", parameters)
    output.close


@pytest.mark.skip("Undlades indtil et bedre test datasæt er indlæst i databasen")
def test_in_polygon():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open("output/in_polygon.xml", "w")
    writer = GamaWriter(fireDb, output)

    geometry = Geometry(
        "POLYGON ((10.4811749340072 56.3061226484564, 10.5811749340072 56.3061226484564, 10.5811749340072 56.4061226484564, 10.4811749340072 56.4061226484564, 10.4811749340072 56.3061226484564))"
    )
    observations = fireDb.hent_observationer_naer_geometri(geometry, 0)
    writer.take_observations(observations)

    writer.set_fixed_point_ids(["7CA9F53D-DAE9-59C0-E053-1A041EAC5678"])

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test/in_polygon.py", parameters)
    output.close


@pytest.mark.skip("Undlades indtil et bedre test datasæt er indlæst i databasen")
def test_naer_geometry_time_interval():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open("output/near_geometry_time_interval.xml", "w")
    writer = GamaWriter(fireDb, output)

    g = Geometry("POINT (12.5983815323665 55.7039994123763)")
    observations = fireDb.hent_observationer_naer_geometri(
        g, 10000, datetime.datetime(2015, 10, 8), datetime.datetime(2018, 10, 9)
    )

    # p = fireDb.hent_punkt("814E9044-1AAB-5A4E-E053-1A041EACF9E4")
    # observations = fireDb.hent_observationer_naer_opstillingspunkt(p, 10000)
    # observations = fireDb.hent_observationer_naer_opstillingspunkt(p, 10000, datetime.datetime(2015, 10, 8), datetime.datetime(2018, 10, 9))

    writer.take_observations(observations)

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test/near_geometry_time_interval.py", parameters)
    output.close


@pytest.mark.skip("Undlades indtil et bedre test datasæt er indlæst i databasen")
def test_naer_geometry():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open("output/near_geometry.xml", "w")
    writer = GamaWriter(fireDb, output)

    g = Geometry("POINT (10.4811749340072 56.3061226484564)")
    observations = fireDb.hent_observationer_naer_geometri(g, 10000)

    writer.take_observations(observations)

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test/near_geometry.py", parameters)
    output.close
