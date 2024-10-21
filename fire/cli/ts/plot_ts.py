from typing import Callable

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FormatStrFormatter
import numpy as np

from fire.api.model import (
    Tidsserie,
    GNSSTidsserie,
    HøjdeTidsserie,
    PunktSamling,
)

from fire.api.model.tidsserier import PolynomieRegression1D
from fire.cli.ts.statistik_ts import (
    StatistikGnss,
    StatistikGnssSamlet,
    StatistikHts,
)

TS_PLOTTING_LABELS = {
    "t": "Dato",
    "x": "x",
    "y": "y",
    "z": "z",
    "kote": "Kote",
    "X": "X",
    "Y": "Y",
    "Z": "Z",
    "n": "Nord",
    "e": "Øst",
    "u": "Op",
    "decimalår": "År",
}

ENHEDER_SKALAFAKTOR = {
    "m": 1,
    "mm": 1e3,
    "μm": 1e6,
    "micron": 1e6,
}


def plot_tidsserie(
    ts: Tidsserie,
    plot_funktion: Callable,
    parametre: list = ["n", "e", "u"],
    y_enhed: str = "m",
):
    """
    Plotter en Tidsserie.

    Denne funktion håndterer figuropsætningen, og kalder ``plot_funktion``, som
    forventes at foretage selve plottingen af data.
    """
    n_parm = min(len(parametre), 3)

    skalafaktor = ENHEDER_SKALAFAKTOR[y_enhed]

    ax = plt.figure()
    plt.suptitle(ts.navn)

    for i, parm in enumerate(parametre, start=1):
        if i > 3:
            break

        y = [skalafaktor * yy for yy in getattr(ts, parm)]

        try:
            label = TS_PLOTTING_LABELS[parm]
        except KeyError:
            label = parm

        ax = plt.subplot(int(f"{n_parm}{1}{i}"))
        plot_funktion(ts.decimalår, y, y_enhed=y_enhed)
        plt.ylabel(f"{label} [{y_enhed}]")
        plt.grid()

    # Vis kun xlabel for nederste subplot
    plt.xlabel("År")

    # Vis kun legend hvis der er noget at vise (ellers vises en tom boks),
    # samt hvis der kun er ét plot i figuren (ellers bliver det for gnidret)
    handles, labels = ax.get_legend_handles_labels()
    if labels and n_parm == 1:
        plt.legend(handles, labels)

    plt.show()


def plot_gnss_analyse(
    label: str,
    linreg: PolynomieRegression1D,
    statistik: StatistikGnssSamlet,
    alpha: float = 0.05,
    er_samlet: bool = False,
):
    """
    Plot resultaterne af en GNSS-analyse.

    Hvis regressionen er en del af et TidsserieEnsemble kan "samlet" statistik
    plottes hvis flaget ``er_samlet`` sættes.

    ``alpha`` bestemmer signifkansniveauet for konfidensbånd til fittet.

    Reference-hældningen vises som en linje der skærer regressionslinjen i punktet (mex,
    mey), som er punktet i midten af tidsserien (middelepoken).
    """

    # Prædiktioner og intervaller
    x_præd = np.linspace(linreg.x[0], linreg.x[-1], 1000)
    y_præd = linreg.beregn_prædiktioner(x_præd)

    konfidensbånd = linreg.beregn_konfidensbånd(
        x_præd,
        y_præd,
        alpha=alpha,
        er_samlet=False,
    )

    konfidensbånd_samlet = linreg.beregn_konfidensbånd(
        x_præd,
        y_præd,
        alpha=alpha,
        er_samlet=True,
    )

    # Uplift
    uplift_fit = statistik.reference_hældning * (x_præd - linreg.mex) + linreg.mey

    # Plotting
    plt.rcParams["figure.autolayout"] = True
    plt.figure(figsize=(12, 9))
    ax = plt.subplot(111)
    ax.scatter(linreg.x, linreg.y, marker="*", color="black", label="GNSS Observation")

    ax.plot(
        x_præd,
        y_præd,
        "r",
        label=f"Hældning af fit: {linreg.beta[1]:.3f} [mm/år]",
    )
    ax.plot(
        x_præd,
        uplift_fit,
        "k",
        label=f"Uplift-rate: {statistik.reference_hældning:.3f} [mm/år]",
    )

    # Konfidensbånd
    ax.plot(x_præd, konfidensbånd[0, :], color="green")
    ax.plot(
        x_præd,
        konfidensbånd[1, :],
        color="green",
        label=f"{100*(1-alpha):g}% Konfidensbånd",
    )

    # Konfidensbånd (samlet)
    if er_samlet:
        ax.plot(
            x_præd,
            konfidensbånd_samlet[0, :],
            color="blue",
        )
        ax.plot(
            x_præd,
            konfidensbånd_samlet[1, :],
            color="blue",
            label=f"{100*(1-alpha):g}% Konfidensbånd (samlet)",
        )

    ax.scatter(
        linreg.mex,
        linreg.mey,
        marker="o",
        facecolors="none",
        edgecolors="blue",
        label="Middelepoke",
    )

    ax.set_title(
        f"Tidsserie: {statistik.TidsserieID}    R$^2$ = {statistik.R2:.2f}   N = {statistik.N}   N$\\mathregular{{_{{binned}}}}$ = {statistik.N_binned}"
    )
    ax.set_xlabel("Dato")
    ax.set_ylabel(label)

    ax.yaxis.set_major_formatter(FormatStrFormatter("%.3f"))

    ax.grid()
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.2, -0.15),
        fancybox=True,
        shadow=True,
        ncol=1,
    )

    # T-test resultater til visning
    t_tekst = f"|t| = {statistik.T_test_score:.2f}\nt$\\mathregular{{_{{crit}}}}$ = {statistik.T_test_kritiskværdi:.2f}\n"

    if statistik.T_test_H0accepteret:
        t_tekst += (
            f"H$_{{0}}$ accepteret ved {statistik.T_test_alpha*100}% signifikansniveau"
        )
    else:
        t_tekst += (
            f"H$_{{0}}$ forkastet ved {statistik.T_test_alpha*100}% signifikansniveau"
        )

    # Z-test resultater til visning
    z_tekst = f"|z| = {statistik.Z_test_score:.2f}\nz$\\mathregular{{_{{crit}}}}$ = {statistik.Z_test_kritiskværdi:.2f}\n"

    if statistik.Z_test_H0accepteret:
        z_tekst += f"H$_{{0}}$ accepteret ved {statistik.Z_test_alpha*100}% signifikansniveau (samlet)"
    else:
        z_tekst += f"H$_{{0}}$ forkastet ved {statistik.Z_test_alpha*100}% signifikansniveau (samlet)"

    # Standardafvigelse data til visning
    std_tekst = f"Std. af data = {statistik.std_0:.2f} mm\n\
Std. af data fra alle tidsserier (samlet) = {statistik.std_samlet:.2f} mm"

    plt.figtext(0.55, 0.18, t_tekst)
    if er_samlet:
        plt.figtext(0.55, 0.11, z_tekst)
    plt.figtext(0.55, 0.05, std_tekst)

    plt.show()


def plot_hts_analyse(
    label: str,
    linreg: PolynomieRegression1D,
    statistik: StatistikHts,
    alpha: float = 0.05,
):
    """
    Plot resultaterne af en Højdetidsserie-analyse.

    ``alpha`` bestemmer signifikansniveauet for konfidensbånd til fittet.
    """

    # Prædiktioner og intervaller
    x_præd = np.linspace(linreg.x[0], linreg.x[-1], 1000)
    y_præd = linreg.beregn_prædiktioner(x_præd)

    konfidensbånd = linreg.beregn_konfidensbånd(
        x_præd,
        y_præd,
        alpha=alpha,
        er_samlet=False,
    )

    # Plotting
    plt.rcParams["figure.autolayout"] = True
    plt.figure(figsize=(12, 9))
    ax = plt.subplot(111)
    ax.errorbar(
        x=linreg.x,
        y=linreg.y,
        yerr=np.sqrt(1 / linreg._W),
        fmt="ko",
        capsize=3,
        label=f"Kote $\\pm$ std. afvigelse",
    )

    ax.plot(
        x_præd,
        y_præd,
        "r",
        label=f"Hældning af fit: {linreg.beta[1]:.3f} [mm/år]",
    )

    # Konfidensbånd
    ax.plot(x_præd, konfidensbånd[0, :], color="green")
    ax.plot(
        x_præd,
        konfidensbånd[1, :],
        color="green",
        label=f"{100*(1-alpha):g}% Konfidensbånd",
    )

    ax.set_title(f"Tidsserie: {statistik.TidsserieID}    N = {statistik.N}")
    ax.set_xlabel("År")
    ax.set_ylabel(label)

    ax.yaxis.set_major_formatter(FormatStrFormatter("%.3f"))

    ax.grid()
    ax.legend(
        loc="upper center",
        fancybox=True,
        ncol=1,
    )
    tekst = f"Std. af residualer = {statistik.std_0:.2f} mm\n"

    if not statistik.er_bevægelse_signifikant:
        tekst += f"H$_{{0}}$ accepteret ved {statistik.alpha_bevægelse_signifikant*100}% signifikansniveau"
    else:
        tekst += f"H$_{{0}}$ forkastet ved {statistik.alpha_bevægelse_signifikant*100}% signifikansniveau"

    # Standardafvigelse data til visning

    ax.text(
        0.5,
        0.05,
        tekst,
        transform=ax.transAxes,
        fontsize=10,
        bbox={
            "facecolor": "white",
            "alpha": 0.8,
            "edgecolor": (0.8,) * 3,
            "pad": 0.4,
            "boxstyle": "round",
        },
        ha="center",
        va="center",
    )

    plt.show()


def plot_data(x: list, y: list, **kwargs):
    plt.plot(
        x,
        y,
        ".",
        markersize=4,
        color="black",
    )


def plot_fit(x: list, y: list, y_enhed: str = "mm"):
    """
    Plot x og y samt bedste rette linje.

    Enheden på x forventes at være decimalår.
    """

    lr = PolynomieRegression1D(x, y)
    lr.solve()

    x_præd = np.linspace(lr.x[0], lr.x[-1], 1000)
    y_præd = lr.beregn_prædiktioner(x_præd)

    plt.plot(
        x_præd,
        y_præd,
        "-",
        color="red",
        label=f"Hældning af fit: {lr.beta[1]:.3f} [{y_enhed}/år]",
    )
    plot_data(lr.x, lr.y)
    plt.ylim(lr.y.min(), lr.y.max())


def plot_konfidensbånd(x: list, y: list, y_enhed: str = "mm"):
    """
    Plot x og y samt bedste rette linje med konfidensbånd.

    Enheden på x forventes at være decimalår.
    """
    # Binning
    x_binned, y_binned = GNSSTidsserie.binning(x, y)

    # Foretag lineær regresion
    lr = PolynomieRegression1D(x_binned, y_binned)
    lr.solve()

    # Prædiktioner
    x_præd = np.linspace(lr.x[0], lr.x[-1], 1000)
    y_præd = lr.beregn_prædiktioner(x_præd)

    # Konfidensbånd
    konfidensbånd = lr.beregn_konfidensbånd(x_præd, y_præd)

    plt.plot(
        x_præd,
        y_præd,
        "-",
        color="red",
        label=f"Hældning af fit: {lr.beta[1]:.3f} [{y_enhed}/år]",
    )
    plt.plot(
        x_præd,
        konfidensbånd[0, :],
        "g-",
    )
    plt.plot(
        x_præd,
        konfidensbånd[1, :],
        "g-",
        label="95% konf. bånd",
    )
    plot_data(lr.x, lr.y)


def plot_tidsserier(
    titel: str,
    tidsserier: list[HøjdeTidsserie],
    fremhæv_nyeste_punkt: bool = False,
    y_enhed: str = "mm",
) -> None:
    """
    Et simpelt plot af en liste af Højdetidsserier

    Tidsseriernes y-værdi normaliseres til det første punkt i serien.
    Sættes ``fremhæv_nyeste_punkt=True``, så fremhæves det sidste punkt i tidsserien.
    """
    skalafaktor = ENHEDER_SKALAFAKTOR[y_enhed]

    # Brug forskellige markør-typer. Og vi gider ikke have markørtypen "."/point med!
    markers = [m for m in Line2D.filled_markers if m != "."]

    fig = plt.figure()
    plt.suptitle(titel)
    for i, ts in enumerate(tidsserier):
        x = np.array(ts.decimalår)
        idx_sorted = np.argsort(x)
        x = x[idx_sorted]

        y = np.array(ts.kote) * skalafaktor
        y = y[idx_sorted]
        y = y - y[0]

        p = plt.plot(
            x,
            y,
            marker=markers[i % len(markers)],
            markersize=6,
            label=f"{ts.navn}",
        )

        # Plot det sidste "nye" punkt og fremhæv det
        if fremhæv_nyeste_punkt:
            # udregn koteændringen
            delta = y[-1] - y[-2]

            plt.plot(
                x[-1],
                y[-1],
                marker="o",
                mfc="none",
                color=p[0].get_color(),
                markersize=p[0].get_markersize() * 2,
            )

            plt.text(
                x[-1] + 2e-1,
                y[-1],
                f"$\\Delta$-kote {delta:.2f}",
                color=p[0].get_color(),
            )

    plt.xlabel("År")
    plt.ylabel(f"Normaliseret kote [{y_enhed}]")
    plt.legend()
    plt.grid()
    plt.show()
