import configparser

import datetime
from fireapi import FireDb
from fireapi.model import (
    Geometry,
)
from adapter import GamaWriter

if __name__ == "__main__":
    db = 'fire:fire@35.158.182.161:1521/xe'
    fireDb = FireDb(db)
    output = open('output/write_near_geometry_time_interval.xml','w')
    writer = GamaWriter(fireDb, output)

    g = Geometry("POINT (10.4811749340072 56.3061226484564)")
    os = fireDb.hent_observationer_naer_geometri(g, 10000, datetime.datetime(2015, 10, 8), datetime.datetime(2015, 10, 9))
    writer.take_observations(os)

    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "test/write_near_geometry_time_interval.py", parameters)
    output.close    
