from fireapi import FireDb
from firegama.adapter import GamaReader
import os


if __name__ == "__main__":
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    input_stream = open('input/all_points.xml','r')
    reader = GamaReader(fireDb, input_stream)
    
    sags_id = "3639726e-4dbd-44b5-9928-8ff1e8c970c2"
    reader.read(sags_id)
