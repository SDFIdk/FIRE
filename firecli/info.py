import datetime
import sys
import itertools

import click
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound

import firecli
from firecli import firedb
from fireapi.model import Punkt, PunktInformation, PunktInformationType, Srid


@click.group()
def info():
    """
    Information om objekter i FIRE
    """
    pass

def punkt_rapport(punkt: Punkt, ident: str, i: int, n: int) -> None:
    """
    Rapportgenerator for funktionen 'punkt' nedenfor.
    """
    firecli.print("")
    firecli.print("-"*80)
    firecli.print(f" PUNKT {ident} ({i}/{n})", bold=True)
    firecli.print("-"*80)
    firecli.print(f"  FIRE ID             :  {punkt.id}")
    firecli.print(f"  Oprettelsesdato     :  {punkt.registreringfra}")
    firecli.print("")

    firecli.print("--- PUNKTINFO ---", bold=True)
    for info in punkt.punktinformationer:
        if info.registreringtil is not None:
            continue
        tekst = info.tekst or ""
        tekst = tekst.replace("\n", "").replace("\r", "")
        tal = info.tal or ""
        firecli.print(f"  {info.infotype.name:20}:  {tekst:.80}{tal}")
    firecli.print("")

    firecli.print("--- KOORDINATER ---", bold=True)
    punkt.koordinater.sort(key=lambda x: x.srid.name, reverse=False)
    for koord in punkt.koordinater:
        line = f"{koord.t.strftime('%Y-%m-%d')}   {koord.srid.name:<15.15} {koord.x}, {koord.y}, {koord.z}"
        if koord.registreringtil is not None:
            firecli.print("     "+line, fg="red")
        else:
            firecli.print("   * "+line, fg="green")
    firecli.print("")

    firecli.print("--- OBSERVATINONER ---", bold=True)
    n_obs_til = len(punkt.observationer_til)
    n_obs_fra = len(punkt.observationer_fra)
    firecli.print(f"Antal observationer til:  {n_obs_til}")
    firecli.print(f"Antal observationer fra:  {n_obs_fra}")

    if n_obs_fra + n_obs_til > 0:
        min_obs = datetime.datetime(9999,12,31)
        max_obs = datetime.datetime(1,1,1)
        for obs in itertools.chain(punkt.observationer_til, punkt.observationer_fra):
            if obs.registreringfra < min_obs:
                min_obs = obs.registreringfra
            if obs.registreringfra > max_obs:
                max_obs = obs.registreringfra

        firecli.print(f"Ældste observation     :  {min_obs}")
        firecli.print(f"Nyeste observation     :  {max_obs}")

    firecli.print("")



@info.command()
@firecli.default_options()
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
            firedb.session.query(pi).filter(pit.name.startswith("IDENT:"), pi.tekst == ident).all()
        )
        n = len(punktinfo)
        for i in range(n):
            punkt_rapport(punktinfo[i].punkt, ident, i+1, n)
    except NoResultFound:
        try:
            punkt = firedb.hent_punkt(ident)
        except NoResultFound:
            firecli.print(f"Error! {ident} not found!", fg="red", err=True)
            sys.exit(1)
        punkt_rapport(punkt, ident, 1, 1)



@info.command()
@firecli.default_options()
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
        firecli.print(f"Error! {srid_name} not found!", fg="red", err=True)
        sys.exit(1)

    firecli.print("--- SRID ---", bold=True)
    firecli.print(f" Name:       :  {srid.name}")
    firecli.print(f" Description :  {srid.beskrivelse}")


@info.command()
@firecli.default_options()
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
        firecli.print(f"Error! {infotype} not found!", fg="red", err=True)
        sys.exit(1)

    firecli.print("--- PUNKTINFOTYPE ---", bold=True)
    firecli.print(f"  Name        :  {pit.name}")
    firecli.print(f"  Description :  {pit.beskrivelse}")
    firecli.print(f"  Type        :  {pit.anvendelse}")
