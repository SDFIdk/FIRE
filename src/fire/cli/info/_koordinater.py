import click
from pyproj import CRS, Transformer
from pyproj.exceptions import ProjError
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire.cli.info import info
from fire.api.model import Punkt, Srid
from fire.api.model.tidsserier import GNSSTidsserie
from fire.cli.ts import (
    _print_tidsserier,
)
from fire.cli.ts.plot_ts import (
    plot_data,
    plot_tidsserie,
)
from fire.ident import klargør_identer_til_søgning, bestem_identtype


@info.command()
@click.option(
    "-s",
    "--source",
    "sources",
    type=str,
    default="DVR90",
    callback=lambda ctx, param, val: [s.strip() for s in val.split(",")],
    help="Vælg koordinat-type der skal udtrækkes. Vælg flere srider, ved at angive dem som en kommasepareret liste.",
)
@click.option(
    "-t",
    "--target",
    type=str,
    default="",
    help="Vælg koordinatsystem der skal transformeres til.",
)
@click.option(
    "-H",
    "--historik",
    is_flag=True,
    default=False,
    help="Udskriv også ikke-gældende (historiske) elementer",
)
@click.option(
    "-P",
    "--plot",
    is_flag=True,
    default=False,
    help="Plot koordinater som tidsserie. Hvis denne er sat, skal ``--historik/-H`` også være sat.",
)
@click.option(
    "-f",
    "--fil",
    required=False,
    type=click.Path(),
    help="Skriv den udtrukne tidsserie til Excel fil.",
)
@click.argument(
    "objekter",
    required=True,
    type=str,
    nargs=-1,
)
@fire.cli.default_options()
def koordinater(
    objekter: list[str],
    sources: list[str],
    target: str,
    historik: bool,
    plot: bool,
    fil: click.Path,
    **kwargs,
) -> None:
    """
    Udtræk koordinater for ét eller flere punkter

    Med **OBJEKTER** angives en liste af punkter eller fikspunktsnet som skal udtrækkes.
    Vælg fx. NET:5D, NET:DMI, eller NET:RTKCONNECT for at udtrække koordinater til hhv.
    5D-punkter, DMIs vandstandsmålere eller RTKConnects referencestationer. Se en fuld
    liste over nettene med ``fire info infotype NET``.

    Som standard udtrækkes den gældende DVR90-kote for hvert af de valgte punkter.

    Med parameteren ``--source/-s`` kan angives en alternativ koordinat-type som skal
    udtrækkes. Der kan vælges alle srid'er som findes i FIRE, se en liste med ``fire info
    srid``. Dog kan der ikke vælges tidsserie-koordinattyper. Hertil skal anvendes ``fire
    ts hts`` og ``fire ts gnss``.

    Parameteren ``--target/-t`` bruges til at angive referencerammen som de udtrukne
    koordinater skal transformeres til og vises i. Den valgte referenceramme skal kunne
    fortolkes af PROJ.

    Der kan vælges flere ``--source`` koordinatsystemer ved at angive dem som en
    kommasepareret liste. De vil da alle blive transformeret til det valgte ``--target``
    koordinatsystem. I tilfælde af man ikke har valgt noget ``--target``, så sættes target
    til det sidst angivne ``source``-system.

    Programmet gør opmærksom på, hvis transformationerne er af typerne "noop" (no
    operation) eller "ballpark". Begge typer angiver, at der reelt ikke foretages en
    transformation, og at de resulterende koordinater derfor ikke er nøjagtige.

    Med parameteren ``--historik/-H`` tilvælges historiske koordinater. Dette er fravalgt
    som standard, så der derved kun udtrækkes gældende koordinater.

    Hvis historik er tilvalgt, kan man med ``--plot/-P`` desuden få vist de resulterende
    tidsserier i et simpelt plot. Ønskes mere avancerede plots og anden analyse, kan
    resultaterne gemmes som excel-fil ved at angive et outputfilnavn med ``--fil/-f``.


    \b **EKSEMPLER**

    Vis gældende DVR90-kote for ALBN, BFYR og CHAK::

        fire info koordinater ALBN BFYR CHAK

    Vis historiske DVR90-koter for ALBN, BFYR og CHAK::

        fire info koordinater ALBN BFYR CHAK -H

    Vis historiske DVR90-koter for ALBN, BFYR og CHAK og gem som fil::

        fire info koordinater ALBN BFYR CHAK -H -f "ABC.xlsx"

    Vis historiske ETRS89-koordinater for ALBN, BFYR og CHAK::

        fire info koordinater ALBN BFYR CHAK -H -s EPSG:4937

    Udtræk gældende ETRS89 koordinater for alle GPSNET punkterne og vis dem i UTM32N +
    DVR90(2023)::

        fire info koordinater NET:GPSNET -s EPSG:4937 -t EPSG:25832+EPSG:10485

    Udtræk alle IGb08, IGS14 og IGS20 koordinater for 5D-punkterne, transformer til IGS20
    geografiske koordinater, og plot::

        fire info koordinater NET:5D -s IGb08,IGS14,IGS20 -t EPSG:10177 -H -P

    For mere info om hvilke transformationer som programmet foretager, kan anvendes
    `projinfo` der kaldes med de samme parametre som denne kommando::

        projinfo -s EPSG:4937 -t EPSG:25832+EPSG:10485

    """
    if not target:
        target = sources[0]
    sources, target = oversæt_srid_alias(sources, target)

    transformers = klargør_transformationer(sources, target)

    punkter_identer = håndter_punkter(list(objekter))

    tidsserier = konstruer_tidsserier(punkter_identer, transformers, historik)

    if not tidsserier:
        fire.cli.print(
            f"Fejl: Ingen af punkterne har koordinater i det valgte referencesystem.",
            fg="red",
        )
        raise SystemExit(1)

    _print_tidsserier(tidsserier, fil)

    if not (historik and plot):
        return

    # Vi plotter bare tidsseriens x,y,z værdier som de er, (medmindre de er None) da de
    # umiddelbart er de eneste vi er sikre på eksisterer.
    for ts in tidsserier:
        parms = [
            parm
            for parm, dim in zip("xyz", [ts.srid.x, ts.srid.y, ts.srid.z])
            if dim is not None
        ]
        plot_tidsserie(ts, plot_data, parametre=parms, y_enhed="m")


def håndter_punkter(objekter: list[str]) -> list[tuple[Punkt, str]]:
    """
    Omsæt `objekter` til en liste af punkter.

    `objekter` kan indeholde identer eller navne på "NET"-infotyper, fx. NET:5D.

    Hvert punkt matches med dén ident som ligger tættest på den søgestreng som punktet
    blev fundet med, hvilket kan bruges til visning i tabeller, plots etc.
    """
    nets = [
        objekter.pop(i) for i, o in enumerate(objekter) if o.upper().startswith("NET:")
    ]
    identer = objekter

    identer = klargør_identer_til_søgning(identer)
    fire.cli.print("Søg i databasen efter punkter til hver ident", fg="yellow")
    punkter: list[Punkt] = fire.cli.firedb.hent_punkt_liste(
        identer, ignorer_ukendte=False
    )

    # Ingen punkter bliver sprunget over da vi ovenfor har sat ignorer_ukendte=False
    # Vi kan derfor antage at punkter og identtyper kommer i samme rækkefølge
    identtyper = [bestem_identtype(ident) for ident in identer]
    punkter_identer = [
        (
            p,
            p._hent_ident_af_type(it) if it is not None else p.ident,
        )  # hvis identtypen ikke kunne bestemmes bruger vi bare den almindelige ident
        for p, it in zip(punkter, identtyper)
    ]

    for net in nets:
        infotype = fire.cli.firedb.hent_punktinformationtype(net)
        punkter = fire.cli.firedb.hent_punkter_med_flag(infotype)
        punkter_identer.extend([(p, p.ident) for p in punkter])

    punkter_identer = sorted(punkter_identer, key=lambda x: x[1])

    return punkter_identer


def oversæt_srid_alias(sources: list[str], target: str = None) -> tuple[list[str], str]:
    """
    Oversæt srid-alias til sridens rigtige navn

    Hvis alias (kortnavn) ikke kan oversættes, returneres inputtet som det blev givet.
    """
    srids_med_alias = (
        fire.cli.firedb.session.query(Srid).filter(Srid.kortnavn != None).all()
    )
    srids_alias_mapper = {s.kortnavn: s.name for s in srids_med_alias}

    sources = [srids_alias_mapper.get(s, s) for s in sources]
    target = srids_alias_mapper.get(target, target)

    return sources, target


def klargør_transformationer(
    sources: list[str], target: str
) -> dict[Srid, dict[Srid, Transformer]]:
    """
    Klargør transformationer fra alle sources til target

    Returnerer en dict-over-dict der mapper alle source-target kombinationer til den
    rette transformation, fx.:
    {
        src_1: {
            trg_1: transformation_11
        },
        src_2: {
            trg_1: transformation_21,
        },
    }
    """
    try:
        transformers = {
            fire.cli.firedb.hent_srid(src := source): {
                target: (trans := lav_transformer(source, target))
            }
            for source in sources
        }
    except NoResultFound:
        fire.cli.print(f"Fejl: Source-srid '{src}' ikke fundet!", fg="red")
        raise SystemExit(1)

    try:
        target_srid = fire.cli.firedb.hent_srid(target)
    except NoResultFound:
        # Konstruér en ny Srid ud fra target_crs
        target_srid = Srid_fra_CRS(trans.target_crs, navn=target)

    # Konstruér ny dict med srids som nøgler
    transformers = {
        src: {target_srid: trans for trg, trans in trg_trans.items()}
        for src, trg_trans in transformers.items()
    }
    return transformers


def lav_transformer(s_crs: str | CRS, t_crs: str | CRS) -> Transformer:
    """Opret Transformer-objekt"""
    if s_crs == t_crs:
        return Transformer.from_pipeline("+proj=noop")

    try:
        transformer = Transformer.from_crs(crs_from=s_crs, crs_to=t_crs, always_xy=True)
    except ProjError as e:
        fire.cli.print(
            f"Fejl: Kan ikke transformere fra {s_crs} til {t_crs}. Mulig årsag:",
            fg="red",
        )
        fire.cli.print(e)
        raise SystemExit(1)

    if "proj=noop" in transformer.definition:
        fire.cli.print(
            f'Bemærk: Klargjorde en "noop" transformation fra {s_crs} til {t_crs}',
            fg="yellow",
        )
    elif "ballpark" in transformer.description.lower():
        fire.cli.print(
            f'Bemærk: Klargjorde en "ballpark" transformation fra {s_crs} til {t_crs}',
            fg="yellow",
        )
    else:
        fire.cli.print(
            f"Klargjorde transformation fra {s_crs} til {t_crs}.",
        )

    return transformer

# Her fastsættes dicts til oversættelse af PROJ's interne akse- og enhedsnavne
# til nogle mere kortfattede og danske navne.
danske_akser = {
    "Easting": "Easting",
    "Northing": "Northing",
    "Westing": "Westing",
    "Southing": "Southing",
    "Geodetic latitude": "Breddegrad",
    "Geodetic longitude": "Længdegrad",
    "Geocentric X": "X",
    "Geocentric Y": "Y",
    "Geocentric Z": "Z",
    "Ellipsoidal height": "Ellipsoidehøjde",
    "Gravity-related height": "Kote",
    "Depth": "Dybde",
}
danske_enheder = {
    "metre": "[m]",
    "degree": "[decimalgrader]",
    "degree minute second hemisphere": "[°]",
}


def Srid_fra_CRS(crs: CRS, navn: str) -> Srid:
    """Oversæt en pyproj.CRS til en Srid"""

    axes = [danske_akser.get(ax.name, ax.name) for ax in crs.axis_info]
    units = [danske_enheder.get(ax.unit_name, "") for ax in crs.axis_info]

    akser_enheder = [f"{ax} {un}" for ax, un in zip(axes, units)]

    x, y, z = None, None, None
    if len(akser_enheder) == 1:
        (z,) = akser_enheder
    elif len(akser_enheder) == 2:
        x, y = akser_enheder
    else:
        x, y, z = akser_enheder

    return Srid(name=navn, x=x, y=y, z=z)


def konstruer_tidsserier(
    punkter_identer: list[tuple[Punkt, str]],
    transformers: dict[Srid, dict[Srid, Transformer]],
    historik: bool,
) -> list[GNSSTidsserie]:
    """
    Konstruér tidsserier til visning i tabeller og plots

    For hvert punkt i listen `punkter_identer` udtrækkes alle koordinater med srid'er
    svarende til source_srid-nøglerne givet i `transformers`.

    Koordinaterne transformeres derefter via de givne "transformers", til `target_srid`,
    og gemmes i en tidsserie til hvert punkt.
    """
    if historik:
        historik_filter = lambda k: True
    else:
        historik_filter = lambda k: k.registreringtil is None

    # Tag target_srid fra første transformation
    target_srid = [
        trg for trg_trans in transformers.values() for trg in trg_trans.keys()
    ][0]

    # Konstruér tidsserier ud fra punkternes koordinater
    tidsserier = []
    for punkt, matchet_ident in punkter_identer:

        tidsserie = GNSSTidsserie(
            punkt=punkt,
            navn=f"{matchet_ident}",
            formål=f"",
            srid=target_srid,
        )

        # Hver af punktets koordinater transformeres via dets Srid til det valgte
        # output-crs, og tilføjes til tidsserien
        koordinater = []
        for k in punkt.koordinater:
            if not (
                k.srid in transformers.keys()
                and k.fejlmeldt == False
                and historik_filter(k)
            ):
                continue

            # Transformér koordinaterne. Vi ændrer deres x,y,z værdier in-place. Det er
            # stadig database-objekter, så man skal IKKE committe noget fra denne session.
            # Man vil nok blive reddet af database-triggerne, som forbyder updates, men
            # stadig...
            k.x, k.y, k.z = transformers[k.srid][target_srid].transform(
                k.x or 0.0, k.y or 0.0, k.z or 0.0
            )
            k.transformeret = True
            k.srid = target_srid

            koordinater.append(k)

        if not koordinater:
            fire.cli.print(
                f"Springer {matchet_ident} over. Fandt ingen koordinater.",
            )
            continue

        tidsserie.koordinater = sorted(koordinater, key=(lambda k: k.t))
        tidsserier.append(tidsserie)

    return tidsserier
