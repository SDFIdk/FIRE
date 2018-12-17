import datetime
from fireapi import FireDb
from adapter import GamaWriter

if __name__ == "__main__":
    db = 'fire:fire@35.158.182.161:1521/xe'
    fireDb = FireDb(db)
    output = open('write_near_geometry.xml','w')
    writer = GamaWriter(fireDb, output)

    go = fireDb.hent_geometri_objekt("7CA9F53D-DE26-59C0-E053-1A041EAC5678")
    os = fireDb.hent_observationer_naer_geometri(go.geometri, 10000)
    writer.take_observations(os)

    writer.write(True, False, "test/write_near_geometry.py", None)
    output.close    
