import datetime
import itertools
import math
import sys

import click
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_

import pprint

from pyproj import CRS

import fire.cli
from fire.cli import firedb
from fire.api.model import Punkt, PunktInformation, PunktInformationType, Srid


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


def kanonisk_ident(uuid):
    try:
        # TODO: Bør cache både pil, pid og resultater pr UUID, så vi kan reducere opslag
        pil = firedb.hent_punktinformationtype("IDENT:landsnr")
        pid = firedb.hent_punktinformationtype("IDENT:diverse")

        identer = (
            firedb.session.query(PunktInformation)
            .filter(
                PunktInformation.punktid == uuid,
                or_(
                    PunktInformation.infotypeid == pil.infotypeid,
                    PunktInformation.infotypeid == pid.infotypeid,
                ),
            )
            .all()
        )
        if len(identer) == 0:
            raise NoResultFound

        for ident in identer:
            if ident.tekst.startswith("G.M."):
                return ident.tekst
            if ident.tekst.startswith("G.I."):
                return ident.tekst
        return identer[0].tekst

    except NoResultFound:
        return uuid


def observation_linje(obs) -> str:
    if obs.observationstypeid > 2:
        return ""

    fra = kanonisk_ident(obs.opstillingspunktid)
    til = kanonisk_ident(obs.sigtepunktid)
    dH = obs.value1
    L = obs.value2
    N = int(obs.value3)
    tid = obs.observationstidspunkt.strftime("%Y-%m-%d %H:%M:%S")
    oid = obs.objectid

    # Geometrisk nivellement
    if obs.observationstypeid == 1:
        præs = int(obs.value7)
        eta_1 = obs.value4
        fejlfaktor = math.sqrt(obs.value5) * 1000
        centrering = obs.value6 * 1000
        return f"G {præs} {tid}    {dH:+09.6f} {L:05.1f} {N}    {fra:12} {til:12}    {fejlfaktor:.6f} {centrering:.6f} {eta_1:+07.2f} {oid}"

    # Trigonometrisk nivellement
    if obs.observationstypeid == 1:
        fejlfaktor = obs.value4
        centrering = obs.value5
        return f"T 0 {år} {dH:+09.6f} {L:05.1f} {N}    {fra:12} {til:12}    {fejlfaktor:.6f} {centrering:.6f} {oid}"


#     'Variabel vedr. eta_1 (refraktion) [m^3]',
#     'Afstandsafhængig varians koteforskel pr. målt koteforskel [m^2/m]',
#     'Afstandsuafhængig varians koteforskel pr. målt koteforskel [m^2]',


def koordinat_linje(koord):
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


def punkt_rapport(
    punkt: Punkt, ident: str, i: int, n: int, udskriv_observationer: bool = False
) -> None:
    """
    Rapportgenerator for funktionen 'punkt' nedenfor.
    """
    fire.cli.print("")
    fire.cli.print("-" * 80)
    fire.cli.print(f" PUNKT {ident} ({i}/{n})", bold=True)
    fire.cli.print("-" * 80)
    fire.cli.print(f"  FIRE ID             :  {punkt.id}")
    fire.cli.print(f"  Oprettelsesdato     :  {punkt.registreringfra}")
    fire.cli.print("")

    fire.cli.print("--- PUNKTINFO ---", bold=True)
    for info in punkt.punktinformationer:
        if info.registreringtil is not None:
            continue
        tekst = info.tekst or ""
        # efter mellemrum rykkes teksten ind på linje med resten af
        # attributteksten
        tekst = tekst.replace("\n", "\n" + " " * 25).replace("\r", "")
        tal = info.tal or ""
        fire.cli.print(f"  {info.infotype.name:20}:  {tekst}{tal}")
    fire.cli.print("")

    fire.cli.print("--- GEOMETRI ---", bold=True)
    for geometriobjekt in punkt.geometriobjekter:
        fire.cli.print(f"  {geometriobjekt.geometri}")
        fire.cli.print("")

    fire.cli.print("--- KOORDINATER ---", bold=True)
    punkt.koordinater.sort(
        key=lambda x: (x.srid.name, x.t.strftime("%Y-%m-%dT%H:%M")), reverse=True
    )
    for koord in punkt.koordinater:
        if koord.registreringtil is not None:
            fire.cli.print(". " + koordinat_linje(koord), fg="red")
        else:
            fire.cli.print("* " + koordinat_linje(koord), fg="green")
    fire.cli.print("")

    fire.cli.print("--- OBSERVATIONER ---", bold=True)
    n_obs_til = len(punkt.observationer_til)
    n_obs_fra = len(punkt.observationer_fra)

    fire.cli.print(f"  Antal observationer til:  {n_obs_til}")
    if udskriv_observationer:
        punkt.observationer_til.sort(
            key=lambda x: x.observationstidspunkt, reverse=True
        )
        for obs in punkt.observationer_til:
            linje = observation_linje(obs)
            if linje != "" and linje is not None:
                fire.cli.print("    " + observation_linje(obs))
        fire.cli.print("")

    fire.cli.print(f"  Antal observationer fra:  {n_obs_fra}")
    if udskriv_observationer:
        punkt.observationer_fra.sort(
            key=lambda x: x.observationstidspunkt, reverse=True
        )
        for obs in punkt.observationer_fra:
            linje = observation_linje(obs)
            if linje != "" and linje is not None:
                fire.cli.print("    " + observation_linje(obs))
        fire.cli.print("")

    if n_obs_fra + n_obs_til > 0:
        min_obs = datetime.datetime(9999, 12, 31, 0, 0, 0)
        max_obs = datetime.datetime(1, 1, 1, 0, 0, 0)
        for obs in itertools.chain(punkt.observationer_fra, punkt.observationer_til):
            if obs.observationstidspunkt < min_obs:
                min_obs = obs.observationstidspunkt
            if obs.observationstidspunkt > max_obs:
                max_obs = obs.observationstidspunkt

        fire.cli.print(f"  Ældste observation:  {min_obs}")
        fire.cli.print(f"  Nyeste observation:  {max_obs}")
    #        print("FRA:")
    #        pprint.pprint(dir(punkt.observationer_fra[0]))
    #        pprint.pprint(punkt.observationer_fra[0])
    #        print("TIL:")
    #        pprint.pprint(dir(punkt.observationer_til[0]))
    #        pprint.pprint(punkt.observationer_til[0])

    fire.cli.print("")


@info.command()
@click.option(
    "-O", "--obs", is_flag=True, default=False, help="Udskriv observationer",
)
@fire.cli.default_options()
@click.argument("ident")
def punkt(ident: str, obs: bool, **kwargs) -> None:
    """
    Vis al tilgængelig information om et fikspunkt

    IDENT kan være enhver form for navn et punkt er kendt som, blandt andet
    GNSS stationsnummer, G.I.-nummer, refnr, landsnummer osv.

    Søgningen er versalfølsom.
    """
    pi = aliased(PunktInformation)
    pit = aliased(PunktInformationType)

    try:
        punktinfo = (
            firedb.session.query(pi)
            .filter(
                pit.name.startswith("IDENT:"),
                or_(
                    pi.tekst == ident,
                    pi.tekst.like(f"FO  %{ident}"),
                    pi.tekst.like(f"GL  %{ident}"),
                ),
            )
            .all()
        )
        n = len(punktinfo)
        if n == 0:
            raise NoResultFound

        for i in range(n):
            punkt_rapport(punktinfo[i].punkt, ident, i + 1, n, obs)

    except NoResultFound:
        try:
            punkt = firedb.hent_punkt(ident)
        except NoResultFound:
            fire.cli.print(f"Error! {ident} not found!", fg="red", err=True)
            sys.exit(1)
        punkt_rapport(punkt, ident, 1, 1, obs)


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
