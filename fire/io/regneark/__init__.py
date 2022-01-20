"""
I/O-modul til håndtering af regneark

"""

from functools import partial
from typing import (
    Union,
    Mapping,
    List,
    Mapping,
    Union,
    Callable,
    BinaryIO,
)

import pandas as pd

from fire.io import arkdef
from fire.io.arkdef.mapper import (
    observationsrække,
    punktrække,
)


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
    ark = nyt_ark(arkdefinition).append(data_df)
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
    ewkw = dict(encoding="utf-8", index=False)
    with pd.ExcelWriter(
        uddata, mode="a", if_sheet_exists="replace", engine="openpyxl"
    ) as writer:
        for navn, ark in faner.items():
            ark.to_excel(writer, sheet_name=navn, **ewkw)
