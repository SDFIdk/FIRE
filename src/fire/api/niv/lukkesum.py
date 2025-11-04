from dataclasses import dataclass
from math import sqrt, pow


import networkx as nx
import numpy as np
from matplotlib import pyplot as plt


@dataclass
class LinjeStats:
    """
    Statistiske parametre regnet pr. nivellementslinje

    Frem-retningen defineres som målingen fra `fra` til `til`, mens
    tilbage-retning er defineret modsat.
    """

    fra: str
    til: str
    deltaH_mean: float
    deltaH_frem: float
    deltaH_tilbage: float
    afstand_mean: float
    afstand_frem: float
    afstand_tilbage: float
    n_frem: float
    n_tilbage: float
    rho: float
    rho_mærke: float

    def omregn_til_mm(self):
        til_mm = 1e3
        til_mm_pr_sqrt_km = pow(10, 4.5)

        self.rho *= til_mm
        self.rho_mærke *= til_mm_pr_sqrt_km

        return self


@dataclass
class LukkesumStats:
    """
    Statistiske parametre fra en lukkesumsberegning regnet for en hel polygon
    """

    summa_rho: float
    summa_rho_mærke: float
    lukkesum: float
    lukkesum_frem: float
    lukkesum_tilbage: float
    lukkesum_mærke: float
    lukkesum_frem_mærke: float
    lukkesum_tilbage_mærke: float
    total_afstand: float
    total_afstand_frem: float
    total_afstand_tilbage: float

    # En liste af de linjer som indgik i lukkesumsberegningen
    linjer: list[LinjeStats]

    def omregn_til_mm(self):
        til_mm = 1e3
        til_mm_pr_sqrt_km = pow(10, 4.5)

        self.summa_rho *= til_mm
        self.summa_rho_mærke *= til_mm_pr_sqrt_km
        self.lukkesum *= til_mm
        self.lukkesum_frem *= til_mm
        self.lukkesum_tilbage *= til_mm
        self.lukkesum_mærke *= til_mm_pr_sqrt_km
        self.lukkesum_frem_mærke *= til_mm_pr_sqrt_km
        self.lukkesum_tilbage_mærke *= til_mm_pr_sqrt_km

        return self


def aggreger_parallelle_kanter(
    multidigraf: nx.MultiDiGraph, knude: str, næste_knude: str
) -> tuple[float, float, int]:
    """
    Beregn gennemsnit af alle linjer fra punkt til næste punkt

    Da der kan være flere parallelle linjer tages der for robusthed gennemsnittet
    af de parallelle linjer. På den måde er det ligemeget om der er fx 2 frem og 1
    tilbage niv.
    Hvis der ikke er forbindelse mellem `knude` og `næste_knude` bliver deltaH og
    afstanden sat til NaN.
    """
    try:
        deltaH = [
            obs["data"].deltaH for obs in multidigraf[knude][næste_knude].values()
        ]
        afstand = [
            obs["data"].afstand for obs in multidigraf[knude][næste_knude].values()
        ]

        n = len(deltaH)  # antallet af parallelle linjer
    except KeyError:
        deltaH = [float("nan")]
        afstand = [float("nan")]
        n = 0
    return np.mean(deltaH), np.mean(afstand), n


def aggreger_multidigraf(multidigraf: nx.MultiDiGraph) -> nx.DiGraph:
    """
    Aggreger alle parallelle kanter i en graf og beregn afledte størrelser

    Returnerer et `networkx.DiGraph` objekt som max indeholder én forbindelse fra et punkt
    til et andet punkt. Hver kant i den returnerede digraf har en attribut af typen
    `LinjeStats`, som indeholder de beregnede størrelser for hver linje.

    Den almindelige antagelse i beregning af statistik for nivellement er, at der
    for hver linje er netop én frem-, og én tilbage-observation af ca samme størrelse med
    forskelligt fortegn, som man så fx kan lægge sammen for at få målefejlen.

    Dette er dog ikke altid tilfældet, hvorfor der for hver linje først beregnes følgende
    størrelser for både frem- og tilbage retningen:

        1. Gennemsnitlig ΔH for parallelle linjer
        2. Gennemsnitlig afstand for parallelle linjer
        3. Antal observationer af parallelle linjer

    Disse størrelser bruges derefter til at beregne de gængse størrelser:

        4. Gennemstnitlig ΔH af frem- og tilbage, defineret positiv i frem-retningen.
        5. Gennemsnitlig afstand af frem- og tilbage
        6. Diskrepansen ρ ("rho") mellem frem- og tilbage
        7. Diskrepansen ρ' ("rho mærke") normaliseret efter den kvadratroden af
           gennemsnitlige afstand.

    Bemærk, at 4. altid regnes i frem-retningen. De øvrige størrelser 5-7 er uafhængig af
    retning.
    """
    # Forbered nyt graf-objekt, som ikke indeholder parallelle kanter
    digraf = nx.DiGraph(multidigraf)

    # Find alle linjer hvor der både er frem og tilbage observationer
    # og beregn gennemsnitlig observation, afstand, rho, og rho'
    for fra, til in digraf.edges:
        deltaH_frem, afstand_frem, n_frem = aggreger_parallelle_kanter(
            multidigraf, fra, til
        )
        deltaH_tilbage, afstand_tilbage, n_tilbage = aggreger_parallelle_kanter(
            multidigraf, til, fra
        )

        # Her tages der højde for at der kan være forskelligt antal frem og tilbage
        deltaH_mean = (deltaH_frem * n_frem - deltaH_tilbage * n_tilbage) / (
            n_frem + n_tilbage
        )
        afstand_mean = (afstand_frem * n_frem + afstand_tilbage * n_tilbage) / (
            n_frem + n_tilbage
        )

        rho = deltaH_frem + deltaH_tilbage
        rho_mærke = rho / sqrt(afstand_mean)

        # Gem alt som attributter på digraf-kanterne.
        digraf[fra][til]["linjestats"] = LinjeStats(
            fra=fra,
            til=til,
            deltaH_frem=deltaH_frem,
            deltaH_tilbage=deltaH_tilbage,
            afstand_frem=afstand_frem,
            afstand_tilbage=afstand_tilbage,
            n_frem=n_frem,
            n_tilbage=n_tilbage,
            deltaH_mean=deltaH_mean,
            afstand_mean=afstand_mean,
            rho=rho,
            rho_mærke=rho_mærke,
        )

    return digraf


def beregn_lukkesum(linjestats: list[LinjeStats]) -> LukkesumStats:
    """
    Beregn lukkesum for en liste af nivellementslinjer

    Er tænkt som hjælpefunktion til `lukkesum_af_polygon`, hvorfor det antages at linjerne
    alle er sammenhængende. Hvis linjerne ikke er sammenhængende, skal man se bort fra de
    resultater der specifikt handler om lukkesum.

    Dog kan det stadig bruges til fx at beregne summa_rho af en vilkårlig mængde
    usammenhængende nivellementslinjer, for at vurdere den overordnede kvalitet af
    linjerne.
    """
    # Udpak linjestats fra list[LinjeStats] til hver sin liste som vi kan summere
    deltaH_mean = [ls.deltaH_mean for ls in linjestats]
    deltaH_frem = [ls.deltaH_frem for ls in linjestats]
    deltaH_tilbage = [ls.deltaH_tilbage for ls in linjestats]
    afstand_mean = [ls.afstand_mean for ls in linjestats]
    afstand_frem = [ls.afstand_frem for ls in linjestats]
    afstand_tilbage = [ls.afstand_tilbage for ls in linjestats]
    rho = [ls.rho for ls in linjestats]

    # Beregn ønskede størrelser
    total_afstand = np.sum(afstand_mean)
    total_afstand_frem = np.sum(afstand_frem)
    total_afstand_tilbage = np.sum(afstand_tilbage)

    summa_rho = np.sum(rho)
    lukkesum = np.sum(deltaH_mean)
    lukkesum_frem = np.sum(deltaH_frem)
    lukkesum_tilbage = np.sum(deltaH_tilbage)

    summa_rho_mærke = summa_rho / sqrt(total_afstand)
    lukkesum_mærke = lukkesum / sqrt(total_afstand)

    lukkesum_frem_mærke = lukkesum_frem / sqrt(total_afstand_frem)
    lukkesum_tilbage_mærke = lukkesum_tilbage / sqrt(total_afstand_tilbage)

    # Kommentarer om lukkesumsberegning
    # Udregning af summa rho og epsilon/lukkesum kan gøres på to måder:
    # Metode 1
    # summa_rho = sum(rho)
    # epsilon   = sum(deltaH)
    #
    # Metode 2:
    # summa_rho = lukkesum_frem + lukkesum_tilbage
    # epsilon   = (lukkesum_frem - lukkesum_frem)/2
    #
    # De to metoder for summa_rho er ækvivalente. For epsilon er de kun ækvivalente
    # hvis hver linje er målt lige mange gange frem og tilbage, hvilket skyldes måden
    # vi regner deltaH på, som er en slags "gennemsnitlig" frem-observation for en
    # given linje.
    # Metode 1 laver et samlet "gennemsnit" af både frem- og tilbage-observationerne,
    # hvor tilbage-observationerne ganges med -1.
    # Metode 2 laver først gennemsnit af frem og tilbage-målinger for sig og dernæst
    # et gennemsnit og de to frem- og tilbage-gennemsnit.
    #
    # For rho er der ikke umiddelbart nogen måde at vægte alle frem- og
    # tilbage-observationer lige meget. rho regnes derfor som summen af de gennemsnitlige
    # frem-målinger og de gennemsnitlige tilbage-målinger. Så dér vil observationer i
    # retningen med færrest observationer have relativt større vægt.
    #
    # Ex: 200 frem målinger med deltaH=2 og 1 tilbage-måling med deltaH=-1:
    # Metode 1 vil vægte de 201 målinger lige meget. Men metode 2 vil tage gennemsnittet af de 200 før der tages
    # gennemsnittet af frem og tilbage, hvorved de 200 målinger vil have meget lidt vægt ift. den ene frem-måling:
    # Metode 1:
    #   rho = 1
    #   deltaH_avg = 1.995
    # Metode 2:
    #   rho = 1
    #   deltaH_avg = 1.5

    return LukkesumStats(
        summa_rho=summa_rho,
        summa_rho_mærke=summa_rho_mærke,
        lukkesum=lukkesum,
        lukkesum_frem=lukkesum_frem,
        lukkesum_tilbage=lukkesum_tilbage,
        lukkesum_mærke=lukkesum_mærke,
        lukkesum_frem_mærke=lukkesum_frem_mærke,
        lukkesum_tilbage_mærke=lukkesum_tilbage_mærke,
        total_afstand=total_afstand,
        total_afstand_frem=total_afstand_frem,
        total_afstand_tilbage=total_afstand_tilbage,
        linjer=linjestats,
    )


def lukkesum_af_polygon(
    digraf: nx.DiGraph, kreds: list, lukket: bool = True
) -> LukkesumStats:
    """
    Beregn lukkesum og andre kvalitetsparametre for en nivellementspolygon

    En polygon er givet ved punkterne i `kreds`. Der tages gennemsnit af parallelle
    linjer.
    Det antages at `kreds` er en egentlig (lukket) kreds, dvs. at første og sidste
    punkt er forbundet. Sættes lukket=False angiver at kredsen er åben. Dette kan fx
    bruges til at analysere blinde linjer.

    Returnerer et `LukkesumStats`-objekt, som både indeholder de beregnede statistiske parametre,
    og en liste af de linjer som indgik i beregningen.

    **Eksempler på lukkesummer**
    Givet et nivellementsnet:
    A ------ B ------ E ------ F
    |        |
    |        |
    D ------ C

    Med følgende observationer:
    Fra     Til     delta H
    A       B        1.1
    B       A       -1.
    B       C        2.1
    C       B       -2.
    C       D        3.1
    D       C       -3.
    D       A       -6
    A       D        5.7
    B       E        2.5
    E       B       -2.4
    E       F        1.3
    F       E       -1.2

    # Lukkesum af almindelig polygon
    > lukkesum_af_polygon([A,B,C,D])
    Returnerer:
    # Rho og deltaH for hver linje
    A-B : rho = 0.1     deltaH = 1.05
    B-C : rho = 0.1     deltaH = 2.05
    C-D : rho = 0.1     deltaH = 3.05
    D-A : rho = -0.3    deltaH = -5.85  <-- summa rho "reddes" af sidste linje, hvilket nok er urealistisk

    # Summa rho og lukkesum for frem og tilbage-nivellement.
    summa_rho = 0
    lukkesum = 0.3
    lukkesum_frem = 0.3
    lukkesum_tilbage = -0.3

    # Lukkesum af blind linje
    > lukkesum_af_polygon([B,E,F], lukket=False)
    Returnerer:
    # Rho for hver linje
    B-E : rho = 0.1     deltaH = 2.45
    E-F : rho = 0.1     deltaH = 1.25

    # Summa rho og lukkesum for frem og tilbage-nivellement.
    summa_rho = 0.2
    lukkesum = 3.7
    lukkesum_frem =  3.8
    lukkesum_tilbage = -3.6
    """
    knuder = kreds if lukket else kreds[:-1]
    næste_knuder = kreds[1:] + kreds[:1] if lukket else kreds[1:]

    # Hiv alle de relevante linjer ud af digrafen
    linjestats = [
        digraf[knude][næste_knude]["linjestats"]
        for knude, næste_knude in zip(knuder, næste_knuder)
    ]

    # Beregn lukkesum
    lukkesumstats = beregn_lukkesum(linjestats)

    return lukkesumstats


def find_polygoner(
    multidigraf: nx.MultiDiGraph, min_længde: int = 3, metode: str = "mcb", **kwargs
) -> list[tuple[str]]:
    """
    Find polygoner i et nivellementnet

    Returnerer en liste af alle fundne polygoner. Polygonerne repræsenteres som en tuple
    af punktnavne som kommer i rækkefølge rundt langs polygonen.

    Der kan vælges mellem følgende metoder til at finde polygoner:

    **Simple Cycles**

    Vælges med `metode='sc'` og anvender `networkx.simple_cycles`
    Finder alle kredse i grafen. Vælg max-længde ved at sætte `length_bound`.

    Advarsel: Hvis den analyserede graf er stor eller nettet har mange polygoner, så
    vil antallet af polygoner eksplodere meget hurtigt!

    **Cycle basis**
    Vælges med `metode='cb'` og anvender `networkx.cycle_basis`
    Finder et vilkårligt sæt af polygoner som udgør en "basis" for grafen.

    Med basis forstås, at man kan konstruere alle andre polygoner i grafen ud fra
    basisen.

    Der returneres ikke altid de samme polygoner, og de overlapper ofte hinanden,
    hvilket man sjældent er interesseret i. Dog kører denne algoritme meget hurtigt.

    **Minimum Cycle Basis**
    Vælges med `metode='mcb'` og anvender `networkx.minimum_cycle_basis`
    Finder sættet af polygoner som udgør en "minimal basis" for grafen, og er den
    anbefalede metode for normale nivellementopgaver.

    Med minimal forstås at summen af kanternes vægt langs polygonerne i den fundne
    basis er minimeret (Som default har hver kant har vægt=1, hvilket svarer til at
    antallet af kanter minimeres).

    Imodsætning til `simple_cycles` er det fundne antal polygoner ikke særlig stort, men
    for store grafer kan kravet om "minimalitet" tage meget lang tid.

    I praksis betyder det, som regel, at man ikke får polygoner som overlapper hinanden,
    hvilket normalt er det man er interesseret i. I nogen tilfælde får man dog stadig
    overlappende polygoner.

    **Eksempel**
    Givet nivellementnet som dette:
    A ------ B ------ C
    |        |        |
    |        |        |
    F ------ E ------ D

    `minimum_cycle_basis` finder polygonerne A-B-E-F og B-C-D-E.

    `simple_cycles` finder alle polygonerne, inkl. den store polygon A-B-C-D-E-F.

    `cycle_basis` finder en tilfældig kombination af to af polygonerne.
    """

    metodevalg = {
        "mcb": nx.minimum_cycle_basis,
        "sc": nx.simple_cycles,
        "cb": nx.cycle_basis,
    }
    try:
        fun = metodevalg[metode]
    except KeyError:
        raise ValueError(f"Metodevalg ikke en af: {', '.join(metodevalg.keys())}")

    # Konverterer fra MultiDiGraph til DiGraph først og dernæst til Graph.
    # På denne måde sikrer vi at kun kanter med både frem- og tilbage-observationer bliver taget med.
    graf = nx.DiGraph(multidigraf).to_undirected(reciprocal=True)

    kredse = [tuple(kreds) for kreds in fun(graf, **kwargs) if len(kreds) >= min_længde]

    return kredse


def plot_lukkesum(luksumstat: LukkesumStats):
    """
    Lav diverse plots af resultaterne af en lukkesumsberegning
    """
    # Udpak linjestats i hver sin liste
    deltaH_mean = [ls.deltaH_mean for ls in luksumstat.linjer]
    afstand_mean = [ls.afstand_mean for ls in luksumstat.linjer]
    rho = [ls.rho for ls in luksumstat.linjer]
    rho_mærke = [ls.rho_mærke for ls in luksumstat.linjer]

    afstande = np.array(afstand_mean) * 1e-3  # km
    afstand_løbende = np.cumsum(afstande)  # km
    dh = np.array(deltaH_mean)  # m
    rho = np.array(rho) * 1e3  # mm
    rhom = np.array(rho_mærke) * np.pow(10, 4.5)  # mm/sqrt(km)

    # Plot de enkelte linjer
    fig, axs = plt.subplots(3)
    fig.suptitle("Observationer")
    axs[0].plot(afstand_løbende, dh)
    axs[0].set(ylabel="deltaH [m]", xlabel="afstand [km]")

    axs[1].plot(afstand_løbende, rho)
    axs[1].set(ylabel="rho [mm]", xlabel="afstand [km]")

    axs[2].plot(afstand_løbende, rhom)
    axs[2].set(ylabel="rho' [mm/sqrt(km)]", xlabel="afstand [km]")

    # Løbende summer
    fig, axs = plt.subplots(2)
    fig.suptitle("Løbende summer")
    axs[0].plot(afstand_løbende, np.cumsum(dh))
    axs[0].set(ylabel="deltaH [m]", xlabel="afstand [km]")

    axs[1].plot(afstand_løbende, np.cumsum(rho))
    axs[1].set(ylabel="rho [mm]", xlabel="afstande [km]")

    # Scatter plots
    fig, axs = plt.subplots(3)
    fig.suptitle("Scatter plots")
    axs[0].plot(afstande, dh, ".")
    axs[0].set(ylabel="deltaH [m]", xlabel="afstand [km]")

    axs[1].plot(afstande, np.abs(rho), ".b")
    axs[1].set(ylabel="rho [mm]", xlabel="afstand [km]")

    axs[2].plot(afstande, np.abs(rhom), ".r")
    axs[2].set(ylabel="rho' [mm/sqrt(km)]", xlabel="afstand [km]")

    # Histogrammer
    fig, axs = plt.subplots(3)
    fig.suptitle("Histogrammer")

    counts, bins = np.histogram(afstande)
    axs[0].stairs(counts, bins)
    axs[0].set(xlabel="deltaH [km]", ylabel="antal")

    counts, bins = np.histogram(rho)
    axs[1].stairs(counts, bins)
    axs[1].set(xlabel="rho [mm]", ylabel="antal")

    counts, bins = np.histogram(rhom)
    axs[2].stairs(counts, bins)
    axs[2].set(xlabel="rho' [mm/sqrt(km)]", ylabel="antal")

    plt.show()
