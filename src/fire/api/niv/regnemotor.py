from collections import Counter, deque
from dataclasses import dataclass, asdict, fields, astuple
from datetime import datetime
from functools import cached_property
from math import (
    hypot,
    sqrt,
)
from pathlib import Path
import subprocess
import xmltodict

import pandas as pd

from fire.api.model import (Observation, GeometriskKoteforskel)

class UdjævningFejl(Exception):
    ...

class UdjævningResultat():
    ...

@dataclass
class InternNivObservation:
    "Baseklasse for almindelige, ukorrelerede nivellementobservationer"
    fra: str
    til: str
    dato: datetime
    multiplicitet: int
    afstand: float
    deltaH: float
    spredning: float
    id: str # kan bruges til journalnummeret, eller observations-id fra FIRE

@dataclass
class InternKote:
    "Baseklasse for koter som enten indgår som input eller output til en beregning"
    punkt: str # kan både bruge ident, database id, eller uuid.
    H: float
    dato: datetime
    spredning: float
    fasthold: bool = False
    nord: float = None
    øst: float  = None

class RegneMotor(object):
    """
    RegneMotor klassen er et intermediate niveau (adapteren) som oversætter fra fx
    geojson, query-resultat eller excel-ark til internt format.

    Det interne format skal være uafhængigt af databasen! Dvs. det skal fx ikke være
    nødvendigt at "fra_ident" er en gyldig ident i databasen.

    child-klasserne (GamaRegn) skal så bruge det interne format udelukkende, og altså være
    ligeglad med om data kommer fra en query eller geojson.

    Det samme gælder for beregningsresultaterne. Output fra de forskellige
    beregningsmotorer skal oversættes til internt format, som kan bruges på en ensartet
    måde.
    Dog kan noget beholdes i child-klasserne, fx html-output fra gama, som man så kan bruge

    """
    # input
    observationer: list[InternNivObservation]
    gamle_koter: list[InternKote] # den her er i princippet ikke nødvendig. Har kun brug for de fastholdte.
    nye_koter: list[InternKote]
    # fastholdte_punkter: list[str] # en liste af fastholdte punkt-identer. punkterne skal være indeholdt i InternKote og InternNivObservation

    udjævnede_koter: list[float]

    def __init__(self, observationer, gamle_koter):
        self.observationer = observationer
        self.gamle_koter = gamle_koter

    @classmethod
    def fra_geojson(cls, ):
        "Oversæt fra geojson til internt format"
        # Vi har ikke et fast geojson format for observationer. Så kommer denne ikke bare til at efterligne det interne format?
        observationer = ...
        koter = ...
        regnemotor = cls(observationer, koter)
        raise NotImplementedError

    @classmethod
    def fra_query(cls, observationer: list[Observation]) -> "RegneMotor":
        "Oversæt fra en liste af sqlalchemy objekter til internt format"
        observationer = ...
        koter = ...
        regnemotor = cls(observationer, koter)
        raise NotImplementedError

    @classmethod
    def fra_dataframe(cls, observationer_df: pd.DataFrame, punkter_df: pd.DataFrame, *args, **kwargs) -> "RegneMotor":
        "Oversæt fra regneark til internt format"
        # self._punkter_df = punkter_df
        observationer = []
        for i, obs in observationer_df.iterrows():
            # først beregn spredning
            spredning=_spredning(obs["Type"], obs["L"], obs["Opst"], obs["σ"], obs["δ"])

            observationer.append(
                InternNivObservation(
                    fra=obs["Fra"],
                    til=obs["Til"],
                    dato=obs["Hvornår"].to_pydatetime(),
                    multiplicitet=obs["Opst"],
                    afstand=obs["L"],
                    deltaH=obs["ΔH"],
                    spredning=spredning,
                    id = obs["Journal"],
                )
            )

        gamle_koter = []
        for i, pkt in punkter_df.iterrows():
            gamle_koter.append(
                InternKote(
                    punkt = pkt["Punkt"],
                    fasthold=(True if pkt["Fasthold"] else False),
                    dato = pkt["Hvornår"].to_pydatetime(),
                    H = pkt["Kote"],
                    spredning=pkt["σ"],
                    nord=pkt["Nord"],
                    øst=pkt["Øst"],
                )
            )

        # returner instans af den kaldende klasse
        return cls(observationer=observationer, gamle_koter=gamle_koter, *args, **kwargs)


    def til_dataframe(self) -> pd.DataFrame:
        """ Oversætter fra det interne format til dataframe """

        df_out = pd.DataFrame(
            [astuple(x) for x in self.nye_koter],
            columns = ("Punkt", "Ny kote", "Hvornår", "Ny σ","Fasthold", "Nord", "Øst")
            )
        df_out["Fasthold"]=df_out["Fasthold"].replace(False, "")
        df_out["Fasthold"]=df_out["Fasthold"].replace(True, "x")

        return df_out

    @cached_property
    def fastholdte(self) -> dict[str,float]:
        """Find fastholdte punkter og koter til en beregning"""
        return {pkt.punkt:pkt.H for pkt in self.gamle_koter if pkt.fasthold}

    @cached_property
    def gyldighedstidspunkt(self) -> datetime:
        """Tid for sidste observation der har været brugt i beregningen"""
        return max([obs.dato for obs in self.observationer])

    @cached_property
    def opstillingspunkter(self) -> set:
        """Alle opstillingspunkter"""
        return {obs.fra for obs in self.observationer}

    @cached_property
    def sigtepunkter(self) -> set:
        """Alle sigtepunkter"""
        return {obs.til for obs in self.observationer}

    @cached_property
    def observerede_punkter(self) -> set:
        return self.opstillingspunkter.union(self.sigtepunkter)

    def netgraf(self) -> tuple[list, list[list], set, tuple]:
        "Konstruér netgraf og find sammenhængende net og ensomme punkter"

        fastholdte_punkter = tuple(self.fastholdte.keys())
        # hvis der slet ikke er nogen fastholdte, så brug det mest observerede punkt. <--- KREBSLW: Det er mærkeligt!
        if len(fastholdte_punkter) == 0:
            alle_obs = list(self.opstillingspunkter) + list(self.sigtepunkter) # obs_fra og obs_til er allerede sets, så hvert punkt kan kun fremgå 2 gange, så de facto tager vi bare et random punkt..
            c = Counter(alle_obs)
            fastholdte_punkter = tuple([c.most_common(1)[0][0]])

        net = self.opbyg_net()
        subnet = self.analyser_subnet(net)

        # IDEA: Måske kan man også gøre så den finder alle de observationer som indgår i hvert subnet, og ikkekun punkterne.
        # Dvs. I stedet for at undersøge om "vertex"erne hænger sammen, undersøges om "edges"ne hænger sammen.

        ensomme_punkter = set()
        # Undersøg om nettet består af flere ikke-sammenhængende subnet.
        # For hvert subnet tjekker vi om det indeholder et fastholdt punkt.
        fastholdte_i_subnet = [None for _ in subnet]
        for i, subnet_ in enumerate(subnet):
            for punkt in fastholdte_punkter:
                if punkt in subnet_:
                    fastholdte_i_subnet[i] = punkt
                    break
            else:
                ensomme_punkter.update(subnet_)

        # De ensomme punkter skal ikke med i netgrafen
        for punkt in ensomme_punkter:
            net.pop(punkt, None)

        return net, subnet, ensomme_punkter, fastholdte_i_subnet

    def opbyg_net(self) -> dict[set]:
        """
        Konstruerer graf med dict[set] som markerer forbindelser mellem punkter.
        """

        net = {p:set() for o in self.observationer for p in (o.fra, o.til)}

        for obs in self.observationer:
            net[obs.til].add(obs.fra)
            net[obs.fra].add(obs.til)

        return net

    def analyser_subnet(self, net: dict[set]) -> list[list]:
        """
        Find selvstændige net i et større net

        Arbejder med non-directional graphs.
        {
            A: [B,C,D]
            B: [A,E]
            C: [], <-- det er ligemeget om C peger på A, når A allerede peger på C.
            D: [A],

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

    # Nedenfor kommer abstrakte metoder
    def udjævn() -> UdjævningResultat:
        raise NotImplementedError("Dette er en abstract metode. Brug en underklasse")


class GamaRegn(RegneMotor):
    """
    Regnemotor som bruger GNU Gama til at lave nivellementberegninger.
    """
    def __init__(
        self,
        projektnavn: str,
        kontrol: bool=None,
        *args,
        **kwargs
    ):
        self.projektnavn = projektnavn
        # you take my...
        self.kontrol = kontrol

        super().__init__(*args, **kwargs)

    def skriv_gama_inputfil(self):
        """
        Skriv gama-inputfil i XML-format
        """
        with open(f"{self.projektnavn}.xml", "wt") as gamafil:
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

            # Punkter til udjævning
            estimerede_punkter = self.observerede_punkter-set(self.fastholdte.keys())
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


    def læs_gama_output(self) -> tuple[list[str], list[float], list[float]]:
        """
        Læser output fra GNU Gama og returnerer relevante parametre til at skrive xlsx fil
        """
        with open(f"{self.projektnavn}-resultat.xml") as resultat:
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

        assert len(koteliste) == len(varliste), "Mismatch mellem antal koter og varianser"

        # Dette kan laves som list comprehension men bliver måske svært at læse?
        nye_koter = []
        for punkt, var in zip(koteliste, varliste):
            nye_koter.append(
                InternKote(
                    punkt = punkt["id"],
                    dato = self.gyldighedstidspunkt,
                    H = float(punkt["z"]),
                    spredning=sqrt(float(var)),
                )
            )

        self.nye_koter=nye_koter
        return

    def udjævn(self, xml_filnavn: str, html_filnavn: str):
        """ Udjævning via gama """

        ret = subprocess.run(
            [
                "gama-local",
                f"{xml_filnavn}.xml",
                "--xml",
                f"{xml_filnavn}-resultat.xml",
                "--html",
                html_filnavn,
            ]
        )

        if ret.returncode:
            if not Path(f"{xml_filnavn}-resultat.xml").is_file():
                raise UdjævningFejl

        return ret


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


def main():
    g = GeometriskKoteforskel(value1=1)
    breakpoint()
    # g.koteforskel = 1
    pass

if __name__ == "__main__":
    main()
