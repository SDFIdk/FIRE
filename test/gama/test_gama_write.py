import configparser
import datetime
import os
from pathlib import Path

from fire.api import FireDb
from fire.api.model import Geometry
from fire.api.gama import GamaWriter


def test_all_points(firedb: FireDb, tmp_path: Path):
    outfile = tmp_path / "all_points.xml"
    output = open(outfile, "w")
    writer = GamaWriter(firedb, output)

    writer.take_all_points()
    writer.set_fixed_point_ids(["67e3987a-dc6b-49ee-8857-417ef35777af"])

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test_all_points", parameters)
    output.close


def test_in_polygon(firedb: FireDb, tmp_path: Path):
    outfile = tmp_path / "in_polygon.xml"
    output = open(outfile, "w")
    writer = GamaWriter(firedb, output)

    geometry = Geometry(
        (
            "POLYGON ((10.209 56.155, "
            "10.209 56.158, "
            "10.215 56.158, "
            "10.215 56.155, "
            "10.209 56.155))"
        )
    )
    observations = firedb.hent_observationer_naer_geometri(geometry, 5000)
    writer.take_observations(observations)

    writer.set_fixed_point_ids(["67e3987a-dc6b-49ee-8857-417ef35777af"])

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test_in_polygon", parameters)
    output.close
    os.remove(outfile)


def test_naer_geometry_time_interval(firedb: FireDb, tmp_path: Path):
    outfile = tmp_path / "near_geometry_time_interval.xml"
    output = open(outfile, "w")
    writer = GamaWriter(firedb, output)

    g = Geometry("POINT (10.200000 56.100000)")
    observations = firedb.hent_observationer_naer_geometri(
        g, 10000, datetime.datetime(2015, 10, 8), datetime.datetime(2018, 10, 9)
    )

    writer.take_observations(observations)

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test_near_geometry_time_interval", parameters)
    output.close
    os.remove(outfile)


def test_naer_geometry(firedb: FireDb, tmp_path: Path):
    outfile = tmp_path / "near_geometry.xml"
    output = open(outfile, "w")
    writer = GamaWriter(firedb, output)

    g = Geometry("POINT (10.200000 56.100000)")
    observations = firedb.hent_observationer_naer_geometri(g, 10000)

    writer.take_observations(observations)

    parameters = configparser.ConfigParser()
    parameters.read("fire-gama.ini")
    writer.write(True, False, "test_near_geometry", parameters)
    output.close
    os.remove(outfile)
