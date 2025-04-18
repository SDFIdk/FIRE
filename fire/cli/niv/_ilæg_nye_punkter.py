import getpass
import math
from itertools import chain
from datetime import datetime

import click
import pandas as pd

import fire.cli
from fire import uuid
from fire.api.model import (
    GeometriObjekt,
    Point,
    Punkt,
    PunktInformation,
    Sagsevent,
    SagseventInfo,
    EventType,
    FikspunktsType,
)
from fire.api.model.geometry import (
    normaliser_lokationskoordinat,
)
from fire.io.regneark import arkdef
import fire.io.dataframe as frame

from . import (
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    niv,
    skriv_ark,
    opret_region_punktinfo,
    er_projekt_okay,
)

FIKSPUNKTSYPER = {
    "GI": FikspunktsType.GI,
    "MV": FikspunktsType.MV,
    "HØJDE": FikspunktsType.HØJDE,
    "JESSEN": FikspunktsType.JESSEN,
    "VANDSTANDSBRÆT": FikspunktsType.VANDSTANDSBRÆT,
}


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
def ilæg_nye_punkter(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyoprettede punkter i databasen.

    Nye punkter tilføjes i fanebladet "Nyetablerede punkter" i projektregnearket
    og et typisk kald vil være::

        fire niv ilæg-nye-punkter SAG

    Under fanebladet "Nyetablerede punkter" findes et antal kolonner hvor information
    om de nye punkter indtastes. En linje pr. nyt punkt. For at tilføje et punkt skal
    følgende kolonner være udfyldt:

    \b
    - Et foreløbigt navn
    - En længdegrad/Y, Nord (UTM eller grader)
    - En breddegrad/X, Øst (UTM eller grader)
    - En angivelse af fikspunktets type

    .. image:: ../workshop/figures/firenivilægpunkter.PNG
        :width: 800
        :alt: Opret nye punkter, excel-visning

    De resterende kolonner kan også udfyldes, men den videre proces er ikke
    afhængig af dem. Det man ikke kan udfylde, er "Landsnummer" og "uuid", da det først
    genereres det øjeblik punktet lægges i databasen.

    Fikspunktstypen afgør hvilket interval landsnummerets løbenummer placeres i. Der kan
    vælges mellem følgende typer:

    \b
    - GI
    - MV
    - HØJDE
    - JESSEN
    - VANDSTANDSBRÆT

    Hvis et punkt angives som værende et GI-punkt får det tildelt både et landsnummer og
    et GI-nummer. Det næste ledige GI-nummer vælges automatisk.

    .. note::
        Koordinater kan skrives både med UTM-format og med gradetal. ``fire`` genkender
        selv formatet og konverterer til geografiske koordinater, som er standard i ``fire``.

    Under afmærkning kan følgende typer indtastes:

    1. ukendt
    2. bolt
    3. lodret bolt
    4. skruepløk
    5. ingen

    Ved oprettelse af punktet indsættes automatisk en ``ATTR:bemærkning`` med info om
    nyetablering i indeværende år af den givne sagsbehandler. Sidstnævnte fremstår som
    brugerens B-nummer medmindre andet er angivet med ``--sagsbehandler`` når kommandoen
    kaldes.

    Samtidigt med at punkter lægges i databasen opdateres sagsregnearket også. Når
    :program:`fire niv ilæg-nye-punkter` har kørt indeholder fanen "Nyetablerede punkter"
    også punkternes netop tildelte landsnumre og UUID'er.

    """
    er_projekt_okay(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")

    # Opbyg oversigt over nyetablerede punkter
    nyetablerede = find_faneblad(
        projektnavn, "Nyetablerede punkter", arkdef.NYETABLEREDE_PUNKTER
    )
    n = nyetablerede.shape[0]

    if n == 0:
        fire.cli.print("Ingen nyetablerede punkter at registrere")
        return

    landsnummer_pit = fire.cli.firedb.hent_punktinformationtype("IDENT:landsnr")
    beskrivelse_pit = fire.cli.firedb.hent_punktinformationtype("ATTR:beskrivelse")
    bemærkning_pit = fire.cli.firedb.hent_punktinformationtype("ATTR:bemærkning")
    h_over_terræn_pit = fire.cli.firedb.hent_punktinformationtype(
        "AFM:højde_over_terræn"
    )
    attr_gi_pit = fire.cli.firedb.hent_punktinformationtype("ATTR:GI_punkt")
    attr_mv_pit = fire.cli.firedb.hent_punktinformationtype("ATTR:MV_punkt")
    attr_højde_pit = fire.cli.firedb.hent_punktinformationtype("ATTR:højdefikspunkt")
    attr_vandstand_pit = fire.cli.firedb.hent_punktinformationtype(
        "ATTR:vandstandsmåler"
    )
    assert landsnummer_pit is not None, "IDENT:landsnr ikke fundet i database"
    assert beskrivelse_pit is not None, "ATTR:beskrivelse ikke fundet i database"
    assert bemærkning_pit is not None, "ATTR:bemærkning ikke fundet i database"
    assert h_over_terræn_pit is not None, "AFM:højde_over_terræn ikke fundet i database"
    assert attr_gi_pit is not None, "ATTR:GI_punkt ikke fundet i database"
    assert attr_mv_pit is not None, "ATTR:MV_punkt ikke fundet i database"
    assert attr_højde_pit is not None, "ATTR:højdefikspunkt ikke fundet i database"
    assert attr_vandstand_pit is not None, "ATTR:vandstandsmåler ikke fundet i database"

    punkter = {}
    fikspunktstyper = []
    punktinfo = []

    # Opret punkter
    fire.cli.print(f"Behandler punkter")
    # Index frasorterer automatisk blanke linjer og er dermed mere robust.
    # Bemærkes, at felter med usynlige tegn som mellemrum IKKE resulterer
    # i en tom linje og en sådan vil fremtvinge en fejl pga ugyldigt input
    for i in nyetablerede.index:
        # Et tomt tekstfelt kan repræsenteres på en del forskellige måder...
        # Punkter udstyret med uuid er allerede registrerede
        if str(nyetablerede.uuid[i]) not in ["", "None", "nan"]:
            continue

        lokation = normaliser_lokationskoordinat(
            nyetablerede["Øst"][i], nyetablerede["Nord"][i], "DK"
        )

        # Skab nyt punktobjekt
        punkter[i] = Punkt(
            id=uuid(),
            geometriobjekter=[GeometriObjekt(geometri=Point(lokation))],
        )

        try:
            fikspunktstype = FIKSPUNKTSYPER[nyetablerede["Fikspunktstype"][i].upper()]
        except KeyError:
            fire.cli.print(
                f"FEJL: '{nyetablerede['Fikspunktstype'][i]}' er ikke en gyldig fikspunktsype! Vælg mellem GI, MV, HØJDE, JESSEN og VANDSTANDSBRÆT",
                bg="red",
                bold=True,
            )
            raise SystemExit(1)

        fikspunktstyper.append(fikspunktstype)

    # sagsevent for punkter
    er = "er" if len(punkter) > 1 else ""
    sagsevent_punkter = sag.ny_sagsevent(
        beskrivelse=f"Oprettelse af punkt{er} ifm. {projektnavn}",
        punkter=list(punkter.values())
        )
    fire.cli.firedb.indset_sagsevent(sagsevent_punkter, commit=False)
    fire.cli.firedb.session.flush()  # hvis noget ikke virker får vi fejl her!

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": sagsevent_punkter.registreringfra,
        "Hvem": sagsbehandler,
        "Hændelse": "punktoprettelse",
        "Tekst": sagsevent_punkter.sagseventinfos[0].beskrivelse,
        "uuid": sagsevent_punkter.id,
    }
    sagsgang = frame.append(sagsgang, sagsgangslinje)

    # Opret punktinfo
    fire.cli.print(f"Behandler punktinformationer")
    for i, punkt in punkter.items():
        # Tilføj punktets højde over terræn som punktinformation, hvis anført
        try:
            ΔH = float(nyetablerede["Højde over terræn"][i])
        except (TypeError, ValueError):
            ΔH = 0
        if math.isnan(ΔH):
            ΔH = 0.0
        if not pd.isna(nyetablerede["Højde over terræn"][i]):
            pi_h = PunktInformation(
                infotype=h_over_terræn_pit,
                punkt=punkt,
                tal=ΔH,
            )
            punktinfo.append(pi_h)

        # Tilføj punktets afmærkning som punktinformation, selv hvis ikke anført
        afm_id = 4999  # AFM:4999 = "ukendt"
        afm_ids = {
            "ukendt": 4999,
            "bolt": 2700,
            "lodret bolt": 2701,
            "skruepløk": 2950,
            "ingen": 5998,
        }

        if not pd.isna(nyetablerede["Afmærkning"][i]):
            # Afmærkningsbeskrivelse
            afm = str(nyetablerede["Afmærkning"][i]).lower()
            # Første ord i afmærkningsbeskrivelsen
            afm_første = afm.split()[0].rstrip(":;,.- ").lstrip("afm:")

            if afm_første.isnumeric():
                afm_id = int(afm_første)
            else:
                afm_id = afm_ids.get(afm, 4999)

            afmærkning_pit = fire.cli.firedb.hent_punktinformationtype(f"AFM:{afm_id}")
            if afmærkning_pit is None:
                afm_id = 4999
                afmærkning_pit = fire.cli.firedb.hent_punktinformationtype("AFM:4999")
            beskrivelse = (
                afmærkning_pit.beskrivelse.replace("-\n", "")
                .replace("\n", " ")
                .rstrip(".")
                .strip()
            )

        if afm_id == 4999:
            fire.cli.print(
                f"ADVARSEL: Nyoprettet punkt index {i} har ingen gyldig afmærkning anført",
                fg="red",
                bg="white",
                bold=True,
            )

        # Grundet den lidt kluntede løsning med AFM:nnnn punktinfo er fx AFM:2700 (bolt)
        # registreret som en tekst-punktinformation (frem for flag, som ville være den
        # ideelle løsning) og tekst attributten skal derfor udfyldes. Vi bruger
        # tekstnøgle til afm_ids.
        afm_txts = {v: k for k, v in afm_ids.items()}
        punktinfo.append(
            PunktInformation(
                infotype=afmærkning_pit,
                punkt=punkt,
                tekst=afm_txts[afm_id].capitalize(),
            )
        )

        # Tilføj punktbeskrivelsen som punktinformation, hvis anført
        beskrivelse = nyetablerede["Beskrivelse"][i]
        if pd.isna(beskrivelse) or beskrivelse == "":
            navn = nyetablerede["Foreløbigt navn"][i]
            fire.cli.print(
                f"FEJL: Beskrivelse for punkt '{navn}' ikke angivet!",
                fg="white",
                bg="red",
                bold=True,
            )
            fire.cli.firedb.session.rollback()
            raise SystemExit
        punktinfo.append(
            PunktInformation(
                infotype=beskrivelse_pit,
                punkt=punkt,
                tekst=beskrivelse,
            )
        )

        # Tilknyt regionskode til punktet
        punktinfo.append(opret_region_punktinfo(punkt))

        # Tilknyt ATTR:bemærkning
        punktinfo.append(
            PunktInformation(
                infotype=bemærkning_pit,
                punkt=punkt,
                tekst=f"Nyetb. {datetime.now().year} {sagsbehandler}",
            )
        )

    # tilknyt diverse punktinfo baseret på fikspunktstypen
    gi_punkter = []
    for punkt, fikspunktstype in zip(punkter.values(), fikspunktstyper):
        if fikspunktstype == FikspunktsType.GI:
            gi_punkter.append(punkt)
            punktinfo.append(PunktInformation(infotype=attr_gi_pit, punkt=punkt))

        if fikspunktstype == FikspunktsType.HØJDE:
            punktinfo.append(PunktInformation(infotype=attr_højde_pit, punkt=punkt))

        if fikspunktstype == FikspunktsType.MV:
            punktinfo.append(PunktInformation(infotype=attr_mv_pit, punkt=punkt))

        if fikspunktstype == FikspunktsType.VANDSTANDSBRÆT:
            punktinfo.append(PunktInformation(infotype=attr_vandstand_pit, punkt=punkt))

    # Tilknyt G.I-numre
    gi_identer = fire.cli.firedb.tilknyt_gi_numre(gi_punkter)
    punktinfo.extend(gi_identer)

    # Tilknyt landsnumre til punkter
    landsnumre = dict(
        zip(
            punkter.keys(),
            fire.cli.firedb.tilknyt_landsnumre(punkter.values(), fikspunktstyper),
        )
    )
    punktinfo.extend(landsnumre.values())

    # sagsevent for punktinfo
    sagsevent_punktinfo = sag.ny_sagsevent(
        beskrivelse=f"Oprettelse af punktinfo ifm. {projektnavn}",
        punktinformationer=punktinfo
    )
    fire.cli.firedb.indset_sagsevent(sagsevent_punktinfo, commit=False)
    fire.cli.firedb.session.flush()  # hvis noget ikke virker får vi fejl her!

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": sagsevent_punktinfo.registreringfra,
        "Hvem": sagsbehandler,
        "Hændelse": "punktinfoindsættelse",
        "Tekst": sagsevent_punktinfo.sagseventinfos[0].beskrivelse,
        "uuid": sagsevent_punktinfo.id,
    }
    sagsgang = frame.append(sagsgang, sagsgangslinje)

    # Opdater regneark
    for k in punkter.keys():
        nyetablerede.at[k, "uuid"] = punkter[k].id
        nyetablerede.at[k, "Landsnummer"] = landsnumre[k].tekst

    # Drop numerisk index
    nyetablerede = nyetablerede.reset_index(drop=True)

    # Forbered  resultater til resultatregneark
    resultater = {"Sagsgang": sagsgang, "Nyetablerede punkter": nyetablerede}

    spørgsmål = click.style("Du indsætter nu ", fg="white", bg="red")
    spørgsmål += click.style(
        f"{len(punkter)} punkter ", fg="white", bg="red", bold=True
    )
    spørgsmål += click.style(f"i ", fg="white", bg="red")
    spørgsmål += click.style(f"{fire.cli.firedb.db}", fg="white", bg="red", bold=True)
    spørgsmål += click.style("-databasen - er du sikker?", fg="white", bg="red")
    if bekræft(spørgsmål):
        # Indsæt rækker i database og skriv resultater til regneark
        fire.cli.firedb.session.commit()
        if skriv_ark(projektnavn, resultater):
            fire.cli.print(
                f"Punkter oprettet. Resultater skrevet til '{projektnavn}.xlsx'"
            )
    else:
        fire.cli.firedb.session.rollback()
