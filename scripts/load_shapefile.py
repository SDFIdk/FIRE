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

firedb = FireDb(db="ci")

with fiona.open(Path(__file__).parent / "../data/herredsogn.shp") as herredsogn:
    for feature in herredsogn:
        g = Geometry(feature["geometry"])
        kode = feature["properties"]["kode"]

        # Fjollet hack for at omgå begrænsninger i Oracle.
        # Tilsyneladende må strenge ikke være længere end 4000 tegn, så her omgår vi begrænsningen
        # ved at splitte wkt-strengen i flere dele og sammensætte den med ||-operatoren i SQL udtrykket.
        # Idioti, men det virker.
        n = len(g.wkt) // 3
        wkt1, wkt2, wkt3 = g.wkt[:n], g.wkt[n: 2 * n + 1], g.wkt[2 * n + 1:]

        try:
            sql = f"""INSERT INTO herredsogn (kode, geometri)
                      VALUES ('{kode}', SDO_GEOMETRY(TO_CLOB('{wkt1}') || TO_CLOB('{wkt2}') || TO_CLOB('{wkt3}'), 4326)
            )"""
            statement = text(sql)
            firedb.session.execute(statement)
        except:
            # debug
            print(g.wkt)
            print(f"{wkt1}{wkt2}{wkt3}")
            print(sql)
            raise SystemExit

firedb.session.commit()

print("Herred- og sognegrænser tilføjet databasen")
