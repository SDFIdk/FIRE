import datetime
import sys
import itertools

import click
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_

from pyproj import CRS

import fire.cli
from fire.cli import firedb
from fire.api.model import (
    Punkt,
    PunktInformation,
    PunktInformationType,
    Srid,
    Koordinat,
)


@click.group()
def info():
    """
    Information om objekter i FIRE
    """
    pass


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


def punkt_rapport(punkt: Punkt, ident: str, i: int, n: int) -> None:
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
    fire.cli.print(f"  Antal observationer fra:  {n_obs_fra}")

    if n_obs_fra + n_obs_til > 0:
        min_obs = datetime.datetime(9999, 12, 31)
        max_obs = datetime.datetime(1, 1, 1)
        for obs in itertools.chain(punkt.observationer_til, punkt.observationer_fra):
            if obs.registreringfra < min_obs:
                min_obs = obs.registreringfra
            if obs.registreringfra > max_obs:
                max_obs = obs.registreringfra

        fire.cli.print(f"  Ældste observation     :  {min_obs}")
        fire.cli.print(f"  Nyeste observation     :  {max_obs}")

    fire.cli.print("")


@info.command()
@fire.cli.default_options()
@click.argument("ident")
def punkt(ident: str, **kwargs) -> None:
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
            punkt_rapport(punktinfo[i].punkt, ident, i + 1, n)
    except NoResultFound:
        try:
            punkt = firedb.hent_punkt(ident)
        except NoResultFound:
            fire.cli.print(f"Error! {ident} not found!", fg="red", err=True)
            sys.exit(1)
        punkt_rapport(punkt, ident, 1, 1)


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
