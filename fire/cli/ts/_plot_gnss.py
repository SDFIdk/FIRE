from typing import Callable

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import numpy as np

from fire.api.model import GNSSTidsserie

from fire.api.model.tidsserier import PolynomieRegression1D


GNSS_TS_PLOTTING_LABELS = {
    "t": "Dato",
    "x": "x [mm]",
    "y": "y [mm]",
    "z": "z [mm]",
    "X": "X [mm]",
    "Y": "Y [mm]",
    "Z": "Z [mm]",
    "n": "Nord [mm]",
    "e": "Øst [mm]",
    "u": "Op [mm]",
    "decimalår": "År",
}


def plot_gnss_ts(
    ts: GNSSTidsserie, plot_funktion: Callable, parametre: list = ["n", "e", "u"]
):
    """
    Plotter en GNSSTidsserie.

    Denne funktion håndterer figuropsætningen, og kalder ``plot_funktion``, som
    forventes at foretage selve plottingen af data.
    """
    # Skalér y-værdien for at vise data i mm
    skalafaktor = 1e3

    n_parm = min(len(parametre), 3)

    ax = plt.figure()
    plt.suptitle(ts.navn)

    for i, parm in enumerate(parametre, start=1):
        if i > 3:
            break

        y = [skalafaktor * yy for yy in getattr(ts, parm)]

        try:
            label = GNSS_TS_PLOTTING_LABELS[parm]
        except KeyError:
            label = parm

        ax = plt.subplot(int(f"{n_parm}{1}{i}"))
        plot_funktion(ts.decimalår, y)
        plt.ylabel(label)
        plt.grid()

    # Vis kun xlabel for nederste subplot
    plt.xlabel("År")

    # Vis kun legend hvis der er noget at vise (ellers vises en tom boks),
    # samt hvis der kun er ét plot i figuren (ellers bliver det for gnidret)
    handles, labels = ax.get_legend_handles_labels()
    if labels and n_parm == 1:
        plt.legend(handles, labels)

    plt.show()


def plot_data(x: list, y: list):
    plt.plot(
        x,
        y,
        ".",
        markersize=4,
        color="black",
    )


def plot_fit(x: list, y: list):
    """
    Plot x og y samt bedste rette linje.

    Enhederne af (x,y) forventes at være (decimalår, mm).
    """

    lr = PolynomieRegression1D("", x, y)
    lr.solve()

    x_præd = np.linspace(lr.x[0], lr.x[-1], 1000)
    y_præd = lr.beregn_prædiktioner(x_præd)

    plt.plot(
        x_præd,
        y_præd,
        "-",
        color="red",
        label=f"Hældning af fit: {lr.beta[1]:.3f} [mm/år]",
    )
    plot_data(lr.x, lr.y)
    plt.ylim(lr.y.min(), lr.y.max())


def plot_konfidensbånd(x: list, y: list):
    """
    Plot x og y samt bedste rette linje med konfidensbånd.

    Enhederne af (x,y) forventes at være (decimalår, mm).
    """
    # Binning
    x_binned, y_binned = GNSSTidsserie.binning(x, y)

    # Foretag lineær regresion
    lr = PolynomieRegression1D("", x_binned, y_binned)
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
        label=f"Hældning af fit: {lr.beta[1]:.3f} [mm/år]",
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
