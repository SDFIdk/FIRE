"""
Nivellementskriterier og hjælpefunktionalitet.

Nøjagtighedskrav (også kaldet forkastelseskriterier) for nivellementmålinger
samt de erfarede og i databasen indtastede empiriske spredninger per afstandsenhed,
som bruges som á priori-spedninger for en given opmåling.

Nøjagtighedskrav:

|   Metode  |       MGL       |        MGL         |      MTL      |        MTL         |
|           |  Forkastelses-  | Empirisk spredning | Forkastelses- | Empirisk spredning |
|           |    kriterium    |  (brugt á priori)  |   kriterium   |  (brugt á priori)  |
|    Krav   | [mm / sqrt(km)] |  [mm / sqrt(km)]   |     [ppm]     |       [ppm]        |
|-----------|-----------------|--------------------|---------------|--------------------|
| Præcision |             2.0 |                0.6 |           2.0 |                1.5 |
| Kvalitet  |             2.5 |                1.0 |           2.5 |                2.0 |
| Detail    |             3.0 |                1.5 |           3.0 |                3.0 |
| Eksternt  |             5.0 |                    |               |                    |

"""

import itertools as it
from typing import (
    List,
    Mapping,
    Tuple,
)

from fire.api.niv import (
    NivMetode,
    Nøjagtighed,
)


FORKASTELSESKRITERIUM: Mapping[Tuple[Nøjagtighed, NivMetode], float] = {
    (Nøjagtighed.Præcision, NivMetode.MotoriseretGeometriskNivellement): 2.0,
    (Nøjagtighed.Kvalitet, NivMetode.MotoriseretGeometriskNivellement): 2.5,
    (Nøjagtighed.Detail, NivMetode.MotoriseretGeometriskNivellement): 3.0,
    (Nøjagtighed.Præcision, NivMetode.MotoriseretTrigonometriskNivellement): 2.0,
    (Nøjagtighed.Kvalitet, NivMetode.MotoriseretTrigonometriskNivellement): 2.5,
    (Nøjagtighed.Detail, NivMetode.MotoriseretTrigonometriskNivellement): 3.0,
}
"Implementerer forkastelseskriterier jævnfør nøjagtighedskrav i modulets dokumentation."

EMPIRISK_SPREDNING: Mapping[Tuple[Nøjagtighed, NivMetode], float] = {
    (Nøjagtighed.Præcision, NivMetode.MotoriseretGeometriskNivellement): 0.6,
    (Nøjagtighed.Kvalitet, NivMetode.MotoriseretGeometriskNivellement): 1.0,
    (Nøjagtighed.Detail, NivMetode.MotoriseretGeometriskNivellement): 1.5,
    (Nøjagtighed.Præcision, NivMetode.MotoriseretTrigonometriskNivellement): 1.5,
    (Nøjagtighed.Kvalitet, NivMetode.MotoriseretTrigonometriskNivellement): 2.0,
    (Nøjagtighed.Detail, NivMetode.MotoriseretTrigonometriskNivellement): 3.0,
}
"Implementerer empiriske spredninger (brugt á priori) jævnfør nøjagtighedskrav i modulets dokumentation."


def mildeste_kvalitetskrav(
    nøjagtigheder: List[Nøjagtighed],
    metoder: List[NivMetode],
    mapping: dict = EMPIRISK_SPREDNING,
) -> float:
    """
    Returnerer mildeste (højeste værdi) kvalitets-kriterium i enheden [mm / km ** (1/2)]
    ud fra kombination af flere mulige kombinationer af nøjagtighed og metoder.

    """
    return max(
        mapping[kombination]
        for kombination in it.product(nøjagtigheder, metoder)
        if kombination in mapping
    )
