"""
Indlæs herred- og sognegrænser i Oracledatabasen.

Dette kunne være en ogr2ogr one-liner, men da Oracle-driveren ikke
tilbydes som en del af gdal/ogr-pakken i conda-forge populeres databasen
istedet med dette script.
"""
from pathlib import Path

from sqlalchemy.sql import text
import fiona

from fire.api import FireDb
from fire.api.model import Geometry

firedb = FireDb()

with fiona.open(Path(__file__).parent / "../data/herredsogn.shp") as herredsogn:
    for feature in herredsogn:
        g = Geometry(feature["geometry"])
        kode = feature["properties"]["kode"]

        # Fjollet hack for at omgå begrænsninger i Oracle.
        # Tilsyneladende må strenge ikke være længere end 4000 tegn, så her omgår vi begrænsningen
        # ved at splitte wkt-strengen i to dele og sammensætte den med ||-operatoren i SQL udtrykket.
        # Idioti, men det virker.
        wkt1, wkt2 = g.wkt[: len(g.wkt) // 2], g.wkt[len(g.wkt) // 2 :]
        statement = text(
            f"""INSERT INTO herredsogn (kode, geometri)
                VALUES ('{kode}', SDO_GEOMETRY(TO_CLOB('{wkt1}') || TO_CLOB('{wkt2}'), 4326)
            )"""
        )
        firedb.session.execute(statement)

firedb.session.commit()

print("Herred- og sognegrænser tilføjet databasen")
