from fireapi import FireDb
from adapter import GamaWriter

if __name__ == "__main__":
    db = 'fire:fire@35.158.182.161:1521/xe'
    fireDb = FireDb(db)
    output = open('write_all_points.xml','w')
    writer = GamaWriter(fireDb, output)
    writer.take_all_points()
    writer.write(True, False, "test/write_all_points.py", None)
    output.close    
