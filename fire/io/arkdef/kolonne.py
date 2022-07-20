class FILOVERSIGT:
    Filnavn = "Filnavn"
    Type = "Type"
    σ = "σ"
    δ = "δ"


class NYETABLEREDE_PUNKTER:
    Foreløbigt_navn = "Foreløbigt navn"
    Landsnummer = "Landsnummer"
    Nord = "Nord"
    Øst = "Øst"
    Fikspunktstype = "Fikspunktstype"
    Beskrivelse = "Beskrivelse"
    Afmærkning = "Afmærkning"
    Højde_over_terræn = "Højde over terræn"
    uuid = "uuid"


class OBSERVATIONER:
    """Kolonnenavne for nivellement-observationer"""

    # Journalnummer for observationen
    Journal = "Journal"
    # Indikerer, om punktet skal udelades i beregningen.
    # Markeres med et lille 'x', hvis det er tilfældet.
    Sluk = "Sluk"
    # Fra-dato for observationens gyldighed
    Fra = "Fra"
    # Til-dato for observationens gyldighed
    Til = "Til"
    # Koteforskel mellem opstillingspunktet og sigtepunktet
    ΔH = "ΔH"
    # Nivellementlængde
    L = "L"
    # Antal opstillinger
    Opst = "Opst"
    # Empirisk spredning per afstandsenhed [mm * km ** -1/2]
    σ = "σ"
    # Empirisk centreringsfejl per opstilling [ppm]
    δ = "δ"
    # Kommentar i regnearket
    Kommentar = "Kommentar"
    # Observationstidspunkt
    Hvornår = "Hvornår"
    # Meteorologiske parametre
    T = "T"
    Sky = "Sky"
    Sol = "Sol"
    Vind = "Vind"
    Sigt = "Sigt"
    # Projekt
    Kilde = "Kilde"
    #
    Type = "Type"
    # Observationspostens ID i databasen
    uuid = "uuid"


class PUNKTOVERSIGT:
    # Punktets ident
    Punkt = "Punkt"
    # Fastholder punktets data i beregninger
    Fasthold = "Fasthold"
    # Observationstidspunkt for målte kote, etc.
    Hvornår = "Hvornår"
    # Vinkelret højde fra geoiden
    Kote = "Kote"
    # Empirisk spredning per afstand
    σ = "σ"
    Ny_kote = "Ny kote"
    Ny_σ = "Ny σ"
    Δ_kote_mm = "Δ-kote [mm]"
    Opløft_mm_år = "Opløft [mm/år]"
    # Referencesystem
    System = "System"
    # Northing
    Nord = "Nord"
    # Easting
    Øst = "Øst"
    # Punktets ID i databasen
    uuid = "uuid"
    #
    Udelad_publikation = "Udelad publikation"


class REVISION:
    Punkt = "Punkt"
    Attribut = "Attribut"
    Talværdi = "Talværdi"
    Tekstværdi = "Tekstværdi"
    Sluk = "Sluk"
    Ny_værdi = "Ny værdi"
    id = "id"
    Ikke_besøgt = "Ikke besøgt"


class SAG:
    Dato = "Dato"
    Hvem = "Hvem"
    Hændelse = "Hændelse"
    Tekst = "Tekst"
    uuid = "uuid"


class PARAM:
    Navn = "Navn"
    Værdi = "Værdi"
