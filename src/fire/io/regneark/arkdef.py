from typing import (
    Mapping,
    Union,
)

ArkDefinitionType = Mapping[str, Union[type, str]]
"Regnearksdefinition (søjlenavne og -typer)"

FILOVERSIGT: ArkDefinitionType = {
    "Filnavn": str,
    "Type": str,
    "σ": float,
    "δ": float,
}

NYETABLEREDE_PUNKTER: ArkDefinitionType = {
    "Foreløbigt navn": str,
    "Landsnummer": str,
    "Nord": float,
    "Øst": float,
    "Fikspunktstype": str,
    "Beskrivelse": str,
    "Afmærkning": str,
    "Højde over terræn": float,
    "uuid": str,
}

OBSERVATIONER: ArkDefinitionType = {
    # Journalnummer for observationen
    "Journal": str,
    # Indikerer, om punktet skal udelades i beregningen.
    # Markeres med et lille 'x', hvis det er tilfældet.
    "Sluk": str,
    # Fra-dato for observationens gyldighed
    "Fra": str,
    # Til-dato for observationens gyldighed
    "Til": str,
    # Koteforskel mellem opstillingspunktet og sigtepunktet
    "ΔH": float,
    # Nivellementlængde
    "L": float,
    "Opst": int,
    # Empirisk spredning per afstandsenhed [mm * km ** -1/2]
    "σ": float,
    # Empirisk centreringsfejl per opstilling [ppm]
    "δ": float,
    # Kommentar i regnearket
    "Kommentar": str,
    # Observationstidspunkt
    "Hvornår": "datetime64[ns]",
    # Meteorologiske parametre
    "T": float,
    "Sky": int,
    "Sol": int,
    "Vind": int,
    "Sigt": int,
    # Projekt
    "Kilde": str,
    #
    "Type": str,
    # Observationspostens ID i databasen
    "uuid": str,
}
"Kolonnenavne og datatyper for nivellement-observationer"

PUNKTOVERSIGT: ArkDefinitionType = {
    # Punktets ident
    "Punkt": str,
    # Fastholder punktets data i beregninger
    "Fasthold": str,
    # Observationstidspunkt for målte kote, etc.
    "Hvornår": "datetime64[ns]",
    # Vinkelret højde fra geoiden
    "Kote": float,
    # Empirisk spredning per afstand
    "σ": float,
    "Ny kote": float,
    "Ny σ": float,
    "Δ-kote [mm]": float,
    "Opløft [mm/år]": float,
    # Referencesystem
    "System": str,
    # Northing
    "Nord": float,
    # Easting
    "Øst": float,
    # Punktets ID i databasen
    "uuid": str,
    #
    "Udelad publikation": str,
}

REVISION: ArkDefinitionType = {
    "Punkt": str,
    "Attribut": str,
    "Talværdi": float,
    "Tekstværdi": str,
    "Sluk": str,
    "Ny værdi": str,
    "id": float,
    "Ikke besøgt": str,
}

SAG: ArkDefinitionType = {
    "Dato": "datetime64[ns]",
    "Hvem": str,
    "Hændelse": str,
    "Tekst": str,
    "uuid": str,
}

PARAM: ArkDefinitionType = {
    "Navn": str,
    "Værdi": str,
}

PUNKTGRUPPE: ArkDefinitionType = {
    # Punktsamlingens navn. Udadtil kalder vi det punktgruppe
    "Punktgruppenavn": str,
    # Jessenpunktets ident
    "Jessenpunkt": str,
    # Jessenpunktets jessennummer
    "Jessennummer": str,
    # Jessenkoten som skal fastholdes.
    "Jessenkote": float,
    # Punktsamlingens formål / beskrivelse, fx nær-/fjernkontrol
    "Formål": str,
}

HØJDETIDSSERIE: ArkDefinitionType = {
    # Punktsamlingens navn
    "Punktgruppenavn": str,
    # Punktets ident
    "Punkt": str,
    # Er punktet jessenpunkt for punktsamlingen?
    "Er Jessenpunkt": str,
    "Tidsserienavn": str,
    # Tidsseriens formål
    "Formål": str,
    # Tidsseriens referencesystem.
    "System": str,
    # SRIDID udledes af System
    # TSTYPE er altid 2
}
