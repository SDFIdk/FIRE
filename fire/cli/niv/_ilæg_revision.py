import re
import getpass
from datetime import datetime
from math import trunc, isnan

import click
import pandas as pd
from pyproj import Proj, Geod
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import DatabaseError

from fire import uuid
from fire.api.model import (
    EventType,
    GeometriObjekt,
    Koordinat,
    Point,
    Punkt,
    PunktInformation,
    PunktInformationTypeAnvendelse,
    FikspunktsType,
)
from fire.api.model.geometry import (
    normaliser_lokationskoordinat,
)
from fire.io.regneark import arkdef
import fire.io.dataframe as frame
import fire.cli
from fire.cli.niv import (
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    niv,
    skriv_ark,
    opret_region_punktinfo,
    er_projekt_okay,
)
from fire.cli.niv._udtræk_revision import LOKATION_DEFAULT


def opret_punktnavne_til_ikke_oprettede_punkter(ark: pd.DataFrame) -> pd.DataFrame:
    """
    Finder ikke-oprettede punkter og skriver  ``NYTPUNKT<#>`` i feltet til punktnavnet.

    Eksempel
    --------

        Før

        |   Punkt   |         Attribut        | ... |
        |-----------|-------------------------|-----|
        |           | LOKATION                |     |
        |           | ATTR:muligt_datumstabil |     |
        |           | ...                     |     |
        |           |                         |     |
        |           |                         |     |
        |           | OPRET                   |     |
        |           | ATTR:muligt_datumstabil |     |
        |           | ...                     |     |
        |           |                         |     |
        |           |                         |     |
        |           | OPRET                   |     |
        |           | ATTR:muligt_datumstabil |     |
        |           | ...                     |     |

        Efter

        |   Punkt   |         Attribut        | ... |
        |-----------|-------------------------|-----|
        |           | LOKATION                |     |
        |           | ATTR:muligt_datumstabil |     |
        |           | ...                     |     |
        |           |                         |     |
        |           |                         |     |
        | NYTPUNKT0 | OPRET                   |     |
        |           | ATTR:muligt_datumstabil |     |
        |           | ...                     |     |
        |           |                         |     |
        |           |                         |     |
        | NYTPUNKT1 | OPRET                   |     |
        |           | ATTR:muligt_datumstabil |     |
        |           | ...                     |     |

    """
    til_oprettelse = ark.query("Attribut == 'OPRET'")
    for i, _ in til_oprettelse.iterrows():
        ark.loc[i, "Punkt"] = f"NYTPUNKT{i}"
    return ark


def udfyld_udeladte_identer(ark: pd.DataFrame) -> pd.DataFrame:
    """
     Udfyld celler med udeladt ident i kolonnen Punkt.

     Første linje/række af punkt-oplysningerne har punktets
     ident i kolonnen Punkt, hvilket indikerer starten på et
     nyt punkts informationer.

     Formålet med funktionen er at tilføje punktets ident
     til hver række med punktoplysninger for punktet og
     frem til starten af næste punkt.

    Eksempel
     --------

         Før

         |   Punkt   |         Attribut        | ... |
         |-----------|-------------------------|-----|
         |  SKEJ     | LOKATION                |     |
         |           | ATTR:muligt_datumstabil |     |
         |           | ...                     |     |
         |           |                         |     |
         |           |                         |     |
         |  FYNO     | LOKATION                |     |
         |           | ATTR:muligt_datumstabil |     |
         |           | ...                     |     |
         |           |                         |     |
         |           |                         |     |
         |  OTTO     | LOKATION                |     |
         |           | ATTR:muligt_datumstabil |     |
         |           | ...                     |     |

         Efter

         |   Punkt   |         Attribut        | ... |
         |-----------|-------------------------|-----|
         |  SKEJ     | LOKATION                |     |
         |  SKEJ     | ATTR:muligt_datumstabil |     |
         |  SKEJ     | ...                     |     |
         |  SKEJ     |                         |     |
         |  SKEJ     |                         |     |
         |  FYNO     | LOKATION                |     |
         |  FYNO     | ATTR:muligt_datumstabil |     |
         |  FYNO     | ...                     |     |
         |  FYNO     |                         |     |
         |  FYNO     |                         |     |
         |  OTTO     | LOKATION                |     |
         |  OTTO     | ATTR:muligt_datumstabil |     |
         |  OTTO     | ...                     |     |


    """
    # kopiér de eksisterende værdier i kolonnen Punkt
    punkter = list(ark["Punkt"])

    # Udfyld med hvert punkts ident frem ti ldet næste punkt
    udfyldningsværdi = ""
    for (i, celleværdi_eksisterende) in enumerate(punkter):
        if (trimmet := celleværdi_eksisterende.strip()) != "":
            # Opdatér udfyldningsværdi, så alle felter
            # i samme kolonne får tilskrevet samme
            # værdi, indtil vi rammer næste punkt.
            udfyldningsværdi = trimmet

        # Overskriv kopien af den eksisterende værdi
        punkter[i] = udfyldningsværdi

    # Overskriv den eksisterende kolonne med alle overskrevne værdier.
    ark["Punkt"] = punkter

    return ark


# ------------------------------------------------------------------------------
# Her starter revisionsilæggelsesprogrammet
# ------------------------------------------------------------------------------
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
@click.argument(
    "bemærkning",
    nargs=-1,
    type=str,
)
def ilæg_revision(
    projektnavn: str,
    sagsbehandler: str,
    **kwargs,
) -> None:
    """Læg reviderede punktdata i databasen.

    Ændringer i revisionsregnearket, udtrukket med ``fire niv udtræk-revision``,
    lægges i databasen med dette program. Programmet understøtter primært punktrevision
    som en del af kommunalt vedligehold, men også mere avancerede brugsscenarier
    understøttes. De typiske ændringer i en revision er tilføjelse, ændring eller
    fjernelse af en attribut, samt opdatering af lokationskoordinater. Herudover er det
    også muligt at oprette nye punkter og koordinater.

    Revisionsregnearket er struktureret så punkter og tilhørende attributter grupperes
    sammen i blokke af rækker. Hver blok separeres af nogle tommer rækker. Første
    række i en blok adskiller sig fra de resterende, da den indeholder punktets primære
    ident, lokationskoordinat og har i et nyudtrukket revisionsark "x" i kolonnen
    "Ikke besøgt". Hver række i en blok tilsvarer et objekt i databasen. I kolonnen "Attribut"
    angives hvilken type objekt der er tale om og hører en værdi med til denne attribut
    er den angivet i enten "tal-" eller "tekstværdi" kolonennen.

    Ændring af information om et eksisterende punkt, altså en typisk punktrevision,
    starter med at fjerne krydset i "Ikke besøgt" for det punkt der skal ændres. Krydset
    har to praktiske formål:

    \b
        1. Skabe overblik i omfattende revisionsregneark
        2. Øge effektiviteten af indlæsning, da kun punkter uden kryds tages i betragtning

    Hvis en attributværdi skal ændres angives den nye værdi i kolonnen "Ny værdi". For
    tekstattributter vil der allerede stå en kopi af den eksisterende værdi, så det er
    nemt at lave små ændringer. Ved indlæsning i databasen medtages kun rækker hvor
    "Ny værdi" afviger fra den oprindelige.

    Hvis en attribut skal fjernes, gøres det ved at sætte "x" i kolonnen "Sluk". Det
    resulterer i at attributten afregistreres i databasen så den ikke længere fremgår
    som en aktuel værdi. Attributten slettes ikke, så det vil være muligt at genoprette
    den i tilfælde af fejl.

    Hvis en ny attribut skal tilføjes, gøres det ved at tilføje en ny række hvor kolonnerne
    "Attribut" og, hvis relevant, "Ny værdi" er udfyldt.

    Når alle ændringer er udført gemmes og lukkes regnearket, hvorefter ilægningskommandoen
    køres::

        fire niv ilæg-revision SAG

    \f

    **Eksempel**

    I det følgende eksempel demonstreres al den tilgængelige funktionalitet i
    :program:`fire niv ilæg-revision`. Det vil sige redigering af eksisterende information
    om et punkt og tilføjelse af nye punkter og koordinater. Sidstnævnte er avanceret
    funktionalitet der typisk kun er behov for i særtilfælde, fx oprettelse af en ny
    GNSS-stationer i Grønland.

    Først udtrækkets et revisionsregneark for et enkelt punkt med::

        fire niv udtræk-revision --db test SAG 96-01-09014

    Indholdet af regneark kan ses på figuren herunder

    .. image:: figures/fire_niv_ilæg_revision_før.png
        :width: 800
        :alt: Revisionsregneark udtrukket med ``fire niv udtræk-revision``.

    Inspiceres punktet med :program:`fire info punkt` ses det at de to stemmer overens,
    omend enkelte attributter er udeladt i regnearket.

    .. code-block:: console

        > fire info punkt --db test 96-01-09014

        --------------------------------------------------------------------------------
        PUNKT 96-01-09014
        --------------------------------------------------------------------------------
        Lokation                    POINT (10.5253353662749 56.231632845085)
        Oprettelsesdato             1951-07-01 00:00:00
        AFM:2779                    Plade mærket G.I.
        AFM:vertikal
        AFM:højde_over_terræn       0.45
        ATTR:beskrivelse            Agri Kirke.
                                    Punkt i tårn, N. side.
                                    0.47 m fra V. hjørne.
                                    0.17 m over grundsten.
        ATTR:højdefikspunkt
        ATTR:bemærkning             Rev. uge 44 2018 PN.
        REGION:DK
        IDENT:refgeo_id             390708
        IDENT:landsnr               96-01-09014

        --- KOORDINATER ---
        * 2009-11-16 09:27  EPSG:5799       n 100.00800 (2)
        * 1990-02-27 15:20  DK:GM91         n 100.05200 (5)

    På nedenstående figur ses markeret med gult de ændringer der er lavet i
    regnearket, med henblik på at tilpasse et eksisterende punkt og tilføje
    et nyt.

    .. image:: figures/fire_niv_ilæg_revision_efter.png
        :width: 800
        :alt: Revisionsregneark udtrukket med ``fire niv udtræk-revision``.


    For det eksisterende punkt er følgende ændringer lavet:

    \b
      - Lokationskoordinat opdateret.
      - ATTR:muligt_datumstabil tilføjet (ved at fjerne "x" i "Sluk").
      - ATTR:beskrivelse opdateret.
      - AFM:vertikal slukket (bemærk at indholdet i "Ny værdi" er slettet).
      - AFM:højde_over_terræn er opdateret.
      - ATTR:bemærkning er opdateret.
      - AFM:postament er tilføjet.
      - IDENT:GNSS med værdien "AGR2" er tilføjet.

    Derudover tilføjes et nyt punkt med følgende egenskaber:

    \b
      - Lokationskoordinat (56.231888 N; 10.525849 E)
      - Attributterne ATTR:beskrivelse, REGION:DK, AFM:horisontalvertikal og IDENT:GNSS
      - ETRS89-koordinat (EPSG:4937)
      - DVR90-kote (EPSG:5799)

    For at tilføje det nye punkt bruges den særlige attribut "OPRET", hvor lokationskoordinaten
    angives i "Ny værdi". De efterfølgenge rækker tilhører samme blok af attributter og
    tilknyttes alle til det nye punkt. Lokationskoordinaten kan både angives som UTM32-koordinat
    eller som geografisk koordinat.

    .. note::
        Bemærk at der *ikke* automatisk tilføjes attributter på punkter og den beskrevne
        metode er derfor en komplet manuel manøvre. Det vil typisk være smartere at bruge
        :program:`fire niv ilæg-nye-punkter` til at oprette nye danske fikspunkter, da
        landsnummer m.m. så oprettes korrekt.

    Oprettelse af nye koordinater sker ved at angive en SRID som attribut, og derefter
    indsætte udfylde "Ny værdi" på følgende form::

        x y z t sx sy sz

    Hvor `x`, `y` og `z` er de tre rumlige koordinatkomponenter, `t` er koordinatens
    tilblivelsestidspunkt givet i decimalår og `sx`, `sy` og `sz` er de tre
    koordinatkomponenters spredninger givet i mm. Indsættes koter, hvor kun z-komponenten
    er relevant, skrives `nan` i `x`, `y`, `sx` og `sy`. "Nan" står for "not a number"
    og fortæller programmet at denne værdi ikke er relevant. Tallene skal være adskilt
    af enten mellemrum eller linjeskift. Sidstenævnte kan øge læsbarheden af koordinaten,
    som set i figuren ovenfor.

    Ved kørsel af :program:`fire niv ilæg-revision` kontrolleres det om indholdet
    af revisionsarket er på den rette form hvorefter det forsøges indsættes i
    databasen. Er der fejl eller noget der virker forkert kommer programmet med
    en advarsel eller fejlrapport. Når alt går godt fås output i stil med nedenstående:

    .. code-block:: console

        > fire niv ilæg-revision --db test SAG
        Sags/projekt-navn: SAG  (026699f1-96bb-4503-8eab-d618c9a777bf)
        Sagsbehandler:     b012349

        Opretter nyt punkt 98ea4050: 56.231888 N 10.525849 E

        Behandler 2 punkter
        96-01-09014
            Opretter nyt punktinfo-element: ATTR:muligt_datumstabil
            Retter punktinfo-element: ATTR:beskrivelse
            Slukker: AFM:2779
            Slukker: AFM:højde_over_terræn
            Retter punktinfo-element: ATTR:bemærkning
            Opretter nyt punktinfo-element: AFM:postament
            Opretter nyt punktinfo-element: IDENT:GNSS
        98ea4050-d8fb-45df-9f20-80f70b8a75cd
            Opretter nyt punktinfo-element: ATTR:beskrivelse
            Opretter nyt punktinfo-element: REGION:DK
            Opretter nyt punktinfo-element: AFM:horisontalvertikal
            Opretter nyt punktinfo-element: IDENT:GNSS

        --------------------------------------------------
        Punkter færdigbehandlet, klar til at
        - oprette 9 attributter fordelt på 3 punkter
        - slukke for 2 attributter fordelt på 1 punkter
        - rette 2 attributter fordelt på 1 punkter
        - rette 1 lokationskoordinater
        Er du sikker på du vil indsætte ovenstående i test-databasen (ja/NEJ):
        ja
        Gentag svar for at bekræfte (ja/NEJ)
        ja
        Skriver: {'Sagsgang'}
        Til filen 'SAG.xlsx'
        Overskriver fanebladene {'Sagsgang'}
            med opdaterede versioner.
        Foregående versioner beholdes i 'ex'-filen 'SAG-ex.xlsx'

    Her gives en rapport over de ændringer der er laves, samt en afsluttende opsummering
    af revisionen. Her bør man inspicere outputtet for at sikre sig at det der indsættes
    i databasen er korrekt. Er det tilfældet kan man taste ja til at data indsættes.

    Efter revisionen er lagt i databasen kan vi nu tage et kig på de to opdatere punkter
    og se at ændringer er trådt i kraft:

    .. code-block:: console

        >fire info punkt --db test 96-01-09014

        --------------------------------------------------------------------------------
        PUNKT AGR2
        --------------------------------------------------------------------------------
        Lokation                    POINT (10.52533304 56.2316149)
        Oprettelsesdato             1951-07-01 00:00:00
        AFM:vertikal
        ATTR:højdefikspunkt
        REGION:DK
        IDENT:refgeo_id             390708
        IDENT:landsnr               96-01-09014
        ATTR:muligt_datumstabil
        ATTR:beskrivelse            Agri Kirke.
                                    Punkt i tårn, N. side.
                                    0.49 m fra V. hjørne.
                                    0.17 m over grundsten.
        ATTR:bemærkning             Rev. uge 46 2023 KE.
        AFM:postament
        IDENT:GNSS                  AGR2

        --- KOORDINATER ---
        * 2009-11-16 09:27  EPSG:5799       n 100.00800 (2)
        * 1990-02-27 15:20  DK:GM91         n 100.05200 (5)

        > fire info punkt --db test AGR3

        --------------------------------------------------------------------------------
        PUNKT AGR3
        --------------------------------------------------------------------------------
        Lokation                    POINT (10.525849 56.231888)
        Oprettelsesdato             2023-07-18 14:28:50.303283
        ATTR:beskrivelse            Parkeringsplads ved Agri Kirke
        REGION:DK
        AFM:horisontalvertikal
        IDENT:GNSS                  AGR3
        IDENT:landsnr               96-01-00008

        --- KOORDINATER ---
        * 2023-07-25 20:38  EPSG:5799       n 101.42400 (5)
        * 2023-07-18 04:40  EPSG:4937       n 10.5258490000, 56.2318880000, 101.32000  (15, 15, 45)

    """
    er_projekt_okay(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")
    fire.cli.print("")

    revision = find_faneblad(f"{projektnavn}-revision", "Revision", arkdef.REVISION)
    revision = opret_punktnavne_til_ikke_oprettede_punkter(revision)
    revision = udfyld_udeladte_identer(revision)

    # Frasortér irrelevante data
    # Undlad at behandle punkter, for hvilke der er sat et
    # `x` i kolonnen Ikke besøgt i første række for punktet.
    #
    # `find_faneblad` dropper tomme rækker ved indlæsning af regnearket,
    # men opdaterer ikke indekset. Dét gør vi, inden rækkerne gennemgås:
    revision = revision.reset_index(drop=True)
    # Find række-intervaller
    b_indekser = revision.Punkt.map(lambda s: s.strip() != "").values
    start_positioner = revision.index[b_indekser].values.tolist()
    slut_position = revision.index[-1] + 1
    grænser = start_positioner + [slut_position]
    # Slet rækker for ikke-besøgte punkter
    for (start, stop) in zip(grænser[:-1], grænser[1:]):
        ikke_besøgt = revision.loc[start]["Ikke besøgt"].strip().lower()
        besøgt = ikke_besøgt != "x"
        if besøgt:
            continue
        revision = revision.drop(range(start, stop), axis="index")

    if revision.empty:
        fire.cli.print(
            "Ingen besøgte punkter til ilægning. Stopper.", fg="yellow", bold=True
        )
        raise SystemExit

    # Udfyld udeladte identer
    punkter = list(revision["Punkt"])
    udfyldningsværdi = ""
    for i in range(len(punkter)):
        if punkter[i].strip() != "":
            udfyldningsværdi = punkter[i].strip()
            continue
        punkter[i] = udfyldningsværdi
    revision["Punkt"] = punkter

    # Find alle punkter, der skal nyoprettes
    nye_punkter = []
    oprettelse = revision.query("Attribut == 'OPRET'")
    for row in oprettelse.to_dict("records"):
        if row["id"] == -1:
            continue
        punkt = opret_punkt(row["Ny værdi"])
        fire.cli.print(f"Opretter nyt punkt {punkt.ident}: {row['Ny værdi']}")
        nye_punkter.append(punkt)

        # indsæt nyt punkt ID i Punkt kolonnen, for at kunne trække
        # dem ud med hent_punkt() senere
        erstat = lambda x: punkt.id if x == row["Punkt"] else x
        revision["Punkt"] = revision.Punkt.apply(erstat)

    revision = revision.query("Attribut != 'OPRET'")

    # Find alle lokationskoordinater, der skal korrigeres
    nye_lokationer = []
    lokation = revision.query("Attribut == 'LOKATION'")
    lokation = lokation.query("`Ny værdi` != ''")
    for row in lokation.to_dict("records"):
        # Ret kun, hvis værdien er forskellig fra den eksisterende.
        # Rationale: udtræk-revision indsætter samme værdier i de to kolonner
        # for at spare redigeringstid for brugerne.
        # Samme logik bruges længere nede for attributterne.
        if row["Tekstværdi"] == row["Ny værdi"]:
            continue

        punkt = fire.cli.firedb.hent_punkt(row["Punkt"])
        # gem her inden ny geometri tilknyttes punktet
        try:
            (λ1, φ1) = punkt.geometri.koordinater
        except AttributeError:
            # hvis ikke punktet har en lokationskoordinat bruger vi (11, 56), da dette
            # er koordinaten der skrives i revisionsregnearket ved udtræk når der
            # mangler en lokationskoordinat.
            (λ1, φ1) = LOKATION_DEFAULT

        go = læs_lokation(row["Ny værdi"])
        go.punkt = punkt
        nye_lokationer.append(go)
        (λ2, φ2) = go.koordinater

        g = Geod(ellps="GRS80")
        _, _, dist = g.inv(λ1, φ1, λ2, φ2)
        if dist >= 25:
            fire.cli.print(
                f"    ADVARSEL: Ny lokationskoordinat for {punkt.landsnummer} afviger {dist:.0f} m fra den gamle",
                fg="yellow",
                bold=True,
            )

    if len(nye_punkter) > 0 or len(nye_lokationer) > 0:
        sagsevent = sag.ny_sagsevent(
            beskrivelse="Oprettelse af nye punkter",
            punkter=nye_punkter,
            geometriobjekter=nye_lokationer,
        )
        fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)
        sagsgang = opdater_sagsgang(sagsgang, sagsevent, sagsbehandler)
        flush()

    revision = revision.query("Attribut != 'LOKATION'")

    # Find alle koordinater, der skal oprettes

    # Først skal vi bruge alle gyldige koordinatsystemnavne
    srider = fire.cli.firedb.hent_srider()
    sridnavne = [srid.name.upper() for srid in srider]

    # Så itererer vi over hele rammen og ignorerer ikke-koordinaterne
    nye_koordinater = []
    opdaterede_punkter = []
    for r in revision.to_dict("records"):
        sridnavn = r["Attribut"].upper()
        if sridnavn not in sridnavne:
            continue
        try:
            koord = [float(k.replace(",", ".")) for k in r["Ny værdi"].split()]
        except ValueError as ex:
            fire.cli.print(
                f"Ukorrekt koordinatformat:\n{'    '.join(r['Ny værdi'])}\n{ex}"
            )
            fire.cli.print(
                "Skal være på formen: 'x y z t sx sy sz', hvor ubrugte værdier sættes til 'nan'"
            )
            raise SystemExit(1)

        # Oversæt NaN til None
        koord = [None if isnan(k) else k for k in koord]

        # Tæt-på-kopi af kode fra "niv/ilæg_nye_koter.py". Her bør mediteres og overvejes
        # hvordan denne opgave kan parametriseres på en rimeligt generel måde, så den kan
        # udstilles i et "højniveau-API"
        srid = fire.cli.firedb.hent_srid(sridnavn)

        punkt = fire.cli.firedb.hent_punkt(r["Punkt"])
        opdaterede_punkter.append(r["Punkt"])

        # Det er ikke helt så nemt som i C at oversætte decimal-år til datetime
        år = trunc(koord[3])
        rest = koord[3] - år
        startdato = datetime(år, 1, 1)
        årlængde = datetime(år + 1, 1, 1) - startdato
        tid = startdato + rest * årlængde

        koordinat = Koordinat(
            srid=srid,
            punkt=punkt,
            x=koord[0],
            y=koord[1],
            z=koord[2],
            t=tid,
            sx=koord[4],
            sy=koord[5],
            sz=koord[6],
        )
        nye_koordinater.append(koordinat)

        # I Grønland er vi nødt til at duplikere geografiske koordinater til UTM24,
        # da Oracles indbyggede UTM-rutine er for ringe til at vi kan generere
        # udstillingskoordinater on-the-fly.
        if sridnavn in ("EPSG:4909", "EPSG:4747"):
            srid_utm24 = fire.cli.firedb.hent_srid("EPSG:3184")
            utm24 = Proj("proj=utm zone=24 ellps=GRS80", preserve_units=False)
            x, y = utm24(koord[0], koord[1])
            koordinat = Koordinat(
                srid=srid_utm24,
                punkt=punkt,
                x=x,
                y=y,
                z=None,
                t=tid,
                sx=koord[4],
                sy=koord[5],
                sz=None,
            )
            nye_koordinater.append(koordinat)

    n = len(opdaterede_punkter)
    if n > 0:
        punktnavne = sorted(list(set(opdaterede_punkter)))
        if len(punktnavne) > 10:
            punktnavne[9] = "..."
            punktnavne[10] = punktnavne[-1]
            punktnavne = punktnavne[0:10]
        koordinatoprettelsestekst = (
            f"Opdatering af {n} koordinater til {', '.join(punktnavne)}"
        )

        sagsevent = sag.ny_sagsevent(
            beskrivelse=koordinatoprettelsestekst,
            koordinater=nye_koordinater,
        )
        fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)
        sagsgang = opdater_sagsgang(sagsgang, sagsevent, sagsbehandler)
        flush()

    # Så tager vi fat på punktinformationerne
    til_opret = []
    til_ret = []
    til_sluk = []
    punkter_med_oprettelse = set()
    punkter_med_rettelse = set()
    punkter_med_slukning = set()

    # Først, tilknyt regionspunktinfo til nyoprettede punkter
    for p in nye_punkter:
        til_opret.append(opret_region_punktinfo(p))

    # Find identer for alle punkter, der indgår i revisionen
    identer = tuple(sorted(set(revision["Punkt"]) - set(["nan", ""])))
    fire.cli.print("")
    fire.cli.print(f"Behandler {len(identer)} punkter")

    # Så itererer vi over alle punkter
    for ident in identer:
        fire.cli.print(ident, fg="yellow", bold=True)

        # Hent punkt og alle relevante punktinformationer i databasen.
        # Her er det lidt sværere end for koordinaternes vedkommende:
        # Ved opdatering af eksisterende punkter vil vi gerne checke
        # infonøglerne, så vi er nødt til at hente det faktiske punkt,
        # med tilørende infonøgler, fra databasen
        try:
            punkt = fire.cli.firedb.hent_punkt(ident)
            infonøgler = {
                info.objektid: i for i, info in enumerate(punkt.punktinformationer)
            }
        except NoResultFound as ex:
            fire.cli.print(
                f"FEJL: Kan ikke finde punkt {ident}!",
                fg="yellow",
                bg="red",
                bold=True,
            )
            fire.cli.print(f"Mulig årsag: {ex}")
            raise SystemExit(1)

        # Hent alle revisionselementer for punktet fra revisionsarket
        rev = revision.query(f"Punkt == '{ident}'")

        for r in rev.to_dict("records"):
            pitnavn = r["Attribut"]
            sluk = r["Sluk"].strip() != ""

            # Tom attribut?
            if pitnavn == "":
                continue

            # Koordinatilægning?
            if pitnavn in sridnavne:
                continue

            # Midlertidigt aflukket element?
            if r["id"] < 0:
                continue

            # Det er en fejl at angive ny værdi for et element man slukker for.
            if sluk and r["Ny værdi"].strip() != "":
                fire.cli.print(
                    f"    * FEJL: 'Sluk' og 'Ny værdi' begge udfyldt: {r['Ny værdi']}",
                    fg="red",
                    bold=False,
                )
                continue

            if r["Tekstværdi"] != "" and not sluk:
                # Undgå at overskrive en eksisterende værdi med en usynlig blankværdi
                if r["Ny værdi"].strip() == "":
                    continue

                # Det er almindelig praksis ved revision at kopiere "Tekstværdi" til
                # "Ny værdi", så hvis de to er ens går vi til næste element.
                if r["Tekstværdi"] == r["Ny værdi"]:
                    continue

            if pitnavn is None:
                fire.cli.print(
                    "    * Ignorerer uanført punktinformationstype",
                    fg="red",
                    bold=False,
                )
                continue

            pit = fire.cli.firedb.hent_punktinformationtype(pitnavn)
            if pit is None:
                fire.cli.print(
                    f"    * Ignorerer ukendt punktinformationstype '{pitnavn}'",
                    fg="red",
                    bold=True,
                )
                continue

            # Nyt punktinfo-element?
            if pd.isna(r["id"]):
                # ATTR:muligt_datumstabil+slukket == ikke eksisterende i DB
                # Indsat af fire niv udtræk-revision

                if pitnavn == "ATTR:muligt_datumstabil" and r["Sluk"]:
                    continue

                fire.cli.print(f"    Opretter nyt punktinfo-element: {pitnavn}")
                if pit.anvendelse == PunktInformationTypeAnvendelse.FLAG:
                    if r["Ny værdi"]:
                        fire.cli.print(
                            f"    BEMÆRK: {pitnavn} er et flag. Ny værdi '{r['Ny værdi']}' ignoreres",
                            fg="yellow",
                            bold=True,
                        )
                    pi = PunktInformation(infotype=pit, punkt=punkt)
                elif pit.anvendelse == PunktInformationTypeAnvendelse.TEKST:
                    # Excel *kan* finde på at proppe "_x000D_" ind i stedet for \r,
                    # her rydder vi op for at undgå vrøvl i databasen.
                    tekst = r["Ny værdi"].replace("_x000D_", "").strip()

                    # Ingen definitiv test her: Tom tekst kan være gyldig.
                    # Men vi sørger for at den ikke er None
                    if tekst is None or tekst == "":
                        fire.cli.print(
                            f"    ADVARSEL: Tom tekst anført for {pitnavn}.",
                            fg="yellow",
                            bold=True,
                        )
                        tekst = ""
                    pi = PunktInformation(infotype=pit, punkt=punkt, tekst=tekst)
                else:
                    try:
                        # Både punktum og komma er accepterede decimalseparatorer
                        tal = float(r["Ny værdi"].replace(",", "."))
                    except ValueError as ex:
                        fire.cli.print(
                            f"    FEJL: {pitnavn} forventer numerisk værdi [{ex}].",
                            fg="yellow",
                            bold=True,
                        )
                        tal = 0
                    pi = PunktInformation(infotype=pit, punkt=punkt, tal=tal)

                til_opret.append(pi)
                punkter_med_oprettelse.add(ident)
                continue

            # Ingen ændringer? - så afslutter vi og går til næste element.
            if not sluk and r["Ny værdi"].strip() == "":
                continue

            # Herfra håndterer vi kun punktinformationer med indførte ændringer

            # Nu kan vi bruge objektid som heltal (ovenfor havde vi brug for NaN-egenskaben)
            oid = int(r["id"])
            if sluk:
                try:
                    pi = punkt.punktinformationer[infonøgler[oid]]
                except KeyError:
                    fire.cli.print(
                        f"    * Ukendt id - ignorerer element '{oid}'",
                        fg="red",
                        bold=True,
                    )
                    continue
                fire.cli.print(f"    Slukker: {pitnavn}")
                # pi._registreringtil = func.current_timestamp()
                til_sluk.append(pi)
                punkter_med_slukning.add(punkt.ident)
                continue

            fire.cli.print(f"    Retter punktinfo-element: {pitnavn}")
            if pit.anvendelse == PunktInformationTypeAnvendelse.FLAG:
                pi = PunktInformation(infotype=pit, punkt=punkt)
            elif pit.anvendelse == PunktInformationTypeAnvendelse.TEKST:
                # Fjern overflødigt whitespace og duplerede punktummer
                tekst = r["Ny værdi"]
                tekst = re.sub(r"[ \t]+", " ", tekst.strip())
                tekst = re.sub(r"[.]+", ".", tekst)
                pi = PunktInformation(infotype=pit, punkt=punkt, tekst=tekst)
            else:
                try:
                    tal = float(r["Ny værdi"])
                except ValueError as ex:
                    fire.cli.print(
                        f"    FEJL: {pitnavn} forventer numerisk værdi [{ex}].",
                        fg="yellow",
                        bold=True,
                    )
                    tal = 0
                pi = PunktInformation(infotype=pit, punkt=punkt, tal=tal)
            til_ret.append(pi)
            punkter_med_rettelse.add(punkt.ident)
            continue

    fikspunktstyper = [FikspunktsType.GI for _ in nye_punkter]
    landsnumre = fire.cli.firedb.tilknyt_landsnumre(nye_punkter, fikspunktstyper)
    til_opret.extend(landsnumre)
    for p in nye_punkter:
        punkter_med_oprettelse.add(p.ident)

    if len(til_opret) > 0 or len(til_ret) > 0:
        sagsevent = sag.ny_sagsevent(
            beskrivelse="Opdatering af punktinformationer",
            punktinformationer=[*til_opret, *til_ret],
        )
        fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)
        sagsgang = opdater_sagsgang(sagsgang, sagsevent, sagsbehandler)
        flush()

    if len(til_sluk) > 0:
        sagsevent = sag.ny_sagsevent(
            beskrivelse="Lukning af punktinformationer",
            punktinformationer_slettede=til_sluk,
        )
        fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)
        sagsgang = opdater_sagsgang(sagsgang, sagsevent, sagsbehandler)
        flush()

    opret_tekst = f"- oprette {len(til_opret)} attributter fordelt på {len(punkter_med_oprettelse)} punkter"
    sluk_tekst = f"- slukke for {len(til_sluk)} attributter fordelt på {len(punkter_med_slukning)} punkter"
    ret_tekst = f"- rette {len(til_ret)} attributter fordelt på {len(punkter_med_rettelse)} punkter"
    lok_tekst = f"- rette {len(nye_lokationer)} lokationskoordinater"

    fire.cli.print("")
    fire.cli.print("-" * 50)
    fire.cli.print("Punkter færdigbehandlet, klar til at")
    fire.cli.print(opret_tekst)
    fire.cli.print(sluk_tekst)
    fire.cli.print(ret_tekst)
    fire.cli.print(lok_tekst)

    spørgsmål = click.style(
        f"Er du sikker på du vil indsætte ovenstående i {fire.cli.firedb.db}-databasen",
        fg="white",
        bg="red",
    )
    if bekræft(spørgsmål):
        fire.cli.firedb.session.commit()
        skriv_ark(projektnavn, {"Sagsgang": sagsgang})
    else:
        fire.cli.firedb.session.rollback()


def flush():
    """Indlæs data i database"""
    try:
        fire.cli.firedb.session.flush()
    except DatabaseError as ex:
        fire.cli.print("FEJL! Mulig årsag:", fg="red", bold=True)
        fire.cli.print(f"{ex}", fg="red")
        fire.cli.firedb.session.rollback()
        raise SystemExit(1)


def opdater_sagsgang(sagsgang, sagsevent, sagsbehandler):
    """Opdater sagsgang med data fra sagsevent"""
    hændelsestype = {
        EventType.KOORDINAT_BEREGNET: "Koordinatoprettelse",
        EventType.PUNKTINFO_TILFOEJET: "Punktinformation tilføjet",
        EventType.PUNKTINFO_FJERNET: "Punktinformation fjernet",
        EventType.PUNKT_OPRETTET: "Punktoprettelse",
    }
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": hændelsestype[sagsevent.eventtype],
        "Tekst": sagsevent.beskrivelse,
        "uuid": sagsevent.id,
    }
    sagsgang = frame.append(sagsgang, sagsgangslinje)

    return sagsgang


def læs_lokation(lokation: str) -> GeometriObjekt:
    """Skab GeometriObjekt ud fra en brugerangivet lokationskoordinat"""

    lok = lokation.split()
    assert len(lok) in (
        2,
        4,
    ), f"Lokation '{lokation}' matcher ikke format: 55.443322 [N] 12.345678 [Ø]."
    if len(lok) == 2:
        lok = [lok[0], "", lok[1], ""]
    try:
        e = float(lok[2].replace(",", "."))
        n = float(lok[0].replace(",", "."))
    except ValueError as ex:
        fire.cli.print(f"Ikke-numerisk lokationskoordinat anført: {lokation} ({ex})")
        raise SystemExit(1)

    # Håndter verdenshjørner Nn/ØøEe/VvWw/Ss
    if lok[3].upper() in ("S", "N"):
        lok = [lok[2], lok[3], lok[0], lok[1]]
    if lok[1].upper() == "S":
        n = -n
    if lok[3].upper() in ("W", "V"):
        e = -e

    # Håndter UTM zone 32 og geografiske koordinater ensartet
    e, n = normaliser_lokationskoordinat(e, n)

    go = GeometriObjekt()
    go.geometri = Point([e, n])
    return go


def opret_punkt(lokation: str) -> Punkt:
    """Opret nyt punkt i databasen, ud fra minimumsinformationsmængder."""

    p = Punkt(id=uuid())
    go = læs_lokation(lokation)
    p.geometriobjekter.append(go)

    return p
