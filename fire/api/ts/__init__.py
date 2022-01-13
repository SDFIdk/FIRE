
"""
Modul til tidserie-håndtering.

"""

import datetime as dt
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from fire.api.firedb import FireDb


# --- TEMP

# ENV_DB = 'test'
ENV_DB = 'prod'
DB = None


def ny_df(datacls) -> pd.DataFrame:
    return pd.DataFrame(columns=datacls.__annotations__).astype(datacls.__annotations__)


def dataframe(datacls):
    """
    Class decorator adding classmethod to create a new
    empty Pandas DataFrame based on dataclass annotations.
    
    """
    def method(cls, rows: Iterable = None) -> pd.DataFrame:
        typedict = cls.__annotations__
        if rows is None:
            return pd.DataFrame(columns=typedict).astype(typedict)
        data = (cls(*row) for row in rows)
        return pd.DataFrame(data=data, columns=typedict).astype(typedict)
    datacls.new_df = classmethod(method)
    return datacls


@dataframe
@dataclass
class TidsseriePost:
    punkt_id: str = None
    dato: np.datetime64 = None
    kote: float = None
    jessen_id: str = None
    # er_jessen_punkt: bool = None
    landsnr: str = None


@dataframe
@dataclass
class ObservationsPost:
    registrering_fra: np.datetime64 = None
    opstillingspunkt_id: str = None
    sigtepunkt_id: str = None
    koteforskel: float = None
    observationstype_id: str = None


def get_db():
    global DB
    if DB is None:
        DB = FireDb(db=ENV_DB)
    return DB


def fetchall(sql):
    return get_db().session.execute(sql).all()

# --- / TEMP


def hent_tidsserie(jessen_id: str, *, get_raw_values=False) -> pd.DataFrame:
    """
    Hent tidsserien TS:`jessen_id`.

    Punkterne i tidsserien udgør en punktgruppe.
    Alternativt: En punktgruppe er punkter, der er en del af samme tidsserie.

    Tidsserier indikeres med et SRID med formatet `TS:[JESSEN_ID]`
    (et lokalt kotesystem), hvor `[JESSEN_ID]` er nummeret på
    punktgruppens Jessen-punkt.

    Returns
    -------
        Tabel med følgende kolonner:

        *   punkt-ID
        *   tidspunkt
        *   kote i tidsseriens lokale kotesystem (`TS:[JESSEN_ID]`)
        *   Jessen-ID
        *   True hvis punkt er Jessenpunktet ellers 0
    
    """
    sql = f"""\
WITH jessen_punkter AS (
    SELECT
        p.id AS punkt_id,
        pi.tekst AS jessen_id
    FROM punkt p
    JOIN punktinfo pi ON p.id = pi.punktid
    JOIN punktinfotype pit ON pi.infotypeid = pit.infotypeid
    WHERE
        pit.infotype='IDENT:jessen'
),
landsnumre AS (
    SELECT
        p.id,
        pi.tekst AS landsnr
    FROM punkt p
    JOIN punktinfo pi ON p.id = pi.punktid
    JOIN punktinfotype pit ON pi.infotypeid = pit.infotypeid
    WHERE pit.infotype = 'IDENT:landsnr'
)
SELECT
    p.id AS punkt_id,
    k.t AS dato,
    k.z AS kote,
--    CASE jp.jessen_id WHEN jp.jessen_id THEN 1 ELSE 0 END AS er_jessen_punkt,
    jp.jessen_id,
    l.landsnr

FROM punkt p

JOIN koordinat k ON p.id = k.punktid
JOIN sridtype s ON k.sridid = s.sridid

-- Der kan være punkter med i punktgruppen, som er Jessen-puknt i en anden tidsserie.
-- Med et ekstra krav i denne left join om, at `jessen_id` skal være det samme, som tidsserie-ID'et,
-- gør, at kun tidsseriens Jessen-ID kommer med.
LEFT JOIN jessen_punkter jp ON p.id = jp.punkt_id AND jp.jessen_id = '{jessen_id}'

LEFT JOIN landsnumre l ON p.id = l.id

WHERE
    s.srid = 'TS:{jessen_id}'
ORDER BY
    jp.jessen_id ASC,
    k.t ASC
"""
    if get_raw_values:
        return fetchall(sql)
    return TidsseriePost.new_df(fetchall(sql))
    # data = [TidsseriePost(*row) for row in fetchall(sql)]
    # return ny_df(TidsseriePost).append(data) # .astype(TidsseriePost)


def hent_observationer_af_punktgruppe(punktgruppe: Iterable[str], dato_fra: dt.datetime = None, dato_til: dt.datetime = None, full_print: bool = False) -> pd.DataFrame:
    """
    Antagelser
    ----------
    *   Punkgruppen er større end to punkter, da nedenstående forespørgsel ikke dur uden mindst to punkter, der er observeret mellem i løbet af det angivne tidsrum.    
    """
    # Start et halvt år tilbage, hvis én eller begge datoer i tidsrummet mangler.
    # TODO: Genbesøg detaljer, når resten er klar.
    if dato_fra is None or dato_til is None:
        til = dt.date.today()
        fra = dt.date(til.year, til.month, 1) - dt.timedelta(weeks=26)
        dato_fra = fra.isoformat()
        dato_til = til.isoformat()

    comma_separated = '\', \''.join(punktgruppe)
    sql_tuple = f'(\n\'{comma_separated}\'\n)'
    sql = f"""\
SELECT DISTINCT
    o.registreringfra,
    o.opstillingspunktid,
    o.sigtepunktid,
    o.value1 AS koteforskel,
    o.observationstypeid
FROM punkt p
JOIN observation o ON p.id = o.opstillingspunktid OR p.id = o.sigtepunktid
WHERE
    o.observationstypeid IN (1, 2)
  AND
    o.registreringfra BETWEEN DATE '{dato_fra}' AND DATE '{dato_til}'
  AND
    o.opstillingspunktid IN {sql_tuple}
  AND
    o.sigtepunktid IN {sql_tuple}
ORDER BY
    o.registreringfra ASC,
    o.opstillingspunktid ASC,
    o.sigtepunktid ASC
"""
    if full_print:
        print(sql)
    else:
        print(sql.replace(sql_tuple, '(...)'))
    return ObservationsPost.new_df(fetchall(sql))


def hent_observationer_for_tidsserie(jessen_id: str, dato_fra: dt.datetime = None, dato_til: dt.datetime = None) -> pd.DataFrame:
    """

    """
    # Start et halvt år tilbage, hvis én eller begge datoer i tidsrummet mangler.
    # TODO: Genbesøg detaljer, når resten er klar.
    if dato_fra is None or dato_til is None:
        til = dt.date.today()
        fra = dt.date(til.year, til.month, 1) - dt.timedelta(weeks=26)
        dato_fra = fra.isoformat()
        dato_til = til.isoformat()

    sql = f"""\
WITH tidsserie_punkter AS (
    SELECT DISTINCT p.id
    FROM punkt p
    JOIN koordinat k ON p.id = k.punktid
    JOIN sridtype s ON k.sridid = s.sridid
    WHERE s.srid = 'TS:{jessen_id}'
)
SELECT DISTINCT
    o.registreringfra,
    o.opstillingspunktid,
    o.sigtepunktid,
    o.value1 AS koteforskel,
    o.observationstypeid
FROM tidsserie_punkter tp
JOIN observation o ON tp.id = o.opstillingspunktid OR tp.id = o.sigtepunktid
WHERE
    o.observationstypeid IN (1, 2)
  AND
    o.registreringfra BETWEEN DATE '{dato_fra}' AND DATE '{dato_til}'
  AND
    o.opstillingspunktid IN (SELECT tp.id FROM tidsserie_punkter tp)
  AND
    o.sigtepunktid IN (SELECT tp.id FROM tidsserie_punkter tp)
ORDER BY
    o.registreringfra ASC,
    o.opstillingspunktid ASC,
    o.sigtepunktid ASC
"""
    print(sql)
    return ObservationsPost.new_df(fetchall(sql))


def hent_tidsserie_for_punkt(jessen_id: str, punkt_id: str) -> pd.DataFrame:
    sql = f"""\
SELECT
  k.t,
  k.z
FROM koordinat k
WHERE
  k.punktid='{punkt_id}'
AND
  k.sridid=(
	SELECT sridid
	FROM sridtype
	WHERE srid='TS:{jessen_id}'
  )
ORDER BY
  k.t ASC
"""
    return fetchall(sql)


# SQL-eksempler fra KE

def hent_mulige_tidsserier(punktid: str) -> list:
    sql = f"""\
SELECT
  s.srid,
  count(s.sridid)
FROM koordinat k
JOIN sridtype s ON s.sridid=k.sridid
WHERE
  k.punktid = '{punktid}'
GROUP BY
  s.srid
ORDER BY
  count(s.sridid) DESC
"""
    return fetchall(sql)


# --- Under opbygning

def hent_punkt_geometri(punkt_id: str) -> object:
    sql = f"""\
SELECT
    g.geometri,
    p.id
FROM punkt p
JOIN geometriobjekt g ON p.id = g.punktid
WHERE
    p.id = '{punkt_id}'
"""
    print(sql)
    return fetchall(sql)