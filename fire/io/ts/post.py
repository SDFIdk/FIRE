from dataclasses import dataclass
from typing import (
    Iterable,
)

import numpy as np
import pandas as pd


class Post:
    """
    Class decorator adding classmethod to create a new
    empty Pandas DataFrame based on dataclass annotations.

    """

    @classmethod
    def asdf(cls, rows: Iterable = None) -> pd.DataFrame:
        typedict = cls.__annotations__
        if rows is None:
            return pd.DataFrame(columns=typedict).astype(typedict)
        data = (cls(*row) for row in rows)
        return pd.DataFrame(data=data, columns=typedict).astype(typedict)

    @classmethod
    def map(cls, rows: Iterable = None) -> pd.DataFrame:
        return (cls(*row) for row in rows)


@dataclass
class TidsseriePost(Post):
    punkt_id: str = None
    dato: np.datetime64 = None
    kote: float = None
    jessen_id: str = None
    # er_jessen_punkt: bool = None
    landsnr: str = None


@dataclass
class ObservationsPost(Post):
    registreringfra: np.datetime64 = None
    opstillingspunktid: str = None
    sigtepunktid: str = None
    koteforskel: float = None
    nivlaengde: float = None
    opstillinger: int = None
    spredning_afstand: float = None
    spredning_centrering: float = None
    observationstypeid: str = None
    observationstidspunkt: np.datetime64 = None
    uuid: str = None


@dataclass(order=True)
class MuligTidsserie(Post):
    skridt: int
    srid: str

    def jessen_id(self):
        return self.srid[self.srid.index(":") + 1 :]
