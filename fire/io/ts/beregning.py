from typing import (
    Any,
    Iterable,
    Optional,
    Union,
)
import datetime as dt

import numpy as np

from fire.io.arkdef import (
    mapper,
)
from fire.api.niv.gama_beregner import (
    DataMapper,
    Observation,
    Punkt,
    InternalData,
    FASTHOLD,
    FASTHOLD_IKKE,
)
from fire.io.ts.post import (
    ObservationsPost,
    TidsseriePost,
)


def til_gama_observation(observation: ObservationsPost) -> Observation:
    return Observation(
        journal="",
        fra=observation.opstillingspunktid,
        til=observation.sigtepunktid,
        nivlaengde=observation.nivlaengde,
        koteforskel=observation.koteforskel,
        opstillinger=observation.opstillinger,
        sigma=observation.spredning_afstand,
        delta=observation.spredning_centrering,
        type=mapper.OBSTYPE.get(observation.observationstypeid, ""),
    )


def til_gama_opstillingspunkt(observation: ObservationsPost) -> Punkt:
    return Punkt(id=observation.opstillingspunktid, fasthold=FASTHOLD_IKKE, kote=0.00)


class TidsserieMapper(DataMapper):
    def __init__(self):
        self._data = None

    def til_intern(self, data):
        # Gem data til udlæsning
        self._data = data

        # Oversæt
        projektnavn = data.get("projektnavn", "gama-beregning")
        projektbeskrivelse = f"Nivellementsprojekt {ascii(projektnavn)}"

        _observationer: Iterable[ObservationsPost] = data.get("observationer")
        observationer = [
            til_gama_observation(observation) for observation in _observationer
        ]

        punkter = [
            til_gama_opstillingspunkt(observation) for observation in _observationer
        ]
        _jessen_punkt = data.get("jessen_punkt")
        punkter.insert(
            0,
            Punkt(
                id=_jessen_punkt.punkt_id, fasthold=FASTHOLD, kote=_jessen_punkt.kote
            ),
        )

        fastholdte = {_jessen_punkt.punkt_id: _jessen_punkt.kote}
        _opstillingspunkter = set(observation.fra for observation in observationer)
        estimerede = tuple(_opstillingspunkter - {_jessen_punkt.punkt_id})
        gyldighedsdato = max(
            observation.observationstidspunkt for observation in _observationer
        )

        return InternalData(
            projektnavn=projektnavn,
            projektbeskrivelse=projektbeskrivelse,
            observationer=observationer,
            fastholdte=fastholdte,
            estimerede=estimerede,
            gyldighedsdato=gyldighedsdato,
        )

    def fra_intern(self, data: InternalData) -> Any:
        assert data.resultat is not None, f"Resultat er `None`."

        jessen = self._data.get("jessen_punkt")

        def jessen_id_eller_ej(punkt_id):
            if jessen.punkt_id == punkt_id:
                return jessen.jessen_id

        return [
            TidsseriePost(
                punkt_id=punkt.id,
                dato=pydate_to_npdate(punkt.gyldig),
                kote=punkt.kote,
                jessen_id=jessen_id_eller_ej(punkt.id),
            )
            for punkt in data.resultat
        ]


def pydate_to_npdate(
    date: Optional[Union[dt.date, dt.datetime]] = None
) -> np.datetime64:
    if date is None:
        raise ValueError("Date must be Python date or datetime.")
    return np.datetime64(date.isoformat())
