from pathlib import Path

from fire.api import FireDb
from fire.api.model import Sag
from fire.api.gama import GamaReader


def test_read(firedb: FireDb, sag: Sag):
    input_stream = open(Path(__file__).resolve().parent / "input/all_points.xml", "r")
    reader = GamaReader(firedb, input_stream)

    reader.read(sag.id)
