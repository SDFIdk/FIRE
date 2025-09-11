from abc import ABC, abstractmethod
from collections import Counter, deque, defaultdict
from dataclasses import dataclass, astuple
from datetime import datetime
from functools import cached_property
import networkx as nx
from math import (
    hypot,
    sqrt,
    isnan,
)
import json
from pathlib import Path
import subprocess
from typing import Self
import xmltodict
import uuid

import pandas as pd
import numpy as np

# Smarte type hints
PunktNavn = str
# NivSubnet er en forsimplet udgave af et rigtigt net, som bare indeholder navnene på punkter som indgår
NivSubnet = list[PunktNavn]
NivNet = dict[PunktNavn, set[PunktNavn]]


class UdjævningFejl(Exception):
    """Der gik noget galt under udjævningen"""

    pass


class ValideringFejl(Exception):
    """Input til regnemotoren er forkert"""

    pass


class FastholdtIkkeObserveret(ValideringFejl):
    def __init__(self, uobserverede_fastholdte_punkter: list[PunktNavn] = None):
        self.uobserverede_fastholdte_punkter = uobserverede_fastholdte_punkter


@dataclass
class InternNivObservation:
    """Almindelige, ukorrelerede nivellementobservationer"""

    fra: PunktNavn
    til: PunktNavn
    dato: datetime
    multiplicitet: int
    afstand: float
    deltaH: float
    spredning: float
    id: str  # kan bruges til journalnummeret, eller observations-id fra FIRE


@dataclass
class InternKote:
    """Koter som enten indgår som input eller output til en beregning"""

    punkt: PunktNavn  # kan både bruge ident, database id, eller uuid.
    H: float
    dato: datetime
    spredning: float
    fasthold: bool = False
    nord: float = float("nan")
    øst: float = float("nan")


class RegneMotor(ABC):
    """
    Øverste led i RegneMotor-hierarkiet til udjævning af nivellementsobservationer

    En RegneMotor fungerer som en "adapter", som gør det muligt at arbejde med forskellige
    repræsentationer af nivellementobservationer og koter på en ensartet måde.

    En RegneMotor består basalt set af et sæt af observationer til et sæt fikspunkter,samt
    ét eller flere fastholdte punkter. Disse er hver defineret som lister af dataklasserne
    InternNivObservation hhv. InternKote. Disse klasser indeholder de basale attributter
    nødvendige for nivellementberegninger.

    **Instantiering**

    Der er defineret forskellige metoder til instantiering::

        fra_dataframe  : Start RegneMotor ud fra pandas DataFrames som anvendes i det
                         almindelige fire niv-workflow

    **Udjævning**

    Udjævning af observationer foretages med `udjævn` som forventes at være implementeret
    i alle nedarvende klasser. Udjævningsresultaterne er tilgængelige i ``self.nye_koter``
    som ``list[InternKote]``.

    **Grafanalyse**

    Observationerne i et nivellementprojekt danner et netværk af punkter (knuder) som
    forbindes af observationslinjerne (kanter). Tilsammen kaldes dette en graf. RegneMotor
    anvender derfor værktøjer kendt fra grafteori til at beregne størrelser som man
    normalt er interesseret i ifm. et nivellementprojekt.

    Der kan bl.a. undersøges, om netværket består af flere usammenhængende grafer
    (subnet), samt, for hver af disse subnet, om det indeholder mindst ét fastholdt punkt.
    Hvis ikke, vil det ikke være muligt at gennemføre udjævningen for punkterne i
    pågældende subnet.

    Almindeligvis er man ved nivellementberegninger også interesseret i at identificere
    lukkede "polygoner", bestående af observationslinjerne, også kaldet en "kreds".
    Analyseres de observerede højdeforskelle langs kanterne i en kreds er det muligt at
    beregne polygonens lukkesum for frem- og tilbagenivellement samt forskellen
    herimellem, som kaldes "summa rho".

    **Resultater**

    RegneMotor attributterne ``self.gamle_koter`` og ``self.nye_koter`` kan bruges til at
    vise udjævningsresultaterne i forskellige formater.
    ``til_dataframe`` genererer en dataframe i samme format som inputtet i
    ``fra_dataframe``

    """

    def __init__(
        self,
        observationer: list[InternNivObservation],
        gamle_koter: list[InternKote],
        projektnavn: str = "fire",
    ):
        # observationerne refereres internt med et unikt id som kan bruges i forskellige sammenhænge
        self._observationer = {uuid.uuid4():o for o in observationer}
        self._gamle_koter = {gk.punkt: gk for gk in gamle_koter}
        self.nye_koter: list[InternKote] = []
        self.projektnavn = projektnavn

    def valider_fastholdte(self):
        if 0 == len(self.fastholdte):
            raise ValideringFejl("Der skal fastholdes mindst et punkt i en beregning")

        if any([v for v in self.fastholdte.values() if isnan(v)]):
            raise ValideringFejl(
                "Der skal angives koter for alle fastholdte punkter i en beregning"
            )

        uobserverede_fastholdte_punkter = [
            pkt for pkt in self.fastholdte.keys() if pkt not in self.observerede_punkter
        ]
        if len(uobserverede_fastholdte_punkter) > 0:
            raise FastholdtIkkeObserveret(
                f"Observation(er) for fastholdte punkter: {', '.join(uobserverede_fastholdte_punkter)} er slukket eller mangler"
            )

    @property
    def observationer(self):
        return self._observationer.values()

    @property
    def gamle_koter(self):
        return self._gamle_koter.values()

    @classmethod
    def fra_dataframe(
        cls,
        observationer_df: pd.DataFrame,
        punkter_df: pd.DataFrame,
        **kwargs,
    ) -> Self:
        """Oversæt fra regneark til internt format"""
        observationer = []
        for i, obs in observationer_df.iterrows():
            # først beregn spredning
            spredning = _spredning(
                obs["Type"], obs["L"], obs["Opst"], obs["σ"], obs["δ"]
            )

            observationer.append(
                InternNivObservation(
                    fra=obs["Fra"],
                    til=obs["Til"],
                    dato=obs["Hvornår"].to_pydatetime(),
                    multiplicitet=obs["Opst"],
                    afstand=obs["L"],
                    deltaH=obs["ΔH"],
                    spredning=spredning,
                    id=obs["Journal"],
                )
            )

        gamle_koter = []
        for i, pkt in punkter_df.iterrows():
            gamle_koter.append(
                InternKote(
                    punkt=pkt["Punkt"],
                    fasthold=(True if pkt["Fasthold"] else False),
                    dato=pkt["Hvornår"].to_pydatetime(),
                    H=pkt["Kote"],
                    spredning=pkt["σ"],
                    nord=pkt["Nord"],
                    øst=pkt["Øst"],
                )
            )

        return cls(observationer=observationer, gamle_koter=gamle_koter, **kwargs)

    def til_dataframe(self) -> pd.DataFrame:
        """
        Oversætter udjævningsresultater fra det interne format til dataframe

        Den returnerede dataframe har samme kolonnenavne som "Punktoversigt"-
        arkdefinitionen. Der bruges kun den delmængde af kolonnerne som er relevante for
        nye koter.
        Dvs. at der ignoreres kolonnerne "uuid", "System" og "Udelad publikation". Disse
        kolonner skal man selv udfylde bagefter.
        """

        df_nye = pd.DataFrame(
            [astuple(x) for x in self.nye_koter],
            columns=("Punkt", "Ny kote", "Hvornår", "Ny σ", "Fasthold", "Nord", "Øst"),
        )

        df_gamle = pd.DataFrame(
            [astuple(x) for x in self.gamle_koter],
            columns=("Punkt", "Kote", "Hvornår", "σ", "Fasthold", "Nord", "Øst"),
        )
        df_nye = df_nye.set_index("Punkt")
        df_gamle = df_gamle.set_index("Punkt")

        # Beregn tid gået i antal år
        dt = (df_nye["Hvornår"] - df_gamle["Hvornår"]).apply(
            lambda t: t.total_seconds()
        ) / (365.25 * 86400)

        # Fjern rækker hvor dt = 0. Dette gør så Opløft-kolonnen længere nede bliver NaN istedet for inf.
        dt = dt[dt != 0]

        # Beregn ændring i millimeter...
        Delta = (df_nye["Ny kote"] - df_gamle["Kote"]) * 1000.0

        # ...men vi ignorerer ændringer under mikrometerniveau
        Delta[abs(Delta) < 0.001] = 0

        # Konstruer ny dataframe. Index og kolonner er foreningsmængden af de to dataframes.
        # NULL værdier i df_nye udfyldes med værdier fra df_gamle (dvs Fasthold, Kote, σ, Nord, Øst)
        df_out = df_nye.combine_first(df_gamle)

        df_out["Fasthold"] = df_out["Fasthold"].replace(False, "")
        df_out["Fasthold"] = df_out["Fasthold"].replace(True, "x")

        # Opdater felter i arbejdssættet
        df_out["Δ-kote [mm]"] = Delta
        df_out["Opløft [mm/år]"] = Delta.div(dt)

        return df_out

    @cached_property
    def fastholdte(self) -> dict[PunktNavn, float]:
        """Find fastholdte punkter og koter til en beregning"""
        return {pkt.punkt: pkt.H for pkt in self.gamle_koter if pkt.fasthold}

    @cached_property
    def gyldighedstidspunkt(self) -> datetime:
        """Tid for sidste observation der har været brugt i beregningen"""
        return max([obs.dato for obs in self.observationer])

    @cached_property
    def opstillingspunkter(self) -> set[PunktNavn]:
        """Alle opstillingspunkter"""
        return {obs.fra for obs in self.observationer}

    @cached_property
    def sigtepunkter(self) -> set[PunktNavn]:
        """Alle sigtepunkter"""
        return {obs.til for obs in self.observationer}

    @cached_property
    def observerede_punkter(self) -> set[PunktNavn]:
        """Foreningsmængden af opstillings- og sigtepunkter"""
        return self.opstillingspunkter.union(self.sigtepunkter)

    def netanalyse(self) -> tuple[NivNet, list[NivSubnet], list[PunktNavn]]:
        """
        Konstruér netgraf og find ensomme punkter

        Nettet reduceres for de ensomme punkter, da ensomme punkter ikke kan estimeres i udjævningen.
        """

        # Find subnet
        # weakly connected er at "lade som om" grafen er undirected, og så finde connectede subnet.
        # component = subnet)
        subnet = [set(c) for c in nx.weakly_connected_components(self.digraf)]

        # For hvert subnet undersøger vi om der findes et fastholdt punkt
        ensomme_subnet = [list(subn) for subn in subnet if set(self.fastholdte.keys()).isdisjoint(subn)]

        # Punkterne i de ensomme subnet skal ikke med i netgrafen
        ensomme_punkter = set().union(*ensomme_subnet)
        net_uden_ensomme = self.digraf.copy()
        net_uden_ensomme.remove_nodes_from(ensomme_punkter)

        # Det behøves faktisk ikke at konvertere her da byg_netgeometri_og_singulære
        # faktisk virker med networkx Graph objektet, da Graph objekterne opfører sig som dicts
        net_uden_ensomme = nx.to_dict_of_lists(net_uden_ensomme)

         # Estimerbare punkter er dem som er observerede, men ikke ensomme eller fastholdte.
        estimerbare_punkter = list(set(net_uden_ensomme.keys()).difference(self.fastholdte.keys()))

        # Gem de estimerbare punkter så de kan bruges af motoren senere.
        self.estimerbare_punkter = estimerbare_punkter

        return net_uden_ensomme, ensomme_subnet, estimerbare_punkter

    @classmethod
    def find_subnet(cls, net: NivNet) -> list[NivSubnet]:
        """
        Find selvstændige net i et større net

        Antager at nettet er non-directional. Dvs. peger A på B, skal B også pege på A. Ellers
        kan resultaterne blive forskellige alt efter hvilket punkt som søgningen starter ud fra.

        Eksempel: A og B peger på hinanden, og A og C peger på hinanden. Man kan komme fra
        ethvert punkt til ethvert andet punkt.
        {
            A: [B,C]
            B: [A]
            C: [A]
        }

        A og B peger på hinanden, og C peger på A. Hvis søgningen starter i A eller
        B, vil C fremgå som et separat subnet da man ikke kan komme fra A eller B til C.
        Starter søgningen i C vil alle punkterne derimod fremgå i det samme subnet.
        {
            A: [B]
            B: [A]
            C: [A]
        }

        Bruger breadth first search (BFS).
        Baseret på materiale fra: https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/
        """

        # Funktion til breadth first search
        def bfs(net, besøgt, startpunkt, subnet: list = []):
            # Initialiser kø
            kø = deque()

            # Marker nuværende punkt som besøgt og føj til kø
            besøgt[startpunkt] = True
            kø.append(startpunkt)

            # Opbyg subnet
            subnet.append(startpunkt)

            # Loop over køen
            while kø:
                # Fjern nuværende punkt fra køen
                nuværende_punkt = kø.popleft()

                # Find naboer til nuværende punkt
                # Hvis en nabo ikke har været besøgt, marker den da som besøgt og føj til kø
                for nabo in net[nuværende_punkt]:
                    if not besøgt[nabo]:
                        besøgt[nabo] = True
                        kø.append(nabo)

                        # Opbyg subnet
                        subnet.append(nabo)

        besøgt = {punkt: False for punkt in net.keys()}
        liste_af_subnet = []
        for punkt in net.keys():
            if not besøgt[punkt]:
                subnet = []
                bfs(net, besøgt, punkt, subnet)
                liste_af_subnet.append(subnet)

        return liste_af_subnet

    @cached_property
    def digraf(self) -> nx.MultiDiGraph:
        """
        Byg en digraf ud fra observationerne

        Returnerer et networkx MultiDiGraph objekt som kan indeholde flere parallelle (deraf Multi),
        rettede (deraf Di(rectional)) linjer (kanter) mellem hvert punkt (knude).
        Hver kant i grafen har en nøgle som refererer til en InternNivObservation.
        """
        digraf = nx.MultiDiGraph()
        digraf.add_nodes_from(self.observerede_punkter)
        for k, obs in self._observationer.items():
            digraf.add_edge(obs.fra, obs.til, key=k)
        return digraf


    def præaggreger_observationer(self):
        """
        En anden tilgang er at præaggregere alle linjer. For hver linje mellem to punkter, regner
        man
        mean(frem), mean(tilbage), mean(deltaH) = (sum(frem) - sum(tilbage))/(N_frem+N_tilbage), mean(afstand), samt rho = mean(frem)-mean(tilbage)

        Ud fra disse kan man lave fx en geojson og markere de linjer som så skal indgå i polygonen, og summere op.
        summa_rho = sum ( rho_i )        , for alle i i polygonen
        lukkesum  = sum(mean(deltaH)_i)  , for alle i i polygonen
        lukkesum_frem    = sum(mean(frem)_i)
        lukkesum_tilbage = sum(mean(tilbage)_i)

        Dette er nok det bedste at gøre hvis man gerne vil analyse på arbitrære polygoner, da det kan gøres nemt i QGIS.
        Men så skal man selv være opmærksom i QGIS på at polygonen er lukket etc.

        Det er forresten ikke altid at
        lukkesum == (lukkesum_frem-lukkesum_tilbage)/2
        idet der vil være forskel de steder hvor der ikke er lige mange frem og tilbage observationer.


        """


        obs_aggr = defaultdict(lambda: defaultdict(dict))
        # Noget i den her stil, men det er ikke færdigt!!!
        for k, o in self._observationer.items():
            try:
                N = obs_aggr[o.fra][o.til]["N"]
                obs_aggr[o.fra][o.til]["dhmean"] = (obs_aggr[o.fra][o.til]["dhmean"]*N + o.deltaH)/(N+1)
                obs_aggr[o.fra][o.til]["N"] += 1
                obs_aggr[o.fra][o.til]["afstand"] += o.afstand
            except KeyError:
                obs_aggr[o.fra][o.til]["N"] = 1
                obs_aggr[o.fra][o.til]["dhmean"] = o.deltaH
                obs_aggr[o.fra][o.til]["afstand"] = o.afstand


        return obs_aggr


    def lukkesum(self, min_længde: int = 3, metode: str = "mcb", **kwargs) -> dict[tuple[PunktNavn], dict]:
        """
        Find polygoner og beregn lukkesummer

        Returnerer en dict hvor nøglerne er en tuple af punkter i polygonerne, og
        værdierne er de beregnde statistike parametre, herunder lukkesummer, pakket ind i
        endnu en dict.

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

        Med minimal forstås at antallet af kanter langs polygonerne i den fundne basis er
        minimeret (hvis hver kant har vægt=1).

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

        Ønsker man at beregne lukkesummen af en bestemt polygon kan man bruge
        `lukkesum_af_polygon` direkte.
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
        graf = nx.DiGraph(self.digraf).to_undirected(reciprocal=True)

        cykler = {
            tuple(kreds): self.lukkesum_af_polygon(kreds, lukket=True)
            for kreds in fun(graf, **kwargs)
            if len(kreds) >= min_længde
        }

        return cykler


    def lukkesum_af_polygon(self, kreds: list, lukket: bool = True) -> dict:
        """
        Beregn lukkesum og andre kvalitetsparametre for en nivellementspolygon

        En polygon er givet ved punkterne i `kreds`. Der tages gennemsnit af parallelle
        linjer.
        Det antages at `kreds` er en egentlig (lukket) kreds, dvs. at først og sidste
        punkt er forbundet. Sættes lukket=False angiver at kredsen er åben. Dette kan fx
        bruges til at analysere blinde linjer.

        Returnerer:
            summa_rho           : float
            lukkesum            : float
            delta_H_frem_sum    : float
            delta_H_tilb_sum    : float
            afstand_frem_sum    : float
            afstand_tilb_sum    : float
            rho                 : list[float]
            delta_H             : list[float]
            afstand             : list[float]

        **Eksempler**
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
        D-A : rho = -0.3    deltaH = -5.85  <--- det hele "reddes" af sidste linje, hvilket måske er urealistisk

        # Summa rho og lukkesum for frem og tilbage-nivellement.
        summa_rho = 0
        lukkesum = 0.3
        delta_H_frem_sum = 0.3
        delta_H_tilb_sum = -0.3

        # Lukkesum af blind linje
        > lukkesum_af_polygon([B,E,F], lukket=False)
        Returnerer:
        # Rho for hver linje
        B-E : rho = 0.1     deltaH = 2.45
        E-F : rho = 0.1     deltaH = 1.25

        # Summa rho og lukkesum for frem og tilbage-nivellement.
        summa_rho = 0.2
        lukkesum = 3.7
        delta_H_frem_sum =  3.8
        delta_H_tilb_sum = -3.6
        """
        def _hent_kant(knude, næste_knude) -> tuple[list, list]:
            """
            Hent alle linjer fra punkt til næste punkt i kredsen

            Da der kan være flere parallelle linjer tages der for robusthed gennemsnittet
            af de parallelle linjer. På den måde er det ligemeget om der er fx 2 frem og 1
            tilbage niv.
            Hvis der ikke er forbindelse mellem `knude` og `næste_knude` vil det udløse en
            KeyError, som så vil blive fanget. Her kan man vælge om den skal fejle eller
            ej. Det er lidt irriterende at den fejler hvis man er ved at regne på noget
            der tager lang tid.)
            """
            try:
                deltaH = [self._observationer[k].deltaH for k in self.digraf[knude][næste_knude].keys()]
                afstand = [self._observationer[k].afstand for k in self.digraf[knude][næste_knude].keys()]
                n = len(deltaH) # antallet af parallelle linjer
            except KeyError:
                print(f"Advarsel! Der er ikke forbindelse fra {knude} til {næste_knude}")
                deltaH = [float("nan")]
                afstand = [float("nan")]
                n = 0
            return np.mean(deltaH), np.mean(afstand), n

        delta_H_frem_sum = 0
        delta_H_tilb_sum = 0
        afstand_frem_sum = 0
        afstand_tilb_sum = 0
        rho = []
        deltaH =  []   # gennemsnitlig højdeforskel for hver observeret linje
        afstande = []  # gennemsnitlig afstand for hver linje


        knuder = kreds if lukket else kreds[:-1]
        næste_knuder = kreds[1:]+kreds[:1] if lukket else kreds[1:]

        for knude, næste_knude in zip(knuder, næste_knuder):

            frem_deltaH, frem_afstand, n_frem = _hent_kant(knude, næste_knude)
            tilb_deltaH, tilb_afstand, n_tilb = _hent_kant(næste_knude, knude)

            # Vi vægter de enkelte frem- og tilbage-observationerne lige meget.
            deltaH_mean  = (frem_deltaH*n_frem-tilb_deltaH*n_tilb)/(n_frem+n_tilb)
            afstand_mean = (frem_afstand*n_frem+tilb_afstand*n_tilb)/(n_frem+n_tilb)

            deltaH.append(deltaH_mean)
            rho.append(frem_deltaH + tilb_deltaH)
            afstande.append(afstand_mean)

            delta_H_frem_sum += frem_deltaH
            delta_H_tilb_sum += tilb_deltaH

            afstand_frem_sum += frem_afstand
            afstand_tilb_sum += tilb_afstand

        # Udregning af summa rho og epsilon/lukkesum kan gøres på to måder:
        # Metode 1
        # summa_rho = sum(rho)
        # epsilon   = sum(deltaH)
        #
        # Metode 2:
        # summa_rho = delta_H_frem_sum + delta_H_tilb_sum
        # epsilon   = (delta_H_frem_sum - delta_H_tilb_sum)/2
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
        #

        summa_rho = np.sum(rho)
        lukkesum = np.sum(deltaH)

        return dict(
            summa_rho=summa_rho,
            lukkesum=lukkesum,
            delta_H_frem_sum=delta_H_frem_sum,
            delta_H_tilb_sum=delta_H_tilb_sum,
            afstand_frem_sum=afstand_frem_sum,
            afstand_tilb_sum=afstand_tilb_sum,
            deltaH=deltaH,
            rho=rho,
            afstande=afstande,
        )

    @abstractmethod
    def udjævn(self):
        """Udjævn observationer"""
        pass

    @property
    @abstractmethod
    def filer(self) -> list:
        """En liste af filnavne som motoren producerer"""
        pass


class GamaRegn(RegneMotor):
    """
    Regnemotor som bruger GNU Gama til at lave nivellementberegninger.
    """

    def __init__(
        self,
        *,
        xml_in: str = None,
        xml_out: str = None,
        html_out: str = None,
        **kwargs,
    ):
        # Sætter først self.projektnavn
        super().__init__(**kwargs)

        # Hvis gama filnavne ikke er sat bruges projektnavnet
        self.xml_in = xml_in or f"{self.projektnavn}.xml"
        self.xml_out = xml_out or f"{self.projektnavn}-resultat.xml"
        self.html_out = html_out or f"{self.projektnavn}-resultat.html"

    @property
    def filer(self) -> list:
        """En liste af filer som Gama producerer"""
        return [self.xml_in, self.xml_out, self.html_out]

    @filer.setter
    def filer(self, nye_filnavne):
        """Sæt nye filnavne"""
        self.xml_in, self.xml_out, self.html_out = nye_filnavne

    def skriv_gama_inputfil(self):
        """
        Skriv gama-inputfil i XML-format
        """
        with open(self.xml_in, "wt") as gamafil:
            # Preambel
            gamafil.write(
                f"<?xml version='1.0' ?><gama-local>\n"
                f"<network angles='left-handed' axes-xy='en' epoch='0.0'>\n"
                f"<parameters\n"
                f"    algorithm='gso' angles='400' conf-pr='0.95'\n"
                f"    cov-band='0' ellipsoid='grs80' latitude='55.7' sigma-act='aposteriori'\n"
                f"    sigma-apr='1.0' tol-abs='1000.0'\n"
                f"/>\n\n"
                f"<description>\n"
                f"    Nivellementsprojekt {ascii(self.projektnavn)}\n"  # Gama kaster op over Windows-1252 tegn > 127
                f"</description>\n"
                f"<points-observations>\n\n"
            )

            # Fastholdte punkter
            gamafil.write("\n\n<!-- Fixed -->\n\n")
            for punkt, kote in self.fastholdte.items():
                gamafil.write(f"<point fix='Z' id='{punkt}' z='{kote}'/>\n")

            # Vi sorterer punkter til udjævning, så de ser pæne ud i Gama inputfilen.
            estimerede_punkter = sorted(self.estimerbare_punkter)
            gamafil.write("\n\n<!-- Adjusted -->\n\n")
            for punkt in estimerede_punkter:
                gamafil.write(f"<point adj='z' id='{punkt}'/>\n")

            # Observationer
            gamafil.write("<height-differences>\n")
            for obs in self.observationer:
                gamafil.write(
                    f"<dh from='{obs.fra}' to='{obs.til}' "
                    f"val='{obs.deltaH:+.6f}' "
                    f"dist='{obs.afstand:.5f}' stdev='{obs.spredning:.5f}' "
                    f"extern='{obs.id}'/>\n"
                )

            # Postambel
            gamafil.write(
                "</height-differences>\n"
                "</points-observations>\n"
                "</network>\n"
                "</gama-local>\n"
            )

    def kald_gama(self):
        """Udjævning via gama"""

        ret = subprocess.run(
            [
                "gama-local",
                self.xml_in,
                "--xml",
                self.xml_out,
                "--html",
                self.html_out,
            ]
        )

        if ret.returncode:
            if not Path(self.xml_out).is_file():
                raise UdjævningFejl(
                    """Beregning ikke gennemført. Kontroller om nettet er sammenhængende, og ved flere net om der mangler fastholdte punkter."""
                )
            # Hvis filen findes så bed bruger om at checke den.
            raise UdjævningFejl(f"Beregning ikke gennemført. Check {self.html_out}")

    def læs_gama_outputfil(self) -> list[InternKote]:
        """
        Læser output fra GNU Gama og returnerer relevante parametre til at skrive xlsx fil
        """
        with open(self.xml_out) as resultat:
            doc = xmltodict.parse(resultat.read())

        # Sammenhængen mellem rækkefølgen af elementer i Gamas punktliste (koteliste
        # herunder) og varianserne i covariansmatricens diagonal er uklart beskrevet:
        # I Gamas xml-resultatfil antydes at der skal foretages en ombytning.
        # Men rækkefølgen anvendt her passer sammen med det Gama præsenterer i
        # html-rapportudgaven af beregningsresultatet.
        koteliste = doc["gama-local-adjustment"]["coordinates"]["adjusted"]["point"]
        varliste = doc["gama-local-adjustment"]["coordinates"]["cov-mat"]["flt"]

        # Konverter til liste i tilfælde af der kun er blevet udjævnet ét punkt.
        if isinstance(koteliste, dict):
            koteliste = [koteliste]
        if isinstance(varliste, dict):
            varliste = [varliste]

        assert len(koteliste) == len(
            varliste
        ), "Mismatch mellem antal koter og varianser"

        nye_koter = []
        for punkt, var in zip(koteliste, varliste):
            nye_koter.append(
                InternKote(
                    punkt=punkt["id"],
                    dato=self.gyldighedstidspunkt,
                    H=float(punkt["z"]),
                    spredning=sqrt(float(var)),
                )
            )

        return nye_koter

    def udjævn(self):
        """Skriver gama input, kalder gama og læser gama output."""

        self.skriv_gama_inputfil()
        self.kald_gama()
        self.nye_koter = self.læs_gama_outputfil()


class DumRegn(RegneMotor):
    """Eksempel på en alternativ regnemotor"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def udjævn(self):
        self.nye_koter = self.gamle_koter

    @property
    def filer(self) -> list:
        """En liste af filer som DumRegn producerer"""
        return None


def _spredning(
    observationstype: str,
    afstand_i_m: float,
    antal_opstillinger: float,
    afstandsafhængig_spredning_i_mm: float,
    centreringsspredning_i_mm: float,
) -> float:
    """Apriorispredning for nivellementsobservation

    Fx.  MTL: spredning("mtl", 500, 3, 2, 0.5) = 1.25
         MGL: spredning("MGL", 500, 3, 0.6, 0.01) = 0.4243
         NUL: spredning("NUL", .....) = 0

    Rejser ValueError ved ukendt observationstype eller
    (via math.sqrt) ved negativ afstand_i_m.

    Negative afstandsafhængig- eller centreringsspredninger
    behandles som positive.

    Observationstypen NUL benyttes til at sammenbinde disjunkte
    undernet - det er en observation med forsvindende apriorifejl,
    der eksakt reproducerer koteforskellen mellem to fastholdte
    punkter
    """

    if "NUL" == observationstype.upper():
        return 0

    opstillingsafhængig = sqrt(antal_opstillinger * (centreringsspredning_i_mm**2))

    if "MTL" == observationstype.upper():
        afstandsafhængig = afstandsafhængig_spredning_i_mm * afstand_i_m / 1000
        return hypot(afstandsafhængig, opstillingsafhængig)

    if "MGL" == observationstype.upper():
        afstandsafhængig = afstandsafhængig_spredning_i_mm * sqrt(afstand_i_m / 1000)
        return hypot(afstandsafhængig, opstillingsafhængig)

    raise ValueError(f"Ukendt observationstype: {observationstype}")


def polygon_feature(
    punkter: dict[PunktNavn, InternKote],
    polygoner: dict[tuple[PunktNavn], dict],
    ):
    """
    for hver polygon tages laves en feature som indeholder de attributter givet.
    antager for nu at polygoner er lukkede
    """
    for polygon, attributter in polygoner.items():
        feature = {
            "type": "Feature",
            "properties": attributter,
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[punkter[pkt].øst, punkter[pkt].nord] for pkt in polygon+polygon[:1]]]
            }
        }

        yield feature

def skriv_polygoner_geojson(
    filnavn: str,
    punkter: dict[PunktNavn, InternKote],
    polygoner: dict[tuple[PunktNavn], dict],
):
    til_json = {
        "type": "FeatureCollection",
        "Features": list(polygon_feature(punkter, polygoner)),
    }
    geojson = json.dumps(til_json, indent=4)

    with open(filnavn, "wt") as polygonfil:
        polygonfil.write(geojson)
