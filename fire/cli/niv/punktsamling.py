import getpass

import click
import pandas as pd
from sqlalchemy.exc import (
    NoResultFound,
)

from fire import uuid
from fire.api.model import (
    Punkt,
    PunktSamling,
    Koordinat,
    Tidsserie,
    HøjdeTidsserie,
    Srid,
)
import fire.cli
from fire.cli.niv import (
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    niv,
    skriv_ark,
    er_projekt_okay,
    udled_jessenpunkt_fra_punktoversigt,
    afbryd_hvis_ugyldigt_jessenpunkt,
)
import fire.io.dataframe as frame
from fire.io.regneark import arkdef


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.option(
    "--jessenpunkt",
    "jessenpunkt_ident",
    type=str,
    help="Angiv Jessenpunktet for punktsamlingen",
)
@click.option(
    "--punktsamlingsnavn",
    default="",
    type=str,
    help="Angiv punktsamlingens navn",
)
@click.option(
    "--punkter",
    default="",
    type=str,
    help="Angiv kommasepareret liste over punkter som skal indgå i punktsamlingen",
)
@click.option(
    "--punktoversigt",
    "anvend_punktoversigt",
    default=False,
    type=bool,
    is_flag=True,
    help="Angiver om punktoversigten skal anvendes til at indlæse punkter i punktsamlingen",
)
def opret_punktsamling(
    jessenpunkt_ident: str,
    projektnavn: str,
    punktsamlingsnavn: str,
    punkter: str,
    anvend_punktoversigt: bool,
    **kwargs,
) -> None:
    """
    Opretter et Punktsamlings-ark på sagen, som efterfølgende kan redigeres.

    Det primære formål med denne funktion er at oprette en ny punktsamling og tilhørende
    tidsserier. Oplysningerne kan efterfølgen redigeres, og man kan tilføje punkter og
    tidsserier til punktsamlingen. Bemærk, at "Formål"-kolonnerne ikke må være tomme.

    Resultatet skrives til et eksisterende projekt-regneark i fanerne "Punktgruppe" og
    "Højdetidsserier". Fanerne overskrives ikke, så man kan køre denne funktion flere
    gange, for at oprette flere punktsamlinger samtidig i samme regneark.

    Programmet skal vide hvilket Jessenpunkt det skal bruge. Dette angives lettest med
    ``--jessenpunkt``, som skal være jessenpunktets IDENT. Fx::

        fire niv opret-punktsamling SAG --jessenpunkt 81022

    Alternativt kan man med flaget ``--punktoversigt`` bede programmet om at bruge
    "Punktoversigt"-fanens fastholdte punkt til at udlede jessenpunktet. Hertil kræves
    det, at "Punktoversigt"-fanen er til stede i sags-regnearket, samt at der kun er
    netop ét fastholdt punkt. Eks::

        fire niv opret-punktsamling SAG --punktoversigt

    Det er nødvendigt at anvende enten ``--jessenpunkt`` eller ``--punktoversigt``. Angives
    begge, bliver ``--jessenpunkt`` brugt.

    Punktsamlingens navn angives med ``--punktsamlingsnavn``. Udelades denne, anvendes
    default-navnet "PUNKTSAMLING_[JESSENNR]".

    Nye punktsamlinger oprettes altid med Jessenkoten 0, og dette bliver således
    også referencekoten for nye tidsserier som kobles til punktsamlingen.

    Jessenpunktet indsættes altid i arket som medlem af punktsamlingen. Derudover kan man, for at
    lette opgaven med at tilføje flere punkter og tidsserier til arket, angive en kommasepareret
    liste af punkter med ``--punkter`` som programmet automatisk indsætter i arket.
    Punkterne indsættes da med default tidsserienavne og formål. Eks::

        fire niv opret-punktsamling SAG --jessenpunkt 81022 --punkter "SKEJ,RDIO,RDO1"

    Alternativt kan man igen anvende ``--punktoversigt``, som fortæller programmet at det
    skal udvide listen af punkter valgt med ``--punkter``, med punkterne i
    "Punktoversigt"-fanen. Eks::

        fire niv opret-punktsamling SAG --jessenpunkt 81022 --punkter "SKEJ,RDIO,RDO1" --punktoversigt

    Efter endt redigering kan oplysningerne ilægges databasen med ``ilæg-punktsamling`` og
    ``ilæg-tidsserie``.
    """
    er_projekt_okay(projektnavn)

    # fjern whitespace og split streng op i liste
    if punkter == "":
        punkter = []
    else:
        punkter = "".join(punkter.split()).split(",")

    punktsamling_ark = find_faneblad(
        projektnavn, "Punktgruppe", arkdef.PUNKTGRUPPE, ignore_failure=True
    )
    højdetidsserie_ark = find_faneblad(
        projektnavn, "Højdetidsserier", arkdef.HØJDETIDSSERIE, ignore_failure=True
    )

    resultater = {}

    # Hent Punktoversigten, hvis den er tilvalgt
    if anvend_punktoversigt:
        punktoversigt = find_faneblad(
            projektnavn, "Punktoversigt", arkdef.PUNKTOVERSIGT
        )
    else:
        punktoversigt = None

    # Find Jessenpunkt.
    #   Gøres enten fra angivet ident, eller udledes fra Punktoversigten
    if jessenpunkt_ident:
        # Prioritér punkter som matcher på Jessennummer da dette er mest intuitivt.
        jessenpunkt = fire.cli.firedb.hent_punkt(jessenpunkt_ident)
    elif punktoversigt is not None:
        # Find jessenpunktet ud fra oplysningerne i Punktoversigt-arket
        jessenpunkt_kote, jessenpunkt = udled_jessenpunkt_fra_punktoversigt(
            punktoversigt
        )
    else:
        # Hverken Punktoversigt eller jessenpunktets ident er givet.
        fire.cli.print(
            f"FEJL: Intet Jessenpunkt angivet, og kan ikke udlede Jessenpunkt fra Punktoversigten, da den er fravalgt.",
            fg="black",
            bg="yellow",
        )
        raise SystemExit(1)

    afbryd_hvis_ugyldigt_jessenpunkt(jessenpunkt)

    # Find Punkter.
    if punktoversigt is not None:
        # Udvid brugerspecificeret liste af punkter med punkter fra Punktoversigten.
        punkter.extend(list(punktoversigt["Punkt"]))

    # Hent punkter fra FIRE
    punkter = fire.cli.firedb.hent_punkt_liste(punkter, ignorer_ukendte=False)

    # Opret en ny Punktsamling
    ps = opret_ny_punktsamling(jessenpunkt, punkter, punktsamlingsnavn)
    ps_data, hts_data = generer_arkdata(ps)

    # Opret ark som skal gemmes.
    punktsamling_ark = frame.append(
        punktsamling_ark,
        pd.DataFrame.from_records(data=ps_data, columns=arkdef.PUNKTGRUPPE),
    )

    højdetidsserie_ark = frame.append(
        højdetidsserie_ark,
        pd.DataFrame.from_records(data=hts_data, columns=arkdef.HØJDETIDSSERIE),
    )
    # Sorter højdetidsserie-arket
    højdetidsserie_ark.sort_values(
        by=["Punktgruppenavn", "Er Jessenpunkt", "Tidsserienavn", "Punkt"],
        ascending=[True, False, False, True],
        inplace=True,
    )

    resultater.update(
        {"Punktgruppe": punktsamling_ark, "Højdetidsserier": højdetidsserie_ark}
    )

    if skriv_ark(projektnavn, resultater):
        fire.cli.print(
            f"Punktsamlinger oprettet. Rediger nu Navne og Formål og tilføj Punkter og Tidsserier"
        )
        fire.cli.åbn_fil(f"{projektnavn}.xlsx")

    return


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.option(
    "--jessenpunkt",
    "jessenpunkt_ident",
    type=str,
    help="Angiv Jessenpunktet for punktsamlingen",
)
@click.option(
    "--punktsamlingsnavn",
    default="",
    type=str,
    help="Angiv punktsamlingens navn",
)
@click.option(
    "--punkter",
    default="",
    type=str,
    help="Angiv kommasepareret liste over punkter som skal tilføjes til punktsamlingen",
)
@click.option(
    "--punktoversigt",
    "anvend_punktoversigt",
    default=False,
    type=bool,
    is_flag=True,
    help="Angiver om punktoversigten skal anvendes til at indlæse punkter i punktsamlingen",
)
def udtræk_punktsamling(
    jessenpunkt_ident: str,
    projektnavn: str,
    punktsamlingsnavn: str,
    punkter: str,
    anvend_punktoversigt: bool,
    **kwargs,
) -> None:
    """
    Udtræk en eller flere punktsamlinger fra databasen

    Det primære formål med denne funktion er at udtrække oplysninger om en eksisterende
    punktsamling og de tilhørende tidsserier. Oplysningerne kan redigeres, og man kan
    tilføje punkter og tidsserier til punktsamlingen.

    Resultatet skrives til et eksisterende projekt-regneark i fanerne "Punktgruppe" og
    "Højdetidsserier". Fanerne overskrives ikke, så man kan køre denne funktion flere
    gange, for at udtrække og redigere flere punktsamlinger samtidig i samme regneark.

    Oplysningerne udtrækkes ved at angive enten navnet på punktsamlingen::

        fire niv udtræk-punktsamling SAG --punktsamlingsnavn PUNKTSAMLING_81066

    eller punktsamlingens jessenpunkt::

        fire niv udtræk-punktsamling SAG --jessenpunkt 81066

    Hvis der findes flere punktsamlinger med samme jessenpunkt, trækkes alle
    punktsamlingerne ud. Det er nødvendigt at angive enten ``--punktsamlingsnavn`` eller
    ``--jessenpunkt``. Angives begge, ignoreres ``--jessenpunkt``.

    For at lette opgaven med at tilføje punkter og tidsserier til punktsamlingen, kan man
    angive en kommasepareret liste af punkter med ``--punkter`` som programmet automatisk
    indsætter i arket. Punkterne indsættes da med default tidsserienavne og formål. Eks::

        fire niv udtræk-punktsamling SAG --punktsamlingsnavn PUNKTSAMLING_81066 --punkter "SKEJ,RDIO,RDO1"

    Derudover kan man anvende ``--punktoversigt``, der ligesom ``--punkter`` fortæller
    programmet at det skal udvide listen af punkter med punkterne i "Punktoversigt"-fanen.
    Eks::

        fire niv udtræk-punktsamling SAG --punktsamlingsnavn PUNKTSAMLING_81066 --punktoversigt

    I tilfælde af at man har trukket flere punktsamlinger ud på én gang, bliver punkterne
    tilføjet til alle punktsamlingerne.

    Efter endt redigering kan ændringerne ilægges databasen med ``ilæg-punktsamling`` og
    ``ilæg-tidsserie``.
    """
    er_projekt_okay(projektnavn)

    # fjern whitespace og split streng op i liste
    if punkter == "":
        punkter = []
    else:
        punkter = "".join(punkter.split()).split(",")

    punktsamling_ark = find_faneblad(
        projektnavn, "Punktgruppe", arkdef.PUNKTGRUPPE, ignore_failure=True
    )
    højdetidsserie_ark = find_faneblad(
        projektnavn, "Højdetidsserier", arkdef.HØJDETIDSSERIE, ignore_failure=True
    )

    resultater = {}

    # Find Punktsamling(en/erne)
    if punktsamlingsnavn:
        # Find den valgte punktsamling. Hvis brugeren har valgt et jessenpunkt, ignoreres det
        try:
            punktsamlinger = list(fire.cli.firedb.hent_punktsamling(punktsamlingsnavn))
        except NoResultFound:
            fire.cli.print(
                f"FEJL! Punktsamling {punktsamlingsnavn} ikke fundet!",
                fg="black",
                bg="yellow",
            )
            raise SystemExit
    elif jessenpunkt_ident:
        # Udtræk alle punktsamlinger som har det valgte Jessenpunkt
        try:
            jessenpunkt = fire.cli.firedb.hent_punkt(jessenpunkt_ident)
        except NoResultFound:
            fire.cli.print(
                f"FEJL! Jessenpunkt {jessenpunkt_ident} ikke fundet!",
                fg="black",
                bg="yellow",
            )
            raise SystemExit

        afbryd_hvis_ugyldigt_jessenpunkt(jessenpunkt)
        punktsamlinger = [
            ps for ps in jessenpunkt.punktsamlinger if ps.jessenpunkt == jessenpunkt
        ]
    else:
        fire.cli.print(
            f"Hverken Jessenpunkt eller Punktsamling angivet. Afbryder...",
            fg="black",
            bg="yellow",
        )
        raise SystemExit

    # Hent Punktoversigten, hvis den er tilvalgt, og udvid punktlisten.
    if anvend_punktoversigt:
        punktoversigt = find_faneblad(
            projektnavn, "Punktoversigt", arkdef.PUNKTOVERSIGT
        )

        # Udvid brugerspecificeret liste af punkter med punkter fra Punktoversigten.
        punkter.extend(list(punktoversigt["Punkt"]))

    punkter = fire.cli.firedb.hent_punkt_liste(punkter, ignorer_ukendte=False)

    # Generer data som skal skrives til excel-ark
    ps_data, hts_data = [], []
    for ps in punktsamlinger:
        # Tilføj punkter til punktsamlingerne, hvis angivet af brugeren og hvis punktet ikke allerede er en del af punktsamlingen
        tidsserier = [
            opret_ny_tidsserie(punkt, ps)
            for punkt in punkter
            if punkt not in ps.punkter
        ]

        psd, htsd = generer_arkdata(ps)
        ps_data.extend(psd)
        hts_data.extend(htsd)

    # Opret ark som skal gemmes.
    punktsamling_ark = frame.append(
        punktsamling_ark,
        pd.DataFrame.from_records(data=ps_data, columns=arkdef.PUNKTGRUPPE),
    )

    højdetidsserie_ark = frame.append(
        højdetidsserie_ark,
        pd.DataFrame.from_records(data=hts_data, columns=arkdef.HØJDETIDSSERIE),
    )
    # Sorter højdetidsserie-arket
    højdetidsserie_ark.sort_values(
        by=["Punktgruppenavn", "Er Jessenpunkt", "Tidsserienavn", "Punkt"],
        ascending=[True, False, False, True],
        inplace=True,
    )

    resultater.update(
        {"Punktgruppe": punktsamling_ark, "Højdetidsserier": højdetidsserie_ark}
    )

    if skriv_ark(projektnavn, resultater):
        fire.cli.print(
            f"Punktsamlinger udtrukket. Rediger nu Formål og tilføj Tidsserier, "
            f"eller kontrollér at oplysningerne er korrekte."
        )
        fire.cli.åbn_fil(f"{projektnavn}.xlsx")

    return


def find_eller_opret_jessenkote(
    jessenpunkt: Punkt, jessenkote: float, kotesystem: Srid
) -> Koordinat:
    """
    Finder et Koordinat-objekt i databasen med givet punkt, jessenkote, og kotesystem

    Hvis der findes mere end ét Koordinat så returneres det først fundne. Hvis der ikke
    eksisterer et sådant Koordinat, så oprettes og returneres et nyoprettet koordinat, som
    man sidenhen kan vælge at lægge i databasen.

    Bemærk at denne funktion er tiltænkt situationer hvor en punktsamling forsøges ilagt
    databasen med en jessenkote som ikke findes. Dog kan den også bruges til at finde
    eller oprette arbitrære Koordinater.
    """
    try:
        # Filterer med vilje ikke på RegistreringTil = None, idet jessenpunktet godt
        # kan have tidsserier i andre punktsamlinger, hvis tidsserie-koordinater også
        # har SRID'en TS:jessen.
        # RegistreringTil = None vil kun finde det nyeste koord. som altså kan ændre
        # kote.
        # Der forventes kun ét resultat, men søgningen kan i edge-cases returnere
        # flere koordinater med identisk z-værdi, hvorfor der bare tages den først
        # fundne, som også burde være den første i tid.
        jessenkoordinat = [
            k
            for k in jessenpunkt.koordinater
            if k.srid == kotesystem and k.z == jessenkote
        ][0]
    except IndexError:

        fire.cli.print(
            f"BEMÆRK: Jessenkote ikke fundet i databasen. \n"
            f"Opretter nyt Jessenkoordinat med koten {jessenkote} [m]",
            fg="black",
            bg="yellow",
        )

        jessenkoordinat = Koordinat(
            punkt=jessenpunkt,
            srid=kotesystem,
            # hvilket tidspunkt skal den nye jessenkote gælde fra?
            # default er "current_timestamp"
            # t=None,
            z=jessenkote,
            sz=0,
        )

    return jessenkoordinat


def find_punktsamling(
    jessenpunkt: Punkt,
    punktsamlingsnavn: str = "",
) -> PunktSamling:
    """Finder en punktsamling ud fra angivet navn og jessenpunkt."""

    punktsamling = fire.cli.firedb.hent_punktsamling(punktsamlingsnavn)

    # Sikr at den fundne Punktsamling også har korrekt Jessenpunkt
    if punktsamling.jessenpunkt != jessenpunkt:
        fire.cli.print(
            f"FEJL: Jessenpunktet '{punktsamling.jessenpunkt.ident}' for punktsamlingen '{punktsamlingsnavn}' "
            f"er ikke det samme som det angivne Jessenpunkt '{jessenpunkt.ident}'",
            fg="black",
            bg="yellow",
        )
        raise SystemExit(1)

    return punktsamling


def er_punktsamling_unik(
    punktsamling_A: PunktSamling, punktsamlinger: list[PunktSamling] = []
) -> tuple[set[str], set[str], set[str]]:
    """
    Undersøg om en Punktsamling A udgør en unik samling af punkter.

    Givet Punktsamling A (herved forstås mængden af punkter i punktsamlingen) undersøges
    der for alle andre Punktsamlinger B flg:
        1. Er A lig med B
        2. Er A en delmængde af B (Er A et "subset" af B)
        3. Er B en delmængde af A (Er A et "superset" af B)

    Returnerer for hvert af de ovenstående tilfælde, en mængde af navne på punktsamlinger
    der falder inden for de 3 kategorier.
    """
    if not isinstance(punktsamling_A, PunktSamling):
        raise TypeError("'punktsamling' er ikke en instans af PunktSamling")

    # Mængde af punkter i Punktsamling A
    punkter_A = {pkt.ident for pkt in punktsamling_A.punkter}

    if not punktsamlinger:
        punktsamlinger = fire.cli.firedb.hent_alle_punktsamlinger()

    # Initialiser lister
    ligmed, subset, superset = set(), set(), set()
    for punktsamling_B in punktsamlinger:

        # Lad være med at sammenligne Punktsamlingen med sig selv
        if punktsamling_A.navn == punktsamling_B.navn:
            continue

        # Mængde af punkter i Punktsamling B
        punkter_B = {pkt.ident for pkt in punktsamling_B.punkter}

        if punkter_A == punkter_B:
            ligmed.add(punktsamling_B.navn)
        elif punkter_A.issubset(punkter_B):
            subset.add(punktsamling_B.navn)
        elif punkter_A.issuperset(punkter_B):
            superset.add(punktsamling_B.navn)

    return ligmed, subset, superset


def opret_ny_tidsserie(
    punkt: Punkt, punktsamling: PunktSamling, tidsserienavn: str = None
) -> Tidsserie:
    """
    Opretter ny højdetidsserie

    Hvis intet tidsserienavn angives, så bruges default-navnet: [IDENT]_HTS_[JESSENNR]. Hvis der findes
    en tidsserie med samme navn i forvejen, vil funktionen fejle.
    """
    if not tidsserienavn:
        tidsserienavn = (
            f"{punkt.ident}_HTS_{punktsamling.jessenpunkt.jessennummer}"  # Default navn
        )

    try:
        tidsserie = fire.cli.firedb.hent_tidsserie(tidsserienavn)
    except NoResultFound:
        pass
    else:
        fire.cli.print(
            f"FEJL: Tidsserien '{tidsserienavn}' eksisterer allerede. ",
            fg="black",
            bg="yellow",
        )
        raise SystemExit

    if punkt not in punktsamling.punkter:
        punktsamling.tilføj_punkter([punkt])

    tidsserie = HøjdeTidsserie(
        punkt=punkt,
        punktsamling=punktsamling,
        navn=tidsserienavn,
        formål=f"",
    )

    return tidsserie


def opret_ny_punktsamling(
    jessenpunkt: Punkt, punkter: list[Punkt], punktsamlingsnavn: str = None
) -> PunktSamling:
    """
    Opretter ny punktsamling og tilhørende højdetidsserier

    Hvis intet punktsamlingsnavn angives, så bruges default-navnet PUNKTSAMLING_[JESSENNR].
    Hvis der findes en punktsamling med samme navn i forvejen, vil funktionen fejle.

    Punkter som skal indgå i punktsamling angives med "punkter". Der oprettes også
    højdetidsserier for alle disse punkter. Tidsserierne oprettes med default-navne.
    """
    if not punktsamlingsnavn:
        punktsamlingsnavn = f"PUNKTSAMLING_{jessenpunkt.jessennummer}"  # Default navn

    try:
        punktsamling = fire.cli.firedb.hent_punktsamling(punktsamlingsnavn)
    except NoResultFound:
        pass
    else:
        fire.cli.print(
            f"FEJL: Punktsamlingen '{punktsamlingsnavn}' eksisterer allerede. "
            f"Anvend 'fire niv udtræk-punktsamling' for at udtrække og redigere i eksisterende punktsamlinger.",
            fg="black",
            bg="yellow",
        )
        raise SystemExit

    # fjern dubletter med list(set( ... ))
    punkter = list(set([jessenpunkt] + punkter))
    punktsamling = PunktSamling(
        navn=punktsamlingsnavn,
        formål="",
        jessenpunkt=jessenpunkt,
        jessenkoordinat=None,  # Nye punktsamlinger får ikke nogen jessenkote
        punkter=punkter,
    )

    # Opret tidsserier for alle de nye punkter
    tidsserier = [opret_ny_tidsserie(punkt, punktsamling) for punkt in punkter]

    return punktsamling


def generer_arkdata(punktsamling: PunktSamling) -> tuple[list, list]:
    """Genererer data ud fra en Punktsamling, til indsættelse i punktsamlings- og højdetidsseriearkene"""
    ps_data = [
        (
            punktsamling.navn,
            punktsamling.jessenpunkt.ident,
            punktsamling.jessenpunkt.jessennummer,
            punktsamling.jessenkote,
            punktsamling.formål,
        )
    ]

    # Finder først punktsamlingens tidsserier
    hts_data = [
        (
            punktsamling.navn,
            hts.punkt.ident,
            ("x" if hts.punkt == punktsamling.jessenpunkt else ""),
            hts.navn,
            hts.formål,
            "Jessen",
        )
        for hts in punktsamling.tidsserier
        if hts.registreringtil is None
    ]

    # Dernæst finder vi punktsamlingens punkter, som ikke har nogen tidsserier
    hts_data += [
        (
            punktsamling.navn,
            punkt.ident,
            ("x" if punkt == punktsamling.jessenpunkt else ""),
            "Ingen tidsserie fundet",
            "Ingen tidsserie fundet",
            "Jessen",
        )
        for punkt in punktsamling.punkter
        if punkt
        not in [
            hts.punkt for hts in punktsamling.tidsserier if hts.registreringtil is None
        ]
    ]

    return ps_data, hts_data
