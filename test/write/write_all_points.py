import configparser

from fireapi import FireDb
from adapter import GamaWriter

if __name__ == "__main__":
    db = 'fire:fire@35.158.182.161:1521/xe'
    fireDb = FireDb(db)
    output = open('output/write_all_points.xml','w')
    writer = GamaWriter(fireDb, output)

    writer.take_all_points()
    writer.set_fixed_point_ids(["7CA9F53D-DAE9-59C0-E053-1A041EAC5678"])

    parameters = configparser.ConfigParser()
    parameters.read('fire-gama.ini')
    writer.write(True, False, "test/write_all_points.py", parameters)
    output.close    
