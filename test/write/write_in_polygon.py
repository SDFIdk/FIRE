import configparser

from fireapi import FireDb
from fireapi.model import (
    Geometry,
)

from adapter import GamaWriter

if __name__ == "__main__":
    db = 'fire:fire@35.158.182.161:1521/xe'
    fireDb = FireDb(db)
    output = open('output/write_in_polygon.xml','w')
    writer = GamaWriter(fireDb, output)

    geometry = Geometry(
        "POLYGON ((10.4811749340072 56.3061226484564, 10.5811749340072 56.3061226484564, 10.5811749340072 56.4061226484564, 10.4811749340072 56.4061226484564, 10.4811749340072 56.3061226484564))"
    )
    os = fireDb.hent_observationer_naer_geometri(geometry, 0)
    writer.take_observations(os)

    writer.set_fixed_point_ids(["7CA9F53D-DAE9-59C0-E053-1A041EAC5678"])
    
    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "test/write_in_polygon.py", parameters)
    output.close    
