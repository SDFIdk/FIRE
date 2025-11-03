"""
I/O-modul til håndtering af regneark

"""

from functools import partial
from typing import (
    Any,
    Optional,
    Union,
    Mapping,
    List,
    Mapping,
    Union,
    Callable,
    BinaryIO,
)

import pandas as pd

from fire.api.model import (
    Koordinat,
    Punkt,
    ObservationstypeID,
    GeometriskKoteforskel,
    TrigonometriskKoteforskel,
)
from fire.api.niv.datatyper import NivMetode
from fire.srid import SRID
from fire.io.regneark import arkdef
import fire.io.dataframe as frame


# Annoteringstyper
RækkeType = Mapping[str, Any]
_basisrækker: Mapping[str, RækkeType] = dict()
"Cache til u-initialiserede rækker for en given arkdefinition."


def _hashable_from_keys(arkdefinition: arkdef.ArkDefinitionType) -> str:
    """Return string of all dict keys as hashable object for caching"""
    return "".join(arkdefinition.keys())


def basisrække(arkdefinition: arkdef.ArkDefinitionType) -> RækkeType:
    """
    Returnerer en dict-instans med arkdefinitionens nøgler
    og `None` som standard-værdi

    """
    # Rationale: en dict er ikke hashable (immutable),
    # så vi skal bruge noget andet unikt som nøgle.
    h = _hashable_from_keys(arkdefinition)
    if h not in _basisrækker:
        _basisrækker[h] = {key: None for key in arkdefinition}
    return _basisrækker[h]


MAPPER = {
    ObservationstypeID.geometrisk_koteforskel: NivMetode.MGL.name,
    ObservationstypeID.trigonometrisk_koteforskel: NivMetode.MTL.name,
}
"Oversætter observationstypeid til det forkortede navn for observationstypen."


OBSERVATIONER_KONSTANTE_FELTER = {
    "Journal": "",
    "Sluk": "",
    "Kommentar": "",
    "T": -999,
    "Sky": -999,
    "Sol": -999,
    "Vind": -990,
    "Sigt": -999,
    "Kilde": "Ingen",
    "Type": "",
}


def observations_data(
    observation: Union[GeometriskKoteforskel, TrigonometriskKoteforskel]
) -> dict:
    return {
        "Fra": observation.opstillingspunkt.ident,
        "Til": observation.sigtepunkt.ident,
        "L": observation.nivlængde,
        "ΔH": observation.koteforskel,
        "Opst": observation.opstillinger,
        "σ": observation.spredning_afstand,
        "δ": observation.spredning_centrering,
        "Hvornår": observation.observationstidspunkt,
        "Type": MAPPER.get(observation.observationstypeid, ""),
        "uuid": observation.id,
    }


def observationsrække(
    observation: Union[GeometriskKoteforskel, TrigonometriskKoteforskel]
) -> dict:
    """
    Oversætter atributter på en observationstype til en post,
    der kan bruges som række i et observationsregneark til
    et nivellement-projekt.

    """
    return {
        **basisrække(arkdef.OBSERVATIONER),
        **OBSERVATIONER_KONSTANTE_FELTER,
        **observations_data(observation),
    }


PUNKTOVERSIGT_KONSTANTE_FELTER = {
    "Fasthold": "",
    "System": "DVR90",
    "Udelad publikation": "",
}


def punkt_data(punkt: Punkt) -> dict:
    λ, φ = punkt.geometri.koordinater
    return {
        "Punkt": punkt.ident,
        "Nord": φ,
        "Øst": λ,
    }


def gældende_DVR90_koordinat(punkt: Punkt) -> Optional[Koordinat]:
    koordinatsæt = [
        k
        for k in punkt.koordinater
        if k.srid.name == SRID.DVR90 and k.registreringtil is None
    ]
    if not koordinatsæt:
        return

    return koordinatsæt[0]


def kote_data(punkt: Punkt) -> Koordinat:
    koordinater = gældende_DVR90_koordinat(punkt)
    if koordinater is None:
        return {}
    return {
        "Hvornår": koordinater.t,
        "Kote": koordinater.z,
        "σ": koordinater.sz,
    }


def punktrække(punkt: Punkt) -> dict:
    """
    Oversætter atributter på en observationstype til en post,
    der kan bruges som række i et punktoversigtsregneark til
    et nivellement-projekt.

    """
    return {
        **basisrække(arkdef.PUNKTOVERSIGT),
        **PUNKTOVERSIGT_KONSTANTE_FELTER,
        **punkt_data(punkt),
        **kote_data(punkt),
    }


def nyt_ark(arkdefinition: arkdef.ArkDefinitionType) -> pd.DataFrame:
    """Returnerer en tom pandas.dataframe med kolonner baseret på arkdefinition."""
    columns = arkdefinition.keys()
    return pd.DataFrame(columns=columns).astype(arkdefinition)


def til_nyt_ark(
    entiteter: list,
    arkdefinition: arkdef.ArkDefinitionType,
    rækkemager: Callable,
    sorter_efter: Union[str, List[str]] = None,
) -> pd.DataFrame:
    """
    Konverterer poster af en given entitet til rækker i en `pandas.DataFrame` (et ark).

    """
    data_dict = (rækkemager(entitet) for entitet in entiteter)
    data_df = pd.DataFrame(data_dict, columns=arkdefinition.keys())
    ark = frame.append_df(nyt_ark(arkdefinition), data_df)
    if sorter_efter is not None:
        return ark.sort_values(sorter_efter)
    return ark


til_nyt_ark_observationer = partial(
    til_nyt_ark,
    arkdefinition=arkdef.OBSERVATIONER,
    rækkemager=observationsrække,
    sorter_efter="Hvornår",
)
til_nyt_ark_observationer.__doc__ = (
    "Konverterer observationer til rækker i en ny `pandas.DataFrame`."
)


til_nyt_ark_punktoversigt = partial(
    til_nyt_ark,
    arkdefinition=arkdef.PUNKTOVERSIGT,
    rækkemager=punktrække,
    sorter_efter="Punkt",
)
til_nyt_ark_punktoversigt.__doc__ = (
    "Konverterer punkter til rækker i en ny `pandas.DataFrame`."
)


def skriv_data(uddata: BinaryIO, faner: Mapping[str, pd.DataFrame]):
    """
    Skriver observationer og punkter til givet uddata.

    """
    with pd.ExcelWriter(
        uddata, mode="a", if_sheet_exists="replace", engine="openpyxl"
    ) as writer:
        for navn, ark in faner.items():
            ark.to_excel(writer, sheet_name=navn, index=False)
