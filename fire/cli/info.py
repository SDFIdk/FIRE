import datetime
import itertools
import math
import re
import sys
from typing import Dict, List, Set, Tuple, IO

import click
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_

import pprint

from pyproj import CRS

import fire.cli
from fire.cli import firedb
from fire.api.model import (
    Punkt,
    PunktInformation,
    PunktInformationType,
    Srid,
    Koordinat,
    Observation,
)


@click.group()
def info():
    """
    Information om objekter i FIRE
    """
    pass


# INSERT INTO observationtype (
#     beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt,
#     value1, value2, value3, value4, value5, value6, value7
# )
# VALUES (
#     'Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt geometrisk ',
#      1,
#     'geometrisk_koteforskel',
#     'true',
#
#     'Koteforskel [m]',
#     'Nivellementslængde [m]',
#     'Antal opstillinger',
#     'Variabel vedr. eta_1 (refraktion) [m^3]',
#     'Afstandsafhængig varians koteforskel pr. målt koteforskel [m^2/m]',
#     'Afstandsuafhængig varians koteforskel pr. målt koteforskel [m^2]',
#     'Præcisionsnivellement [0,1,2,3]',
# );
#
# INSERT INTO observationtype (
#     beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt,
#     value1, value2, value3, value4, value5
# )
# VALUES (
#     'Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt trigonometrisk',
#      2,
#     'trigonometrisk_koteforskel',
#     'true',
#
#     'Koteforskel [m]',
#     'Nivellementslængde [m]',
#     'Antal opstillinger',
#     'Afstandsafhængig varians pr. målt koteforskel [m^2/m^2]',
#     'Afstandsuafhængig varians pr. målt koteforskel [m^2]',
# );

# TIL:
# [
#  '_decl_class_registry',
#  '_registreringfra',
#  '_registreringtil',
#  '_sa_class_manager',
#  '_sa_instance_state',
#  'antal',
#  'beregninger',
#  'gruppe',
#  'metadata',
#  'objectid',
#  'observationstidspunkt',
#  'observationstype',
#  'observationstypeid',
#  'opstillingspunkt',
#  'opstillingspunktid',
#  'registreringfra',
#  'registreringtil',
#  'sagsevent',
#  'sagseventfraid',
#  'sagseventtilid',
#  'sigtepunkt',
#  'sigtepunktid',
#  'slettet',
#  'value1',
#  'value10',
#  'value11',
#  'value12',
#  'value13',
#  'value14',
#  'value15',
#  'value2',
#  'value3',
#  'value4',
#  'value5',
#  'value6',
#  'value7',
#  'value8',
#  'value9']
#
# Observation(
#     antal=1, gruppe=71441, objectid=10342, observationstidspunkt=datetime.datetime(2003, 6, 25, 16, 7),
#     observationstypeid=1,
#     opstillingspunktid='61c61847-ed54-4969-b94e-df74fd63f108',
#     sagseventfraid='A3B4DD6C-9D06-054B-E053-D380220A57E2', sagseventtilid=None,
#     sigtepunktid='67e3987a-dc6b-49ee-8857-417ef35777af',
#     value1=2.73728, value10=None, value11=None, value12=None, value13=None, value14=None, value15=None,
#     value2=27.0, value3=2.0, value4=0.0, value5=6.075e-08, value6=1e-10, value7=0.0, value8=None, value9=None
# )


# Observation(
#     antal=1, gruppe=71327, objectid=10331, observationstidspunkt=datetime.datetime(1997, 5, 23, 18, 2),
#     observationstypeid=1, opstillingspunktid='61c61847-ed54-4969-b94e-df74fd63f108',
#     sagseventfraid='A3B4DD6C-8CE5-054B-E053-D380220A57E2', sagseventtilid=None,
#     sigtepunktid='807c78a4-17e4-4f82-93f2-2e0a7b891fb3',
#     value1=2.2897, value2=29.1, value3=-31072.0, value4=0.0,
#     value5=2.9100000000000002e-08, value6=1e-10, value7=0.0
# )
#
# Observation(
#     antal=1, gruppe=71327, objectid=11129, observationstidspunkt=datetime.datetime(1997, 5, 23, 18, 4),
#     observationstypeid=1, opstillingspunktid='807c78a4-17e4-4f82-93f2-2e0a7b891fb3',
#     sagseventfraid='A3B4DD6C-8CE5-054B-E053-D380220A57E2', sagseventtilid=None,
#     sigtepunktid='61c61847-ed54-4969-b94e-df74fd63f108',
#     value1=-2.2898, value2=28.0, value3=-31072.0, value4=0.0,
#     value5=2.8000000000000003e-08, value6=1e-10, value7=0.0
# )


#  fire info punkt -O K-63-09007

# --- OBSERVATIONER ---
#   Antal observationer til:  4
#     G 0 1997-07-15 12:00:00    +1.125000 100.0 10    K-63-09004   K-63-09007      1.581139 0.001000 +000.00
#     G 0 1997-05-23 18:02:00    +2.289700 029.1 -31072    G.M.901      K-63-09007      0.170587 0.000000 +000.00
#     G 0 1997-02-19 12:00:00    +0.441000 100.0 10    K-63-09010   K-63-09007      1.581139 0.001000 +000.00
#     G 3 1988-04-15 11:18:00    +2.288820 029.9 1    G.M.901      K-63-09007      0.103750 0.000000 +511.00
#
#   Antal observationer fra:  3
#     G 0 1997-05-23 18:04:00    -2.289800 028.0 -31072    K-63-09007   G.M.901         0.167332 0.000000 +000.00
#     G 0 1997-02-19 12:00:00    -0.421000 030.0 10    K-63-09007   K-63-09271      0.866025 0.001000 +000.00
#     G 3 1988-04-15 11:23:00    -2.289070 030.0 1    K-63-09007   G.M.901         0.103923 0.000000 -515.00
#
#   Ældste observation:  1988-04-15 11:18:00
#   Nyeste observation:  1997-07-15 12:00:00


# Cache de relevante punktinformationstyper for kanonisk_ident,
# så de ikke skal slås op ved hvert kald af funktionen
pit_landsnr = firedb.hent_punktinformationtype("IDENT:landsnr")
pit_gnssnavn = firedb.hent_punktinformationtype("IDENT:GNSS")
pit_gi_gs_gm = firedb.hent_punktinformationtype("IDENT:diverse")


def kanonisk_ident(uuid: str) -> str:
    """
    Omsæt et punkt.id (uuid) til det geodætisk mest læsbare:
    I nævnte rækkefølge: Klassisk GM-, GI- eller GS-nummer,
    GNSS-navn, eller landsnummer.

    Hvis et punkt hverken har et klassisk nummer eller et GNSS-navn,
    så returneres landsnummeret. Hvis det end ikke har et landsnummer
    så returneres uuiden uforandret.
    """
    try:
        identer = (
            firedb.session.query(PunktInformation)
            .filter(
                PunktInformation.punktid == uuid,
                or_(
                    PunktInformation.infotypeid == pit_landsnr.infotypeid,
                    PunktInformation.infotypeid == pit_gnssnavn.infotypeid,
                    PunktInformation.infotypeid == pit_gi_gs_gm.infotypeid,
                ),
            )
            .all()
        )
        if len(identer) == 0:
            return uuid

        for ident in identer:
            if ident.tekst.startswith("G.M."):
                return ident.tekst
        for ident in identer:
            if ident.tekst.startswith("G.I."):
                return ident.tekst
        for ident in identer:
            if ident.tekst.startswith("G.S."):
                return ident.tekst
        for ident in identer:
            if ident.infotypeid == pit_gnssnavn.infotypeid:
                return ident.tekst
        for ident in identer:
            if ident.infotypeid == pit_landsnr.infotypeid:
                return ident.tekst

    except NoResultFound:
        return uuid


def punktinforapport(punktinformationer: List[PunktInformation]) -> None:
    """
    Hjælpefunktion for 'punkt_fuld_rapport'.
    """
    for info in punktinformationer:
        if info.registreringtil is not None:
            continue
        tekst = info.tekst or ""
        # efter mellemrum rykkes teksten ind på linje med resten af
        # attributteksten
        tekst = tekst.replace("\n", "\n" + " " * 30).replace("\r", "").rstrip(" \n")
        tal = info.tal or ""
        fire.cli.print(f"  {info.infotype.name:27} {tekst}{tal}")


def observation_linje(obs: Observation) -> str:
    if obs.observationstypeid > 2:
        return ""

    if obs.slettet:
        return ""

    fra = kanonisk_ident(obs.opstillingspunktid)
    til = kanonisk_ident(obs.sigtepunktid)
    dH = obs.value1
    L = max(obs.value2, 0.001)  # undgå division med 0 nedenfor
    N = int(obs.value3)
    tid = obs.observationstidspunkt.strftime("%Y-%m-%d %H:%M")
    grp = obs.gruppe
    oid = obs.objectid

    # Geometrisk nivellement
    if obs.observationstypeid == 1:
        præs = int(obs.value7)
        eta_1 = obs.value4
        fejlfaktor = math.sqrt(obs.value5) * 1000 / math.sqrt(L / 1000.0)
        fejlfaktor = math.sqrt(obs.value5 * 1000 / L) * 1000
        centrering = math.sqrt(obs.value6) * 1000
        return f"G {præs} {tid}    {dH:+09.6f}  {L:05.1f} {N:2}    {fra:12} {til:12}    {fejlfaktor:3.1f} {centrering:4.2f} {eta_1:+07.2f} {grp:6} {oid:6}"

    # Trigonometrisk nivellement
    if obs.observationstypeid == 2:
        fejlfaktor = obs.value4
        fejlfaktor = math.sqrt(obs.value4 * 1000 / L) * 1000
        centrering = math.sqrt(obs.value5) * 1000
        return f"T 0 {tid}    {dH:+09.6f}  {L:05.1f} {N:2}    {fra:12} {til:12}    {fejlfaktor:3.1f} {centrering:4.2f}    0.00 {grp:6} {oid:6}"


def koordinat_linje(koord: Koordinat) -> str:
    """
    Konstruer koordinatoutput i overensstemmelse med koordinatens dimensionalitet,
    enhed og proveniens.
    """
    native_or_transformed = "t"
    if koord.transformeret == "false":
        native_or_transformed = "n"

    meta = f"{koord.t.strftime('%Y-%m-%d %H:%M')}  {koord.srid.name:<15.15} {native_or_transformed} "

    # Se i proj.db: Er koordinatsystemet lineært eller vinkelbaseret?
    try:
        grader = False
        if CRS(koord.srid.name).axis_info[0].unit_name in ("degree", "radian"):
            grader = True
    except:
        # ignorer pyproj.exceptions.CRSError: Antag at ukendte koordinatsystemers enheder
        # er lineære, bortset fra specialtilfældet NAD83G
        if koord.srid.name == "GL:NAD83G":
            grader = True

    dimensioner = 0
    if koord.x is not None and koord.y is not None:
        dimensioner = 2

    if koord.z is not None:
        if dimensioner == 2:
            dimensioner = 3
        else:
            dimensioner = 1

    if dimensioner == 1:
        linje = meta + f"{koord.z:.5f} ({koord.sz:.0f})"

    if dimensioner == 2:
        if grader:
            linje = (
                meta
                + f"{koord.x:.10f}, {koord.y:.10f} ({koord.sx:.0f}, {koord.sy:.0f})"
            )
        else:
            linje = (
                meta + f"{koord.x:.4f}, {koord.y:.4f} ({koord.sx:.0f}, {koord.sy:.0f})"
            )

    if dimensioner == 3:
        linje = meta + f"{koord.x:.10f}, {koord.y:.10f}, {koord.z:.5f}"
        linje += f"  ({koord.sx:.0f}, {koord.sy:.0f}, {koord.sz:.0f})"

    return linje


def punktinforapport(punktinformationer: List[PunktInformation]) -> None:
    """
    Hjælpefunktion for 'punkt_fuld_rapport'.
    """
    for info in punktinformationer:
        if info.registreringtil is not None:
            continue
        tekst = info.tekst or ""
        # efter mellemrum rykkes teksten ind på linje med resten af
        # attributteksten
        tekst = tekst.replace("\n", "\n" + " " * 30).replace("\r", "").rstrip(" \n")
        tal = info.tal or ""
        fire.cli.print(f"  {info.infotype.name:27} {tekst}{tal}")


def koordinatrapport(koordinater: List[Koordinat], options: str) -> None:
    """
    Hjælpefunktion for 'punkt_fuld_rapport': Udskriv formateret koordinatliste
    """
    koordinater.sort(
        key=lambda x: (x.srid.name, x.t.strftime("%Y-%m-%dT%H:%M")), reverse=True
    )
    ts = True if "ts" in options.split(",") else False
    alle = True if "alle" in options.split(",") else False
    for koord in koordinater:
        tskoord = koord.srid.name.startswith("TS:")
        if tskoord and not ts:
            continue
        if koord.registreringtil is not None:
            if alle or (ts and tskoord):
                fire.cli.print(". " + koordinat_linje(koord), fg="red")
        else:
            fire.cli.print("* " + koordinat_linje(koord), fg="green")
    fire.cli.print("")


def observationsrapport(
    observationer_til: List[Observation],
    observationer_fra: List[Observation],
    options: str,
    opt_detaljeret: bool,
) -> None:
    """
    Hjælpefunktion for 'punkt_fuld_rapport': Udskriv formateret observationsliste
    """
    # p.t. er kun nivellementsobservationer understøttet
    if options not in ["niv", "alle"]:
        return

    n_obs_til = len(observationer_til)
    n_obs_fra = len(observationer_fra)
    if n_obs_til + n_obs_fra == 0:
        return

    if n_obs_til > 0:
        punktid = observationer_til[0].sigtepunktid
    else:
        punktid = observationer_fra[0].opstillingspunktid

    observationer = [
        obs
        for obs in observationer_fra + observationer_til
        if obs.observationstypeid in [1, 2]
    ]
    # Behjertet forsøg på at sortere de udvalgte observationer,
    # så de giver bedst mulig mening for brugeren: Først præs,
    # så andre, og indenfor hver gruppe baglæns kronologisk og med
    # frem/tilbage par så vidt muligt grupperet. Det er ikke nemt!
    observationer.sort(
        key=lambda x: (
            (x.value7 if x.observationstypeid == 1 else 0),
            (x.observationstidspunkt.year),
            (x.gruppe),
            (x.sigtepunktid if x.sigtepunktid != punktid else x.opstillingspunktid),
            (x.observationstidspunkt),
        ),
        reverse=True,
    )

    n_vist = len(observationer)
    if n_vist == 0:
        return

    fire.cli.print(
        "    [Trig/Geom][Præs][T]     dH        L      N    Fra          Til             ne  d     eta    grp    id"
    )
    fire.cli.print("  " + 110 * "-")
    for obs in observationer:
        linje = observation_linje(obs)
        if linje != "" and linje is not None:
            fire.cli.print("    " + observation_linje(obs))
    fire.cli.print("  " + 110 * "-")

    if not opt_detaljeret:
        return

    fire.cli.print(f"  Observationer ialt:  {n_obs_til + n_obs_fra}")
    fire.cli.print(f"  Observationer vist:  {n_vist}")

    # Find ældste og yngste observation
    min_obs = datetime.datetime(9999, 12, 31, 0, 0, 0)
    max_obs = datetime.datetime(1, 1, 1, 0, 0, 0)
    for obs in itertools.chain(observationer_fra, observationer_til):
        if obs.observationstidspunkt < min_obs:
            min_obs = obs.observationstidspunkt
        if obs.observationstidspunkt > max_obs:
            max_obs = obs.observationstidspunkt

    fire.cli.print(f"  Ældste observation:  {min_obs}")
    fire.cli.print(f"  Nyeste observation:  {max_obs}")
    fire.cli.print("  " + 110 * "-")


def punkt_fuld_rapport(
    punkt: Punkt,
    ident: str,
    i: int,
    n: int,
    opt_obs: str,
    opt_koord: str,
    opt_detaljeret: bool,
) -> None:
    """
    Rapportgenerator for funktionen 'punkt' nedenfor.
    """

    kanonisk = kanonisk_ident(punkt.id)

    # Header
    fire.cli.print("")
    fire.cli.print("-" * 80)
    if n > 1:
        fire.cli.print(f" PUNKT {kanonisk} ({i}/{n})", bold=True)
    else:
        fire.cli.print(f" PUNKT {kanonisk}", bold=True)
    fire.cli.print("-" * 80)

    # Geometri, fire-id, oprettelsesdato og PunktInformation håndteres
    # under et, da det giver et bedre indledende overblik
    for geometriobjekt in punkt.geometriobjekter:
        fire.cli.print(f"  Lokation                    {geometriobjekt.geometri}")
    fire.cli.print(f"  Oprettelsesdato             {punkt.registreringfra}")

    punktinforapport(punkt.punktinformationer)

    if opt_detaljeret:
        fire.cli.print(f"  uuid                        {punkt.id}")
        fire.cli.print(f"  objekt-id                   {punkt.objectid}")
        fire.cli.print(f"  sagsid                      {punkt.sagsevent.sagid}")
        fire.cli.print(f"  sagsevent-fra               {punkt.sagseventfraid}")
        if punkt.sagseventtilid is not None:
            fire.cli.print(f"  sagsevent-til               {punkt.sagseventtilid}")

    # Koordinater og observationer klares af specialiserede hjælpefunktioner
    if "ingen" not in opt_koord.split(","):
        fire.cli.print("")
        fire.cli.print("--- KOORDINATER ---", bold=True)
        koordinatrapport(punkt.koordinater, opt_koord)

    if opt_obs != "":
        fire.cli.print("")
        fire.cli.print("--- OBSERVATIONER ---", bold=True)
        observationsrapport(
            punkt.observationer_til, punkt.observationer_fra, opt_obs, opt_detaljeret
        )
        fire.cli.print("")


@info.command()
@click.option(
    "-K",
    "--koord",
    default="",
    help="ts: Udskriv også tidsserier; alle: Udskriv også historiske koordinater; ingen: Udelad alle",
)
@click.option(
    "-O", "--obs", is_flag=False, default="", help="niv/alle: Udskriv observationer",
)
@click.option(
    "-D",
    "--detaljeret",
    is_flag=True,
    default=False,
    help="Udskriv også sjældent anvendte elementer",
)
@fire.cli.default_options()
@click.argument("ident")
def punkt(ident: str, obs: str, koord: str, detaljeret: bool, **kwargs) -> None:
    """
    Vis al tilgængelig information om et fikspunkt

    IDENT kan være enhver form for navn et punkt er kendt som, blandt andet
    GNSS stationsnummer, G.I./G.M.-nummer, refnr, landsnummer, uuid osv.

    Søgningen er versalfølsom.

    Punkt-klassen er omfattende og består af følgende elementer:

    Punkt = Punkt(\n
        'geometriobjekter',   -- placeringskoordinat\n
        'id',                 -- uuid: intern databaseidentifikation\n
        'koordinater',        -- alle tilgængelige koordinater\n
        'metadata',           -- øh\n
        'objectid',           -- databaserækkenummer\n
        'observationer_fra',  -- alle observationer udført fra punkt\n
        'observationer_til',  -- alle observationer udført til punkt\n
        'punktinformationer', -- attributter og punktbeskrivelser\n
        'registreringfra',    -- oprettelsesdato/registreringsdato\n
        'registreringtil',    -- invalideringstidspunkt\n
        'sagsevent',          -- ?? seneste sagsevent??\n
        'sagseventfraid',     -- sagsevent for punktoprettelsen\n
        'sagseventtilid',     -- sagsevent for punktinvalideringen\n
        'slettet'             -- øh\n
    )

    Anfører man ikke specifikke tilvalg vises kun basale dele: Attributter og
    punktbeskrivelser + gældende koordinater.

    Tilvalg `--detaljer/-D` udvider med sjældnere brugte informationer

    Tilvalg `--koord/-K` kan sættes til ts, alle, ingen - eller kombinationer:
    fx ts,alle. `alle` tilvælger historiske koordinater, `ts` tilvælger
    tidsseriekoordinater, `ingen`fravælger alle koordinatoplysninger.

    Tilvalg `--obs/-O` kan sættes til alle eller niv. Begge tilvælger visning
    af observationer til/fra det søgte punkt. P.t. understøttes kun visning af
    nivellementsobservationer.
    """
    pi = aliased(PunktInformation)
    pit = aliased(PunktInformationType)

    # Vær mindre pedantisk mht. foranstillede nuller hvis identen er et landsnummer
    landsnummermønster = re.compile("[0-9]*-[0-9]*-[0-9]*$")
    if landsnummermønster.match(ident):
        dele = ident.split("-")
        herred = int(dele[0])
        sogn = int(dele[1])
        lbnr = int(dele[2])
        ident = f"{herred}-{sogn:02}-{lbnr:05}"

    try:
        # Hvis ident er en uuid kan vi gå direkte på hegnspælen med "hent_punkt"...
        uuidmønster = re.compile("[a-f0-9]*-[a-f0-9]*-[a-f0-9]*-[a-f0-9]*-[a-f0-9]*$")
        if uuidmønster.match(ident):
            pkt = firedb.hent_punkt(ident)
            # TODO: Undersøg hvorfor det er nødvendigt at hejse flaget manuelt
            if pkt is None:
                raise NoResultFound
            punkt_fuld_rapport(pkt, ident, 1, 1, obs, koord, detaljeret)
            sys.exit(0)

        # Ellers skal vi gennem en større søgesejlads...
        pinfo = (
            firedb.session.query(pi)
            .filter(pit.name.startswith("IDENT:"), pi.tekst == ident,)
            .first()
        )

        if pinfo is not None:
            punktinfo = [pinfo]

        # ...og måske endda til at bruge mønstersøgning
        else:
            punktinfo = (
                firedb.session.query(pi)
                .filter(
                    pit.name.startswith("IDENT:"),
                    or_(
                        pi.tekst.like(f"{ident}%"),  # Herred/sognesøgning
                        pi.tekst.like(f"FO  %{ident}"),  # Færøerne
                        pi.tekst.like(f"GL  %{ident}"),  # Grønland
                    ),
                )
                .all()
            )
            if 0 == len(punktinfo):
                raise NoResultFound
    except NoResultFound:
        fire.cli.print(f"Error! {ident} not found!", fg="red", err=True)
        sys.exit(1)

    # Succesfuld søgning - vis hvad der blev fundet
    n = len(punktinfo)
    for i in range(n):
        punkt_fuld_rapport(punktinfo[i].punkt, ident, i + 1, n, obs, koord, detaljeret)


@info.command()
@fire.cli.default_options()
@click.argument("srid")
def srid(srid: str, **kwargs):
    """
    Information om et givent SRID (Spatial Reference ID)

    Eksempler på SRID'er: EPSG:25832, DK:SYS34, TS:81013
    """
    srid_name = srid

    try:
        srid = firedb.hent_srid(srid_name)
    except NoResultFound:
        fire.cli.print(f"Error! {srid_name} not found!", fg="red", err=True)
        sys.exit(1)

    fire.cli.print("--- SRID ---", bold=True)
    fire.cli.print(f" Name:       :  {srid.name}")
    fire.cli.print(f" Description :  {srid.beskrivelse}")


@info.command()
@fire.cli.default_options()
@click.argument("infotype")
def infotype(infotype: str, **kwargs):
    """
    Information om en punktinfotype.

    Eksempler på punktinfotyper: IDENT:GNSS, AFM:diverse, ATTR:beskrivelse
    """
    try:
        pit = firedb.hent_punktinformationtype(infotype)
        if pit is None:
            raise NoResultFound
    except NoResultFound:
        fire.cli.print(f"Error! {infotype} not found!", fg="red", err=True)
        sys.exit(1)

    fire.cli.print("--- PUNKTINFOTYPE ---", bold=True)
    fire.cli.print(f"  Name        :  {pit.name}")
    fire.cli.print(f"  Description :  {pit.beskrivelse}")
    fire.cli.print(f"  Type        :  {pit.anvendelse}")
