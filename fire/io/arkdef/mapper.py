from typing import (
    Any,
    Optional,
    Mapping,
    Union,
)

from fire.api.model.punkttyper import (
    Koordinat,
    Punkt,
    ObservationstypeID,
    GeometriskKoteforskel,
    TrigonometriskKoteforskel,
)
from fire.api.niv.enums import NivMetode
from fire.srid import SRID
from fire.io import arkdef
from fire.io.arkdef import kolonne
from fire.api.model.geometry import (
    normaliser_lokationskoordinat,
)


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
    if not h in _basisrækker:
        _basisrækker[h] = {key: None for key in arkdefinition}
    return _basisrækker[h]


OBSTYPE: dict = {
    ObservationstypeID.geometrisk_koteforskel: NivMetode.MGL.name,
    ObservationstypeID.trigonometrisk_koteforskel: NivMetode.MTL.name,
}
"Oversætter observationstypeid til det forkortede navn for observationstypen."


OBSERVATIONER_KONSTANTE_FELTER = {
    kolonne.OBSERVATIONER.Journal: "",
    kolonne.OBSERVATIONER.Sluk: "",
    kolonne.OBSERVATIONER.Kommentar: "",
    kolonne.OBSERVATIONER.Kilde: "",
    kolonne.OBSERVATIONER.Type: "",
}


def observations_data(
    observation: Union[GeometriskKoteforskel, TrigonometriskKoteforskel]
) -> dict:
    return {
        kolonne.OBSERVATIONER.Fra: observation.opstillingspunkt.ident,
        kolonne.OBSERVATIONER.Til: observation.sigtepunkt.ident,
        kolonne.OBSERVATIONER.L: observation.nivlængde,
        kolonne.OBSERVATIONER.ΔH: observation.koteforskel,
        kolonne.OBSERVATIONER.Opst: observation.opstillinger,
        kolonne.OBSERVATIONER.σ: observation.spredning_afstand,
        kolonne.OBSERVATIONER.δ: observation.spredning_centrering,
        kolonne.OBSERVATIONER.Hvornår: observation.observationstidspunkt,
        kolonne.OBSERVATIONER.Type: OBSTYPE.get(observation.observationstypeid, ""),
        kolonne.OBSERVATIONER.uuid: observation.id,
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
    kolonne.PUNKTOVERSIGT.Fasthold: "",
    kolonne.PUNKTOVERSIGT.System: "DVR90",
    kolonne.PUNKTOVERSIGT.Udelad_publikation: "",
}


def punkt_data(punkt: Punkt) -> dict:
    WGS84_lonlat = punkt.geometri.koordinater
    λ, φ = normaliser_lokationskoordinat(*WGS84_lonlat)
    return {
        kolonne.PUNKTOVERSIGT.Punkt: punkt.ident,
        kolonne.PUNKTOVERSIGT.Nord: φ,
        kolonne.PUNKTOVERSIGT.Øst: λ,
        kolonne.PUNKTOVERSIGT.uuid: punkt.id,
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
        kolonne.PUNKTOVERSIGT.Hvornår: koordinater.t,
        kolonne.PUNKTOVERSIGT.Kote: koordinater.z,
        kolonne.PUNKTOVERSIGT.σ: koordinater.sz,
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
