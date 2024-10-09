from datetime import datetime

import click
import pandas as pd
from sqlalchemy.exc import NoResultFound

import fire.cli
from fire.api.model import (
    Tidsserie,
    HøjdeTidsserie,
)
from fire.cli.ts import (
    _find_tidsserie,
    _udtræk_tidsserie,
)
from fire.cli.ts.statistik_ts import (
    StatistikHts,
    beregn_statistik_til_hts_rapport,
)
from fire.cli.ts.plot_ts import (
    plot_tidsserie,
    plot_data,
    plot_fit,
    plot_konfidensbånd,
    plot_hts_analyse,
    plot_tidsserier,
)

from . import ts

HTS_PARAMETRE = {
    "t": "t",
    "decimalår": "decimalår",
    "kote":"kote",
    "sz": "sz",
}


@ts.command()
@click.argument("objekt", required=True, type=str)
@click.option(
    "--parametre",
    "-p",
    required=False,
    type=str,
    default="t,decimalår,kote,sz",
    help="""Vælg hvilke parametre i tidsserien der skal udtrækkes. Som standard
sat til 't,decimalår,kote,sz'. Bruges værdien 'alle' udtrækkes alle mulige parametre
i tidsserien.  Se ``fire ts hts --help`` for yderligere detaljer.""",
)
@click.option(
    "--fil",
    "-f",
    required=False,
    type=click.Path(writable=True),
    help="Skriv den udtrukne tidsserie til Excel fil.",
)
@fire.cli.default_options()
def hts(objekt: str, parametre: str, fil: click.Path, **kwargs) -> None:
    """
    Udtræk en Højdetidsserie.


    "OBJEKT" sættes til enten et punkt eller et specifik navngiven tidsserie.
    Hvis "OBJEKT" er et punkt udskrives en oversigt over de tilgængelige
    tidsserier til dette punkt. Hvis "OBJEKT" er en tidsserie udskrives
    tidsserien på skærmen. Hvilke parametre der udskrives kan specificeres
    i en kommasepareret liste med ``--parametre``. Følgende parametre kan vælges::

    \b
        t               Tidspunkt for koordinatobservation
        decimalår       Tidspunkt for koordinatobservation i decimalår
        kote            Koordinatens z-komponent
        sz              z-komponentens (kotens) spredning (i mm)

    Tidsserien kan skrives til en fil ved brug af ``--fil``, der resulterer i
    en csv-fil på den angivne placering. Denne fil kan efterfølgende åbnes
    i Excel, eller et andet passende program, til videre analyse.

    \b
    **EKSEMPLER**

    Vis alle tidsserier for punktet RDIO::

        fire ts hts RDIO

    Vis tidsserien "K-63-00909_HTS_81066" med standardparametre::

        fire ts hts K-63-00909_HTS_81066

    Vis tidsserie med brugerdefinerede parametre::

        fire ts hts K-63-00909_HTS_81066 --parametre decimalår,kote,sz

    Gem tidsserie med samtlige tilgængelige parametre::

        fire ts hts K-63-00909_HTS_81066 -p alle -f RDIO_HTS_81066.xlsx
    """
    _udtræk_tidsserie(objekt, HøjdeTidsserie, HTS_PARAMETRE, parametre, fil)

    return

@ts.command()
@click.argument("tidsserie", required=True, type=str)
@click.option(
    "--plottype",
    "-t",
    required=False,
    type=click.Choice(["rå", "fit", "konf"]),
    default="rå",
    help="Hvilken type plot vil man se?",
)
@click.option(
    "--parametre",
    "-p",
    required=False,
    type=str,
    default="kote",
    help="Hvilken parameter skal plottes?",
)
@fire.cli.default_options()
def plot_hts(tidsserie: str, plottype: str, parametre: str, **kwargs) -> None:
    """
    Plot en Højdetidsserie.

    Et simpelt plot der som standard viser kotens udvikling over tid.

    "TIDSSERIE" er et Højdetidsserienavn fra FIRE. Eksisterende Højdetidsserier kan
    fremsøges med kommandoen ``fire ts hts <punktnummer>``.
    Hvilke parametre der plottes kan specificeres i en kommasepareret liste med
    ``--parametre``. Højst 3 parametre plottes. Følgende parametre kan vælges::

    \b
        t               Tidspunkt for koordinatobservation
        kote            Koordinatens z-komponent
        sz              z-komponentens (kotens) spredning (i mm)
        decimalår       Tidspunkt for koordinatobservation i decimalår

    Typen af plot som vises kan vælges med ``--plottype``. Følgende plottyper kan vælges::

    \b
        rå              Plot rå data
        fit             Plot lineær regression oven på de rå data
        konf            Plot lineær regression med konfidensbånd

    \f
    **EKSEMPLER:**

    Plot af højdetidsserie for GED3::

        fire ts plot-hts 52-03-00846_HTS_81005

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_hts_GED3_HTS_81005.png
        :width: 800
        :alt: Eksempel på plot af højde-tidsserie for GED3.

    Plot af højdetidsserie for GED2::

        fire ts plot-hts 52-03-00845_HTS_81050 -t fit

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_hts_GED2_HTS_81050_fit.png
        :width: 800
        :alt: Eksempel på plot af højde-tidsserie for GED2.

    Plot af højdetidsserie for GED5::

        fire ts plot-hts 52-03-09089_HTS_81068 -t konf

    Resulterer i visning af nedenstående plot.

    .. image:: figures/fire_ts_plot_hts_GED5_HTS_81068_konf.png
        :width: 800
        :alt: Eksempel på plot af højde-tidsserie for GED5.

    """
    plot_funktioner = {
        "rå": plot_data,
        "fit": plot_fit,
        "konf": plot_konfidensbånd,
    }

    try:
        tidsserie = _find_tidsserie(HøjdeTidsserie, tidsserie)
    except NoResultFound:
        raise SystemExit("Højdetidsserie ikke fundet")

    parametre = parametre.split(",")

    for parm in parametre:
        if parm not in HTS_PARAMETRE.keys():
            raise SystemExit(f"Ukendt tidsserieparameter '{parm}'")

    parametre = [HTS_PARAMETRE[parm] for parm in parametre]

    plot_tidsserie(tidsserie, plot_funktioner[plottype], parametre, y_enhed="mm")


@ts.command()
@click.argument(
    "objekt",
    required=True,
    nargs=-1,
    type=str,
)
@click.option(
    "--fil",
    "-f",
    required=False,
    type=click.Path(writable=True),
    help="Skriv beregnet tidsseriestatistik til csv-fil.",
)
@click.option(
    "--nmin",
    required=False,
    type=int,
    default=3,
    help="Minimum antal punkter i tidsserien.",
)
@click.option(
    "--plot/--no-plot",
    is_flag=True,
    default=True,
    help="Vælg om plots skal vises eller ej.",
)
@fire.cli.default_options()
def analyse_hts(
    objekt: tuple[str],
    fil: click.Path,
    nmin: int,
    plot: bool,
    **kwargs,
):
    """
    Analysér en eller flere Højdetidsserier.

    Der beregnes for hver af de valgte højdetidsserier et vægtet, lineært fit til
    tidsserien. Som vægte anvendes de inverse koteusikkerheder.

    Der vises et plot af alle tidsseriernes normaliserede koter. Dernæst vises et
    detaljeret plot af hver tidsserie med konfidensbånd og diverse andre
    kvalitetsparametre for fittet. De detaljerede plots kan til/fravælges med
    ``--plot/--no-plot``.
    Analyseresultaterne gemmes i csv-format hvis en sti angives med ``--fil``. Se
    nedenfor, for detaljer om analysen.

    ``OBJEKT`` kan enten være en Punktsamling eller en liste indeholdende én eller flere
    HøjdeTidsserier.

    Hvis ``OBJEKT`` angiver flere Højdetidsserier, skal alle tidsserierne være givet over
    det samme jessenpunkt. Hvis ``OBJEKT`` angiver en Punktsamling analyseres alle
    Højdetidsserierne i punktsamlingen.

    Tidsserier med meget få datapunkter filtreres fra i søgningen. Antallet kan vælges med
    ``--nmin``. Default-værdien er 3 datapunkter.

    **Statistisk analyse:**

    Programmet beregner som nævnt et lineært fit ved brug af vægtet mindste kvadraters
    metode (WLS). Som vægte anvendes koternes usikkerheder. I mange tilfælde er
    usikkerhederne i databasen angivet til 0 mm (pga. nedrunding). I disse tilfælde
    anvendes en værdi for usikkerheden på 0.5 mm.
    Følgende er en beskrivelse af de nogle af statistiske parametre som programmet
    beregner og som fortjener forklaring::

    \b
        std_0               Standardafvigelse af residualer
    \b
        var_0               Varians af residualer
    \b
        std_hældning        Estimeret varians af estimeret hældning
    \b
        var_hældning        Estimeret varians af estimeret hældning
    \b
        ki_hældning         Nedre/øvre grænse for konfidensinterval for estimeret
                            hældning. Konfidensintervallet er bestemt ved
                            signifikansniveau på 5%
    \b
        mex                 Middelepoke for tidsserien (Gennemsnit af x-værdier)
    \b
        mey                 Tidsseriens fittede værdi ved middelepoken
    \b
        er_bevægelse_signifikant    Resultat af hypotesetest (T-test) for om
                                    bevægelsen er signifikant forskellig fra 0
    \b
        alpha_bevægelse_signifikant Signifikansniveau anvendt i T-test (default 1%)

    I de detaljerede plots vises som nævnt konfidensbånd for fittet. Hertil anvendes
    signifikansniveau på 5%.
    """
    # skaler data så der regnes og plottes i [mm] i stedet for [m]
    skalafaktor = 1e3

    # Minimum spredning
    apriori_spredning = 0.5 # [mm]

    # Hent tidsserier som skal analyseres baseret på bruger input.
    try:
        # Antag først at der er givet en punktsamling
        punktsamling = fire.cli.firedb.hent_punktsamling(objekt[0])
    except NoResultFound:
        # Ellers må det være tidsserier
        tidsserier = (
            fire.cli.firedb.session.query(HøjdeTidsserie)
            .filter(
                HøjdeTidsserie._registreringtil == None,
                HøjdeTidsserie.navn.in_(objekt),
            )
            .all()
        )  # NOQA

        if not tidsserier:
            raise SystemExit("Fandt ingen tidsserier")

        punktsamling = tidsserier[0].punktsamling
        punktsamling.navn
        # Tjek at tidsserierne alle har samme jessenpunkt og jessenkote
        ugyldige_tidsserier = [
            ts
            for ts in tidsserier
            if not (ts.punktsamling.jessenkote == punktsamling.jessenkote
            and ts.punktsamling.jessenpunkt == punktsamling.jessenpunkt)
        ]

        if ugyldige_tidsserier:
            raise SystemExit("Fandt tidsserier i forskellige lokale højdesystemer. Afbryder!")

    else:
        tidsserier: list[HøjdeTidsserie] = punktsamling.tidsserier

    # Filtrér desuden på minimum antal punkter, da de ikke kan filtreres via SQL
    tidsserier = [
        ts
        for ts in tidsserier
        if (len(ts) >= nmin )
    ]

    if not tidsserier:
        raise SystemExit("Fandt ingen tidsserier")

    for ts in tidsserier:
        print(f"Fandt {ts.navn}")

    # Beregn lineær regression for alle tidsserier samt statistik til rapportering.
    ts_statistik = {}
    ts_fejlende = []
    for ts in tidsserier:
        y = [skalafaktor * yy for yy in ts.kote]

        # Divider med 1000, for at få spredninger fra mm til m. Anvend derefter skalafaktor
        # Hvis spredninger fra databasen er nul (ofte pga. nedrunding i det gamle system),
        # så anvendes en apriori spredning på 0.5 mm.
        y_vægte = [1/(skalafaktor * (sy if sy!=0 else apriori_spredning)/1e3)**2  for sy in ts.sz]

        ts.forbered_lineær_regression(ts.decimalår, y, y_vægte = y_vægte)

        try:
            ts.beregn_lineær_regression()
        except ValueError as e:
            print(f"Fejl ved løsning af tidsserien {ts.navn}:\n{e}")
            # Fjern tidsserien, så man stadig kan se plots af de tidsserier som ikke gav fejl
            ts_fejlende.append(ts)
            continue

        ts_statistik[ts.navn] = beregn_statistik_til_hts_rapport(ts)

    tidsserier = list(set(tidsserier)-set(ts_fejlende))

    # Gem statistik
    if fil:
        linjer = ""
        for _, statistik in ts_statistik.items():
            header = str(statistik).split("\n")[0]
            linje = str(statistik).split("\n")[1]

            linjer += f"{linje}\n"

        outstr = f"{header}\n{linjer}"

        with open(fil, "w") as f:
            f.write(outstr)

    if not plot:
        return

    # Plot punktsamlingens tidsserier
    plot_tidsserier(punktsamling.navn, tidsserier)

    # Detaljerede plots af analyseresultater for de enkelte tidsrækker.
    for ts in tidsserier:
        plot_hts_analyse("Kote [mm]", ts.linreg, ts_statistik[ts.navn])

    return
