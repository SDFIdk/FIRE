import pathlib
from functools import partial
import getpass

import click
import pandas as pd

import fire.cli
from fire import uuid
from fire.api.model import (
    Punkt,
    Tidsserie,
    Koordinat,
    Beregning,
)
from fire.io.regneark import arkdef
from fire.io.formattering import forkort
import fire.io.dataframe as frame

from . import (
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    gyldighedstidspunkt,
    niv,
    skriv_ark,
    er_projekt_okay,
    hent_relevante_tidsserier,
    udled_jessenpunkt_fra_punktoversigt,
    KOTESYSTEMER,
)


def punktdata_ikke_skal_opdateres(punktdata: dict) -> bool:
    """
    Returnerer sand, hvis ingen koteopdatering er nødvendig.
    """
    return (
        # Blank linje (feltet er tomt)
        pd.isna(punktdata["Ny kote"])
        # Allerede registreret (eksisterer i databasen)
        or punktdata["uuid"] != ""
        # Tilbageholdt og skal derfor ikke gemmes, uanset hvad.
        or punktdata["Udelad publikation"] == "x"
    )


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
def ilæg_nye_koter(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyberegnede koter i databasen.

    Koter fra sagsregnearket lægges i databasen. Koter med "x" i kolonnen
    "Udelad publikation" udelades fra indlæsningen. Det samme gælder for koter med
    indhold i "uuid" kolonnen. Uuid'et er et database-ID og betyder at koten allerede
    er registreret i databasen.

    Ikke alt information i regnearket indlæses i databasen. De indlæste data for hver
    kote er

        1. Koten, "Ny kote"
        2. Spredningen på koten, "Ny σ"
        3. Højdereferencesystemet, "System"
        4. Beregningstidspunktet, "Hvornår"

    Herudover gemmes naturligvis hvilket punkt en kote hører til.
    Information om forskel mellem ny og gammel kote, samt estimeret opløfthastighed
    registreres ikke direkte i databasen. Denne information er dog tilgængelig i
    sagsregnearket, der lagres i databasen når sagen lukkes.

    Hvis koternes System er sat til "Jessen", så har programmet brug for at kende navnene
    på de Højdetidsserier som koterne skal tilknyttes. Dette angives i fanen
    "Højdetidsserier". Programmet tjekker samtidig, at oplysningerne om Højdetidsserierne
    i fanen er korrekte. Herunder, om den endelige beregnings fastholdte punkt og kote
    stemmer overens med Højdetidsseriernes jessenpunkt og referencekote.
    """
    er_projekt_okay(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")

    filnavn_gama_output = pathlib.Path(f"{projektnavn}-resultat-endelig.html")
    if not filnavn_gama_output.is_file():
        fire.cli.print(
            f"Sagsopdateringen kræver en outputfil fra GNU Gama {str(filnavn_gama_output)}"
        )
        raise SystemExit(1)

    # Indlæs regnearket
    punktoversigt = find_faneblad(
        projektnavn, "Endelig beregning", arkdef.PUNKTOVERSIGT
    )
    observationer = find_faneblad(projektnavn, "Observationer", arkdef.OBSERVATIONER)

    # Lav en kopi med de endelige resultater
    ny_punktoversigt = punktoversigt.copy()

    # Forbered data til kote-oprettelse
    if len(punktoversigt["System"].unique()) > 1:
        fire.cli.print(
            "FEJL: Flere forskellige højdereferencesystemer er angivet!",
            fg="white",
            bg="red",
            bold=True,
        )
        raise SystemExit()

    kotesystem = punktoversigt["System"][0]

    anvendt_srid = fire.cli.firedb.hent_srid(KOTESYSTEMER[kotesystem])

    # Hvis vi er ved at ilægge nye tidsserie-koter, så skal alle punkter have en
    # Højdetidsserie hvis jessenpunkt er det samme som det fastholdte punkt
    if anvendt_srid.name == "TS:jessen":
        # Højdetidsserie-fanebladet skal være til stede
        hts_ark = find_faneblad(
            projektnavn, "Højdetidsserier", arkdef.HØJDETIDSSERIE, ignore_failure=True
        )
        if hts_ark is None:
            fire.cli.print(
                f"FEJL: Fanebladet Højdetidsserier skal være til stede hvis du vil ilægge tidsserie-koter",
                fg="white",
                bg="red",
                bold=True,
            )
            raise SystemExit(1)

        fastholdt_kote, fastholdt_punkt = udled_jessenpunkt_fra_punktoversigt(
            punktoversigt
        )

    tid = gyldighedstidspunkt(projektnavn)
    ny_kote = partial(Koordinat, srid=anvendt_srid, t=tid)

    event_id = uuid()
    til_registrering = []
    tidsserier_til_registrering = []
    opdaterede_punkter = []

    for index, punktdata in punktoversigt.iterrows():
        if punktdata_ikke_skal_opdateres(punktdata):
            continue

        punkt = fire.cli.firedb.hent_punkt(punktdata["Punkt"])
        opdaterede_punkter.append(punkt)
        punktdata["uuid"] = event_id

        z = punktdata["Ny kote"]
        sz = punktdata["Ny σ"]
        kote = ny_kote(punkt=punkt, z=z, sz=sz)
        til_registrering.append(kote)
        ny_punktoversigt = frame.insert(ny_punktoversigt, index, punktdata)

        # Hvis man har anvendt TS:jessen så tilføjes den beregnede kote til en Tidsserie
        # som brugeren skal have specificeret i Højdetidsserier-arket.
        if anvendt_srid.name == "TS:jessen":

            # Gå igennem alle punktets tidsserier i arket
            opdaterede_tidsserier = hent_relevante_tidsserier(
                hts_ark, punkt, fastholdt_punkt, fastholdt_kote
            )

            for ts in opdaterede_tidsserier:
                ts.koordinater.append(kote)

            if not opdaterede_tidsserier:
                fire.cli.print(
                    f"FEJL: Kan ikke indsætte en ny højdetidsserie-kote {kote.z} for punkt {punkt.ident}."
                    f"Punktet er ikke tilknyttet nogle gyldige tidsserier!",
                    fg="white",
                    bg="red",
                    bold=True,
                )
                raise SystemExit(1)

            tidsserier_til_registrering.extend(opdaterede_tidsserier)

    if 0 == len(til_registrering):
        fire.cli.print("Ingen koter at registrere!", fg="yellow", bold=True)
        return

    # Tilknyt koter til observationer i en beregning
    observationer = observationer[
        observationer["Sluk"] == ""
    ]  # se bort fra slukkede observationer
    observationer = observationer[
        observationer["uuid"] != ""
    ]  # udvælg alle observationer med et database-ID
    observationer_i_beregning = fire.cli.firedb.hent_observationer(
        list(observationer["uuid"])
    )

    # det giver kun mening at oprette en beregning hvis der er relaterede observationer
    if not observationer_i_beregning:
        fire.cli.print(
            "FEJL: Beregning foretaget uden tilknytning til observationer i databasen!",
            fg="white",
            bg="red",
            bold=True,
        )
        raise SystemExit()

    n_koter = len(opdaterede_punkter)
    n_obs = len(observationer_i_beregning)
    # det giver kun mening at oprette en beregning hvis der er relaterede observationer
    if n_koter > n_obs:
        fire.cli.print(
            "FEJL: Færre observationer end beregnede koter registreret i databasen!",
            fg="white",
            bg="red",
            bold=True,
        )
        raise SystemExit()

    beregning = Beregning(
        observationer=observationer_i_beregning,
        koordinater=til_registrering,
    )

    # Vi vil ikke have alt for lange sagseventtekster (bl.a. fordi Oracle ikke
    # kan lide lange tekststrenge), så vi indsætter udeladelsesprikker hvis vi
    # opdaterer mere end 10 punkter ad gangen
    punktnavne = [p.ident for p in opdaterede_punkter]
    punktnavne = forkort(punktnavne)
    sagseventtekst = f"Opdatering af {kotesystem}-kote til {', '.join(punktnavne)}"
    clob_html = filnavn_gama_output.read_text()

    sagsevent = sag.ny_sagsevent(
        id=event_id,
        beskrivelse=sagseventtekst,
        htmler=[clob_html],
        koordinater=til_registrering,
        beregninger=[beregning],
    )
    fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)

    # Generer dokumentation til fanebladet "Sagsgang"
    # Variablen "registreringstidspunkt" har værdien "CURRENT_TIMESTAMP"
    # som udvirker mikrosekundmagi når den bliver skrevet til databasen,
    # men ikke er meget informativ for en menneskelig læser her i regne-
    # arkenes prosaiske verden. Derfor benytter vi pd.Timestamp.now(),
    # som ikke har mikrosekundmagi over sig, men som kan læses og giver
    # mening, selv om den ikke bliver eksakt sammenfaldende med det
    # tidsstempel hændelsen får i databasen. Det lever vi med.
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "Koteberegning",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = frame.append(sagsgang, sagsgangslinje)

    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    fire.cli.print(f"Ialt {n_koter} koter bestemt ud fra {n_obs} observationer\n")

    if hts_ark is not None and anvendt_srid.name == "TS:jessen":
        tsnavne = [ts.navn for ts in tidsserier_til_registrering]
        tsnavne = forkort(tsnavne)

        sagsevent_tidsserier = sag.ny_sagsevent(
            id=uuid(),
            beskrivelse=f"fire niv ilæg-nye-koter: Opdatering af tidsseriekoter til {', '.join(tsnavne)}",
            tidsserier=tidsserier_til_registrering,
        )
        fire.cli.firedb.indset_sagsevent(sagsevent_tidsserier, commit=False)

        sagsgangslinje = {
            "Dato": pd.Timestamp.now(),
            "Hvem": sagsbehandler,
            "Hændelse": "Opdatering af tidsseriekoter",
            "Tekst": sagsevent_tidsserier.sagseventinfos[0].beskrivelse,
            "uuid": sagsevent_tidsserier.id,
        }
        sagsgang = frame.append(sagsgang, sagsgangslinje)

    try:
        fire.cli.firedb.session.flush()
    except Exception as ex:
        # rul tilbage hvis databasen smider en exception
        fire.cli.firedb.session.rollback()
        fire.cli.print(f"Der opstod en fejl - koter for '{projektnavn}' IKKE indlæst!")
        fire.cli.print(f"Mulig årsag: {ex}")
    else:
        spørgsmål = click.style("Du indsætter nu ", fg="white", bg="red")
        spørgsmål += click.style(f"{n_koter} kote(r) ", fg="white", bg="red", bold=True)
        spørgsmål += click.style(f"i ", fg="white", bg="red")
        spørgsmål += click.style(
            f"{fire.cli.firedb.db}", fg="white", bg="red", bold=True
        )
        spørgsmål += click.style("-databasen - er du sikker?", fg="white", bg="red")

        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()

            # Skriv resultater til resultatregneark
            resultater = {"Sagsgang": sagsgang, "Resultat": ny_punktoversigt}
            if skriv_ark(projektnavn, resultater):
                fire.cli.print(
                    f"Koter registreret. Resultater skrevet til '{projektnavn}.xlsx'"
                )
