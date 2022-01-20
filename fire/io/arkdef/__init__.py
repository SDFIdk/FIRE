"""
Arkdefinitioner til ensartet arbejde med `pandas.DataFrame`s.

"""

from typing import (
    Mapping,
    Union,
)

from fire.io.arkdef import kolonne


ArkDefinitionType = Mapping[str, Union[type, str]]
"Regnearksdefinition (søjlenavne og -typer)"

FILOVERSIGT: ArkDefinitionType = {
    kolonne.FILOVERSIGT.Filnavn: str,
    kolonne.FILOVERSIGT.Type: str,
    kolonne.FILOVERSIGT.σ: float,
    kolonne.FILOVERSIGT.δ: float,
}

NYETABLEREDE_PUNKTER: ArkDefinitionType = {
    kolonne.NYETABLEREDE_PUNKTER.Foreløbigt_navn: str,
    kolonne.NYETABLEREDE_PUNKTER.Landsnummer: str,
    kolonne.NYETABLEREDE_PUNKTER.Nord: float,
    kolonne.NYETABLEREDE_PUNKTER.Øst: float,
    kolonne.NYETABLEREDE_PUNKTER.Fikspunktstype: str,
    kolonne.NYETABLEREDE_PUNKTER.Beskrivelse: str,
    kolonne.NYETABLEREDE_PUNKTER.Afmærkning: str,
    kolonne.NYETABLEREDE_PUNKTER.Højde_over_terræn: float,
    kolonne.NYETABLEREDE_PUNKTER.uuid: str,
}

OBSERVATIONER: ArkDefinitionType = {
    kolonne.OBSERVATIONER.Journal: str,
    kolonne.OBSERVATIONER.Sluk: str,
    kolonne.OBSERVATIONER.Fra: str,
    kolonne.OBSERVATIONER.Til: str,
    kolonne.OBSERVATIONER.ΔH: float,
    kolonne.OBSERVATIONER.L: float,
    kolonne.OBSERVATIONER.Opst: int,
    kolonne.OBSERVATIONER.σ: float,
    kolonne.OBSERVATIONER.δ: float,
    kolonne.OBSERVATIONER.Kommentar: str,
    kolonne.OBSERVATIONER.Hvornår: "datetime64[ns]",
    kolonne.OBSERVATIONER.T: float,
    kolonne.OBSERVATIONER.Sky: int,
    kolonne.OBSERVATIONER.Sol: int,
    kolonne.OBSERVATIONER.Vind: int,
    kolonne.OBSERVATIONER.Sigt: int,
    kolonne.OBSERVATIONER.Kilde: str,
    kolonne.OBSERVATIONER.Type: str,
    kolonne.OBSERVATIONER.uuid: str,
}

PUNKTOVERSIGT: ArkDefinitionType = {
    kolonne.PUNKTOVERSIGT.Punkt: str,
    kolonne.PUNKTOVERSIGT.Fasthold: str,
    kolonne.PUNKTOVERSIGT.Hvornår: "datetime64[ns]",
    kolonne.PUNKTOVERSIGT.Kote: float,
    kolonne.PUNKTOVERSIGT.σ: float,
    kolonne.PUNKTOVERSIGT.Ny_kote: float,
    kolonne.PUNKTOVERSIGT.Ny_σ: float,
    kolonne.PUNKTOVERSIGT.Δ_kote_mm: float,
    kolonne.PUNKTOVERSIGT.Opløft_mm_år: float,
    kolonne.PUNKTOVERSIGT.System: str,
    kolonne.PUNKTOVERSIGT.Nord: float,
    kolonne.PUNKTOVERSIGT.Øst: float,
    kolonne.PUNKTOVERSIGT.uuid: str,
    kolonne.PUNKTOVERSIGT.Udelad_publikation: str,
}

REVISION: ArkDefinitionType = {
    kolonne.REVISION.Punkt: str,
    kolonne.REVISION.Attribut: str,
    kolonne.REVISION.Talværdi: float,
    kolonne.REVISION.Tekstværdi: str,
    kolonne.REVISION.Sluk: str,
    kolonne.REVISION.Ny_værdi: str,
    kolonne.REVISION.id: float,
    kolonne.REVISION.Ikke_besøgt: str,
}

SAG: ArkDefinitionType = {
    kolonne.SAG.Dato: "datetime64[ns]",
    kolonne.SAG.Hvem: str,
    kolonne.SAG.Hændelse: str,
    kolonne.SAG.Tekst: str,
    kolonne.SAG.uuid: str,
}

PARAM: ArkDefinitionType = {
    kolonne.PARAM.Navn: str,
    kolonne.PARAM.Værdi: str,
}
