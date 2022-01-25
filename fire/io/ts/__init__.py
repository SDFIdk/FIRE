"""
Modul til tidserie-håndtering.

"""

import datetime as dt
import itertools as it
from typing import (
    Iterator,
    Iterable,
    Union,
    Final,
)

import pandas as pd

from fire.api.firedb import FireDb
from fire.api.model.punkttyper import ObservationstypeID
from fire.api.niv.gama_beregner import GamaBeregner
from fire.io import regneark
from fire.io.ts import query
from fire.io import arkdef
from fire.io.ts.beregning import TidsserieMapper
from fire.io.ts.post import (
    TidsseriePost,
    ObservationsPost,
    MuligTidsserie,
)

# --- TEMP

# ENV_DB = 'test'
ENV_DB: Final = "prod"
DB = None


def ny_df(datacls) -> pd.DataFrame:
    return pd.DataFrame(columns=datacls.__annotations__).astype(datacls.__annotations__)


def get_db():
    global DB
    if DB is None:
        DB = FireDb(db=ENV_DB)
    return DB


def fetchall(sql):
    return get_db().session.execute(sql).all()


# --- / TEMP


def asdate(dato: Union[str, dt.datetime, dt.date]) -> dt.date:
    """
    Konvertér dato til dato.

    """
    if dato is None:
        return None

    if isinstance(dato, str):
        try:
            return dt.datetime.strptime(dato, "%Y-%m-%d").date()
        except:
            raise (f"Forventede ISO-8601-dato, men fik {dato!r}")

    if isinstance(dato, dt.datetime):
        return dato.date()

    assert isinstance(dato, dt.date), f"Forventede Python-dato, men fik {dato!r}"
    return dato


def standard_interval(
    dato_fra: Union[dt.datetime, dt.date],
    dato_til: Union[dt.datetime, dt.date],
):
    """
    Returnér dato-interval i ISO-8601-format.

    Mangler én eller begge datoer, rettes `dato_fra` til
    ca. et halvt år fra dags dato til idag.

    """
    # Start et halvt år tilbage, hvis én eller begge datoer i tidsrummet mangler.
    # TODO: Genbesøg detaljer, når resten er klar.
    if dato_fra is None or dato_til is None:
        til = dt.date.today()
        fra = dt.date(til.year, til.month, 1) - dt.timedelta(weeks=26)
        return fra.isoformat(), til.isoformat()
    return dato_fra.isoformat(), dato_til.isoformat()


def hent_mulige_tidsserier(punkt_id: str) -> list:
    sql = query.hent_mulige_tidsserier.format(punkt_id=punkt_id)
    return MuligTidsserie.map(fetchall(sql))


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
    return TidsseriePost.asdf(fetchall(sql))


def hent_observationer_i_punktgruppe(
    punktgruppe: Iterable[str],
    dato_fra: Union[dt.datetime, dt.date] = None,
    dato_til: Union[dt.datetime, dt.date] = None,
    asdf: bool = False,
) -> Union[Iterator[ObservationsPost], pd.DataFrame]:
    """
    Antagelser
    ----------
    *   Punkgruppen er større end to punkter, da nedenstående forespørgsel ikke dur uden mindst to punkter, der er observeret mellem i løbet af det angivne tidsrum.
    """
    dato_fra, dato_til = standard_interval(asdate(dato_fra), asdate(dato_til))
    kwargs = dict(
        punktgruppe=punktgruppe,
        dato_fra=dato_fra,
        dato_til=dato_til,
    )
    kwargs.update(observationstypeid=ObservationstypeID.geometrisk_koteforskel)
    sql_mgl = query.observationer_i_punktgruppe(**kwargs)
    kwargs.update(observationstypeid=ObservationstypeID.trigonometrisk_koteforskel)
    sql_mtl = query.observationer_i_punktgruppe(**kwargs)
    raw = it.chain(fetchall(sql_mgl), fetchall(sql_mtl))
    if asdf:
        return ObservationsPost.asdf(raw)
    return ObservationsPost.map(raw)


def hent_observationer_for_tidsserie(
    jessen_id: str,
    dato_fra: dt.datetime = None,
    dato_til: dt.datetime = None,
    asdf: bool = False,
) -> Union[Iterator[ObservationsPost], pd.DataFrame]:
    """
    Henter nivellement-observationer (MGL/MTL) for tidsserien med Jessen-punktet `jessen_id`.

    """
    dato_fra, dato_til = standard_interval(asdate(dato_fra), asdate(dato_til))
    kwargs = dict(
        jessen_id=jessen_id,
        dato_fra=dato_fra,
        dato_til=dato_til,
    )
    kwargs.update(observationstypeid=ObservationstypeID.geometrisk_koteforskel)
    sql_mgl = query.observationer_for_tidsserie(**kwargs)
    kwargs.update(observationstypeid=ObservationstypeID.trigonometrisk_koteforskel)
    sql_mtl = query.observationer_for_tidsserie(**kwargs)
    raw = it.chain(fetchall(sql_mgl), fetchall(sql_mtl))
    if asdf:
        return ObservationsPost.asdf(raw)
    return ObservationsPost.map(raw)


def jessen_punkt(tidsserie, jessen_id):
    assert "jessen_id" in tidsserie, f"Mangler kolonnen `jessen_id`."
    bools = tidsserie.jessen_id == jessen_id
    assert sum(bools) == 1, f"Jessen-ID {jessen_id!r} skal være til stede 1 gang."
    return tidsserie[bools].iloc[0]


def fjern_punkter_med_for_få_tidsskridt(tidsserie, N=2):
    s_counts = tidsserie.punkt_id.value_counts()
    remove = s_counts[s_counts < N]
    return tidsserie[~tidsserie.punkt_id.isin(remove.index)].reset_index()


# ---
def beregn_tidsserie_koter(
    jessen_punkt: pd.Series,
    observationer: Iterable[ObservationsPost],
) -> pd.DataFrame:
    """
    Formål
    ------
    Beregn nyt tidsserieskridt for observerede punkter i punktgruppen.

    Antagelser
    ----------

    *   Kvalitetskontrol af observationerne er foretaget af målerne, inden observationerne blev lagt i databasen.
    *   Inddata til kote-beregningen har samme format som de ark, der bruges til blandt andet regnearks-produkter, som bruges af målerne.
    *   Punkterne er en del af punktsamlingen for tidsserien.
    *   Observationerne er foretaget inden for det korrekte tidsrum.
    *   Alle punkter er forbundne.
    *   Alle observationer skal bruges i beregningen.
    *   Jessen-punktet er eneste fastholdte.

    """

    projektnavn = "gama-beregning-endelig"
    data = dict(
        projektnavn=projektnavn,
        observationer=observationer,
        jessen_punkt=jessen_punkt,
    )
    beregner = GamaBeregner(TidsserieMapper())
    beregner.beregn(data)
    return beregner.resultat
