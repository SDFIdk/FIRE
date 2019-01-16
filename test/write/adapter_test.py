import configparser
import datetime

import os

from fireapi import FireDb
from fireapi.model import (
    Geometry,
)
from firegama.adapter import GamaWriter

def all_points():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open('output/all_points.xml','w')
    writer = GamaWriter(fireDb, output)

    writer.take_all_points()
    writer.set_fixed_point_ids(["7CA9F53D-DAE9-59C0-E053-1A041EAC5678"])

    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "test/all_points.py", parameters)
    output.close
    
def in_polygon():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open('output/in_polygon.xml','w')
    writer = GamaWriter(fireDb, output)

    geometry = Geometry(
        "POLYGON ((10.4811749340072 56.3061226484564, 10.5811749340072 56.3061226484564, 10.5811749340072 56.4061226484564, 10.4811749340072 56.4061226484564, 10.4811749340072 56.3061226484564))"
    )
    observations = fireDb.hent_observationer_naer_geometri(geometry, 0)
    writer.take_observations(observations)

    writer.set_fixed_point_ids(["7CA9F53D-DAE9-59C0-E053-1A041EAC5678"])
    
    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "test/in_polygon.py", parameters)
    output.close    

def naer_geometry_time_interval():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open('output/near_geometry_time_interval.xml','w')
    writer = GamaWriter(fireDb, output)

    g = Geometry("POINT (10.4811749340072 56.3061226484564)")
    observations = fireDb.hent_observationer_naer_geometri(g, 10000, datetime.datetime(2015, 10, 8), datetime.datetime(2015, 10, 9))
    writer.take_observations(observations)

    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "test/near_geometry_time_interval.py", parameters)
    output.close    
    
def naer_geometry():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    output = open('output/near_geometry.xml','w')
    writer = GamaWriter(fireDb, output)

    g = Geometry("POINT (10.4811749340072 56.3061226484564)")
    observations = fireDb.hent_observationer_naer_geometri(g, 10000)
    
    writer.take_observations(observations)

    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "test/near_geometry.py", parameters)
    output.close    
    
if __name__ == "__main__":
    all_points()
    in_polygon()
    naer_geometry_time_interval()
    naer_geometry()
