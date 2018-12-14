from fireapi import FireDb
from adapter import GamaWriter

if __name__ == "__main__":
    db = 'fire:fire@35.158.182.161:1521/xe'
    fireDb = FireDb(db)
    output = open('output.xml','w')
    writer = GamaWriter(fireDb, output)
    writer.take_all_points()
    writer.write(True, False, "test_writer.py", None)
    output.close    
