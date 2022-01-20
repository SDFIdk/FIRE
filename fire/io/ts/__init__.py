"""
Modul til tidserie-håndtering.

"""

import datetime as dt
from dataclasses import (
    dataclass,
    make_dataclass,
    field,
    fields,
)
from typing import Iterable

import numpy as np
import pandas as pd

from fire.api.firedb import FireDb
from fire.io.ts import query
from fire.cli.niv._regn import (
    find_fastholdte,
    gama_beregning,
)
from fire.io import arkdef
from fire.io.regneark import (
    nyt_ark,
    MAPPER,
)


# --- TEMP

# ENV_DB = 'test'
ENV_DB = "prod"
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
    nivlaengde: float = None
    opstillinger: int = None
    spredning_afstand: float = None
    spredning_centrering: float = None
    observationstidspunkt: dt.datetime = None
    observationstype_id: str = None
    id: str = None


def get_db():
    global DB
    if DB is None:
        DB = FireDb(db=ENV_DB)
    return DB


def fetchall(sql):
    return get_db().session.execute(sql).all()


@dataclass(order=True)
class MuligTidsserie:
    skridt: int
    srid: str

    def jessen_id(self):
        return self.srid[self.srid.index(":") + 1 :]


# --- / TEMP


def hent_mulige_tidsserier(punkt_id: str) -> list:
    sql = query.hent_mulige_tidsserier.format(punkt_id=punkt_id)
    # return fetchall(sql)
    return [MuligTidsserie(*row) for row in fetchall(sql)]


def hent_tidsserie(jessen_id: str) -> pd.DataFrame:
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
    sql = query.hent_tidsserie.format(jessen_id=jessen_id)
    return TidsseriePost.new_df(fetchall(sql))


def hent_observationer_i_punktgruppe(
    punktgruppe: Iterable[str],
    dato_fra: dt.datetime = None,
    dato_til: dt.datetime = None,
    full_print: bool = False,
) -> pd.DataFrame:
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

    comma_separated = "', '".join(punktgruppe)
    sql_tuple = f"(\n'{comma_separated}'\n)"
    kwargs = dict(
        sql_tuple=sql_tuple,
        dato_fra=dato_fra,
        dato_til=dato_til,
    )
    sql = query.hent_observationer_i_punktgruppe.format(**kwargs)
    # if full_print:
    #     print(sql)
    # else:
    #     print(sql.replace(sql_tuple, "(...)"))
    return ObservationsPost.new_df(fetchall(sql))


def hent_observationer_for_tidsserie(
    jessen_id: str, dato_fra: dt.datetime = None, dato_til: dt.datetime = None
) -> pd.DataFrame:
    """ """
    # Start et halvt år tilbage, hvis én eller begge datoer i tidsrummet mangler.
    # TODO: Genbesøg detaljer, når resten er klar.
    if dato_fra is None or dato_til is None:
        til = dt.date.today()
        fra = dt.date(til.year, til.month, 1) - dt.timedelta(weeks=26)
        dato_fra = fra.isoformat()
        dato_til = til.isoformat()

    kwargs = dict(
        jessen_id=jessen_id,
        dato_fra=dato_fra,
        dato_til=dato_til,
    )
    sql = query.hent_observationer_for_tidsserie.format(**kwargs)
    # print(sql)
    return ObservationsPost.new_df(fetchall(sql))


def jessen_kote(tidsserie, jessen_id):
    assert "jessen_id" in tidsserie, f"Mangler kolonnen `jessen_id`."
    bools = tidsserie.jessen_id == jessen_id
    assert sum(bools) == 1, f"Jessen-ID {jessen_id!r} skal være til stede 1 gang."
    return tidsserie[bools].kote[0]


def fjern_punkter_med_for_få_tidsskridt(tidsserie, N=2):
    s_counts = tidsserie.punkt_id.value_counts()
    remove = s_counts[s_counts < N]
    return tidsserie[~tidsserie.punkt_id.isin(remove.index)].reset_index()


# O = arkdef.OBSERVATIONER
# d_O = make_dataclass('d_O', list(O.items()))
# d_O.__annotations__
# nyt_ark(d_O.__annotations__)


o_default = {
    "Journal": "",
    "Sluk": "",
    "Kommentar": "",
    "Kilde": "",
    "Type": "",
}


def o_insert(o):
    return {
        "Fra": o.opstillingspunktid,
        "Til": o.sigtepunktid,
        "L": o.nivlaengde,
        "ΔH": o.koteforskel,
        "Opst": o.opstillinger,
        "σ": o.spredning_afstand,
        "δ": o.spredning_centrering,
        "Hvornår": o.observationstidspunkt,
        "Type": MAPPER.get(o.observationstypeid, ""),
        "uuid": o.id,
    }


def til_o(række):
    return {
        **o_default,
        **o_insert,
        **dict(),
    }


def beregn_tidsserie_koter(
    observationer: pd.DataFrame, punktoversigt: pd.DataFrame
) -> pd.DataFrame:
    """
    Formål
    ------
    Beregn nyt tidsserieskridt for observerede punkter i punktgruppen.

    Antagelser
    ----------

    *   Kvalitetskontrol af observationerne er foretaget af målerne, inden observationerne blev lagt i databasen.
    *   Inddata til kote-beregningen har samme format som de ark, der bruges til blandt andet regnearks-produkter, som bruges af målerne.
    *   Punkterne er en del af punktgruppen for tidsserien.
    *   Observationerne er foretaget inden for det korrekte tidsrum.

    Fremgangsmåde
    -------------

    *   Jessen-punktet er fastholdt.

    """

    # API: Find fastholdte
    er_kontrolberegning = False
    fastholdte = find_fastholdte(punktoversigt, er_kontrolberegning)

    # API: GNU GAMA-beregning
    punkter = tuple(sorted(set(observationer.Fra) | set(observationer.Til)))
    estimerede_punkter = estimerede_punkter = tuple(
        sorted(set(punkter) - set(fastholdte))
    )

    rapport_navn = "gama-beregning"
    kwargs = dict(
        projektnavn=rapport_navn,
        observationer=observationer,
        arbejdssæt=punktoversigt,
        estimerede_punkter=estimerede_punkter,
        kontrol=er_kontrolberegning,
    )
    beregning, fname_rapport = gama_beregning(**kwargs)

    # Konvertér beregninging til Tidsseriepost?
    return TidsseriePost.new_df()


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
