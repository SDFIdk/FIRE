from dataclasses import dataclass
from typing import (
    Iterable,
    Optional,
)

import numpy as np
import pandas as pd  # type: ignore


class Post:
    """
    Klasse til nedarving i dataklasser, der spiller sammen med pandas.

    """

    @classmethod
    def asdf(cls, rows: Iterable = None) -> pd.DataFrame:
        typedict = cls.__annotations__
        if rows is None:
            return pd.DataFrame(columns=typedict).astype(typedict)
        data = (cls(*row) for row in rows)
        return pd.DataFrame(data=data, columns=typedict).astype(typedict)

    @classmethod
    def map(cls, rows: Iterable) -> pd.DataFrame:
        return (cls(*row) for row in rows)


@dataclass
class TidsseriePost(Post):
    punkt_id: Optional[str] = None
    dato: Optional[np.datetime64] = None
    kote: Optional[float] = None
    jessen_id: Optional[str] = None
    # er_jessen_punkt: Optional[bool] = None
    landsnr: Optional[str] = None


@dataclass
class ObservationsPost(Post):
    registreringfra: Optional[np.datetime64] = None
    opstillingspunktid: Optional[str] = None
    sigtepunktid: Optional[str] = None
    koteforskel: Optional[float] = None
    nivlaengde: Optional[float] = None
    opstillinger: Optional[int] = None
    spredning_afstand: Optional[float] = None
    spredning_centrering: Optional[float] = None
    observationstypeid: Optional[str] = None
    observationstidspunkt: Optional[np.datetime64] = None
    uuid: Optional[str] = None


@dataclass(order=True)
class MuligTidsserie(Post):
    skridt: int
    srid: str

    def jessen_id(self):
        return self.srid[self.srid.index(":") + 1 :]
