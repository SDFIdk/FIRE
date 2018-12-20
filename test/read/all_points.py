from fireapi import FireDb
from adapter import GamaReader

if __name__ == "__main__":
    db = 'fire:fire@35.158.182.161:1521/xe'
    fireDb = FireDb(db)
    input_stream = open('input/all_points.xml','r')
    reader = GamaReader(fireDb, input_stream)
    
    sags_id = "3639726e-4dbd-44b5-9928-8ff1e8c970c2"
    reader.read(sags_id)
