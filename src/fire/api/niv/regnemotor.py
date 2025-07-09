from abc import ABC, abstractmethod
from collections import Counter, deque
from dataclasses import dataclass, astuple
from datetime import datetime
from functools import cached_property
from math import (
    hypot,
    sqrt,
    isnan,
)
from pathlib import Path
import subprocess
from typing import Self
import xmltodict

import pandas as pd

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
        self.observationer = observationer
        self.gamle_koter = gamle_koter
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
        net = self.opbyg_net()

        # Undersøg om nettet består af flere ikke-sammenhængende subnet.
        subnet = self.find_subnet(net)

        # For hvert subnet undersøger vi om der findes et fastholdt punkt
        ensomme_subnet = [
            subn for subn in subnet if set(self.fastholdte.keys()).isdisjoint(subn)
        ]

        # Punkterne i de ensomme subnet skal ikke med i netgrafen
        ensomme_punkter = set().union(*ensomme_subnet)
        for punkt in ensomme_punkter:
            net.pop(punkt, None)

        # Estimerbare punkter er dem som er observerede, men ikke ensomme eller fastholdte.
        estimerbare_punkter = list(set(net.keys()).difference(self.fastholdte.keys()))

        # Gem nettet og de estimerbare punkter så de kan bruges af motoren senere.
        self.net = net
        self.estimerbare_punkter = estimerbare_punkter

        return net, ensomme_subnet, estimerbare_punkter

    def opbyg_net(self) -> NivNet:
        """
        Konstruer non-directed graf som markerer forbindelser mellem punkter.
        """

        net = {p: set() for p in self.observerede_punkter}

        for obs in self.observationer:
            net[obs.til].add(obs.fra)
            net[obs.fra].add(obs.til)

        return net

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
