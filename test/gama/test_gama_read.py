import os

import pytest

from fire.api import FireDb
from fire.api.gama import GamaReader


@pytest.mark.skip("Undlades indtil et bedre test datasæt er indlæst i databasen")
def test_read():
    db = os.environ.get("fire-db")
    fireDb = FireDb(db)
    input_stream = open("input/all_points.xml", "r")
    reader = GamaReader(fireDb, input_stream)

    sags_id = "3639726e-4dbd-44b5-9928-8ff1e8c970c2"
    reader.read(sags_id)
