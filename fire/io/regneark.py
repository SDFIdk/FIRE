"""
I/O-modul til hånderting af regneark

"""

from typing import (
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

from fire.api.model.punkttyper import (
    Koordinat,
    Punkt,
    ObservationsTypeID,
    GeometriskKoteforskel,
    TrigonometriskKoteforskel,
)
from fire.api.niv import (
    NivMetode,
    DVR90_navn,
)
from fire.cli.niv import (
    ARKDEF_OBSERVATIONER,
    ARKDEF_PUNKTOVERSIGT,
    ArkDefinitionType,
    normaliser_lokationskoordinat,
)


# TODO: TO-BE
# import abc
# class Ark(metaclass=abc.ABCMeta):
#     def __init__(self, definition: ArkDefinitionType):
#         self.definition = definition
#     @abc.abstractmethod
#     def gem(self, filename, orm_entities):
#         pass


def nyt_ark(ark_definition: ArkDefinitionType) -> pd.DataFrame:
    columns = ark_definition.keys()
    return pd.DataFrame(columns=columns).astype(ark_definition)


def basisrække(arkdefinition: ArkDefinitionType) -> Mapping[str, None]:
    """
    Returnerer en dict-instans med arkdefinitionens nøgler
    og `None` som standard-værdi

    """
    return {key: None for key in arkdefinition}


MAPPER = {
    ObservationsTypeID.geometrisk_koteforskel: NivMetode.MGL.name,
    ObservationsTypeID.trigonometrisk_koteforskel: NivMetode.MTL.name,
}
"Oversætter observationstypeid til det forkortede navn for observationstypen."


OBSERVATIONER_KONSTANTE_FELTER = {
    "Journal": "",
    "Sluk": "",
    "Kommentar": "",
    "Kilde": "",
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
        **basisrække(ARKDEF_OBSERVATIONER),
        **OBSERVATIONER_KONSTANTE_FELTER,
        **observations_data(observation),
    }


PUNKTOVERSIGT_KONSTANTE_FELTER = {
    "Fasthold": "",
    "System": "DVR90",
    "Udelad publikation": "",
}


def punkt_data(punkt: Punkt) -> dict:
    WGS84_lonlat = punkt.geometri.koordinater
    λ, φ = normaliser_lokationskoordinat(*WGS84_lonlat)
    return {
        "Punkt": punkt.ident,
        "Nord": φ,
        "Øst": λ,
        "uuid": punkt.id,
    }


def gældende_DVR90_koordinat(punkt: Punkt) -> Optional[Koordinat]:
    koordinatsæt = [
        k
        for k in punkt.koordinater
        if k.srid.name == DVR90_navn and k.registreringtil is None
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
        **basisrække(ARKDEF_PUNKTOVERSIGT),
        **PUNKTOVERSIGT_KONSTANTE_FELTER,
        **punkt_data(punkt),
        **kote_data(punkt),
    }


def til_nyt_ark(
    entiteter: list,
    arkdef: ArkDefinitionType,
    rækkemager: Callable,
    sorter_efter: Union[str, List[str]] = None,
) -> pd.DataFrame:
    """
    Konverterer poster af en given entitet til rækker i en `pandas.DataFrame` (et ark)

    """
    data_dict = (rækkemager(entitet) for entitet in entiteter)
    data_df = pd.DataFrame(data_dict, columns=arkdef.keys())
    ark = nyt_ark(arkdef).append(data_df)
    if sorter_efter is not None:
        return ark.sort_values(sorter_efter)
    return ark


def skriv_data(uddata: BinaryIO, faner: Mapping[str, pd.DataFrame]):
    """
    Skriver observationer og punkter til givet uddata.

    """
    ewkw = dict(encoding="utf-8", index=False)
    with pd.ExcelWriter(uddata, mode="a", if_sheet_exists="replace") as writer:
        for navn, ark in faner.items():
            ark.to_excel(writer, sheet_name=navn, **ewkw)
