from dataclasses import dataclass
from typing import (
    Iterable,
    Optional,
)

import numpy as np
import pandas as pd  # type: ignore


def automap(cls):
    """
    Tilføj metode til at oversætte en liste af poster til
    en liste af dataklasse-instanser af den givne type.

    """
    @classmethod
    def map(cls, rows: Iterable) -> pd.DataFrame:
        """
        Oversæt en liste af poster til en liste
        af dataklasse-instanser af den givne type.

        """
        return (cls(*row) for row in rows)
    cls.map = map
    return cls


def automap_pandas(cls):
    """
    Integrér pandas i Python-dataklasser.

    """
    @classmethod
    def asdf(cls, rows: Iterable = None) -> pd.DataFrame:
        """
        Opret en Pandas DataFrame med dataklassens felter som kolonner.

        Med en liste af poster, oversættes disse til den givne
        dataklasse og alt returneres i en Pandas DataFrame.

        """
        typedict = cls.__annotations__
        if rows is None:
            return pd.DataFrame(columns=typedict).astype(typedict)
        data = (cls(*row) for row in rows)
        return pd.DataFrame(data=data, columns=typedict).astype(typedict)
    cls.asdf = asdf
    return cls


@automap_pandas
@automap
@dataclass
class TidsseriePost:
    punkt_id: Optional[str] = None
    dato: Optional[np.datetime64] = None
    kote: Optional[float] = None
    jessen_id: Optional[str] = None
    # er_jessen_punkt: Optional[bool] = None
    landsnr: Optional[str] = None


@automap_pandas
@automap
@dataclass
class ObservationsPost:
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


@automap_pandas
@automap
@dataclass(order=True)
class MuligTidsserie:
    skridt: int
    srid: str

    def jessen_id(self):
        return self.srid[self.srid.index(":") + 1 :]
