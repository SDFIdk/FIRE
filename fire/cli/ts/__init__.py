import click
import matplotlib.pyplot as plt
from sqlalchemy.exc import NoResultFound

import fire.cli


def plot_gnss_ts(ts):
    # Plot
    plt.figure()
    plt.suptitle(ts.punkt.ident)

    plt.subplot(311)
    plt.plot(ts.t, ts.n, ".-")
    plt.grid()
    plt.ylabel("North [mm]")

    plt.subplot(312)
    plt.plot(ts.t, ts.e, ".-")
    plt.grid()
    plt.ylabel("East [mm]")

    plt.subplot(313)
    plt.plot(ts.t, ts.u, ".-")
    plt.ylabel("Up [mm]")
    plt.grid()
    plt.xlabel("Date")

    plt.show()


@click.group()
def ts():
    """
    Håndtering af skitser og fotos af fikspunkter.
    """
    pass


@ts.command()
@click.argument("punkt")
@click.argument("id", required=False, type=int, default=-1)
@fire.cli.default_options()
def gnss(punkt: str, id: int, **kwargs) -> None:
    db = fire.cli.firedb

    try:
        p = db.hent_punkt(punkt)
    except NoResultFound as ex:
        fire.cli.print(ex)
        raise SystemExit

    if id < 0:
        for i, ts in enumerate(p.tidsserier):
            fire.cli.print(f"{i:3}: {ts.referenceramme}, {ts.srid.name}")
        raise SystemExit(0)

    if id >= len(p.tidsserier):
        fire.cli.print(f"Tidsserie med id {id} ikke fundet for {punkt}")
        raise SystemExit

    # Find tidsserie
    ts = p.tidsserier[id]
    plot_gnss_ts(ts)


@ts.command()
@click.argument("navn", required=False, type=str)
@fire.cli.default_options()
def gnss_navn(navn: str, **kwargs) -> None:
    """Mock-up af søgning i navngivne tidsserier."""
    dummy_navne = {
        "RDIO_5D_IGb08": ("RDIO", 0),
        "RDO1_5D_IGS14": ("RDO1", 0),
    }

    if navn not in dummy_navne.keys():
        for navn in dummy_navne:
            print(navn)
        raise SystemExit(0)

    db = fire.cli.firedb

    ident, id = dummy_navne[navn]
    punkt = db.hent_punkt(ident)
    ts = punkt.tidsserier[id]

    plot_gnss_ts(ts)


def plot_niv(jessenpunkt, tidsserier):

    plt.figure()
    plt.suptitle(jessenpunkt.ident)

    for ts in tidsserier:
        plt.plot(ts.t, ts.Z, ".-", label=ts.punkt.ident)
        plt.grid()
        plt.ylabel("Kote")

    plt.xlabel("Tidspunkt")
    plt.legend()
    plt.show()


@ts.command()
@click.argument("punkt", type=str)
@click.argument("id", required=False, type=int, default=-1)
@fire.cli.default_options()
def jessenpunkt(punkt: str, id: int, **kwargs) -> None:
    """Find nivellementstidsserie ud fra på Jessenpunktet"""
    db = fire.cli.firedb

    try:
        p = db.hent_punkt(punkt)
    except NoResultFound as ex:
        fire.cli.print(ex)
        raise SystemExit

    if not p.punktgrupper:
        fire.cli.print(f"Ingen punktgrupper tilknyttet {p.ident}")
        raise SystemExit

    if id < 0:
        for i, pg in enumerate(p.punktgrupper):
            fire.cli.print(f"{i:3}: {pg.navn}, {len(pg.punkter)}")
        raise SystemExit(0)

    plot_niv(p, p.punktgrupper[id].tidsserier)
