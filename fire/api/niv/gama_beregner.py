"""
Modul med funktionalitet til at beregne netværk med GNU GAMA.

"""

from dataclasses import dataclass
from abc import ABC
import subprocess
from pathlib import Path
import math
from typing import (
    Any,
    Iterable,
    Final,
    Optional,
)
import datetime as dt

import xmltodict

from fire.api.niv import beregn


FASTHOLD: Final[str] = "x"
FASTHOLD_IKKE: Final[str] = ""


@dataclass
class Observation:
    journal: Optional[str]
    fra: Optional[str]
    til: Optional[str]
    koteforskel: Optional[float]
    nivlaengde: Optional[float]
    opstillinger: Optional[int]
    sigma: Optional[float]
    delta: Optional[float]
    type: Optional[str]

    def spredning(self) -> float:
        return beregn.spredning(
            self.type, self.nivlaengde, self.opstillinger, self.sigma, self.delta
        )


@dataclass
class Punkt:
    id: Optional[str]
    fasthold: Optional[str]
    kote: Optional[float]
    sigma: Optional[float] = None
    gyldig: Optional[dt.datetime] = None


@dataclass
class InternalData:
    # Data til GNU Gama inddata-fil
    projektnavn: str
    projektbeskrivelse: str
    observationer: Iterable[Observation]
    fastholdte: dict[str, float]
    estimerede: Iterable[str]
    gyldighedsdato: dt.datetime
    # Interne felter
    _filnavn_gama_inddata: Optional[str] = None
    _filnavn_gama_uddata: Optional[str] = None
    _filnavn_gama_rapport: Optional[str] = None
    # Resultat
    resultat: Optional[Iterable[Punkt]] = None


@dataclass
class Fejl:
    prog: str = ""
    besk: str = ""


class DataMapper(ABC):
    def til_intern(self, data: Any) -> InternalData:
        pass

    def fra_intern(self, data: InternalData) -> Any:
        pass


class GamaBeregner:
    """
    GamaBeregner lader en oversætter konvertere brugerens egne data til et internt format, der bruges af beregneren til at oprette en Gama-input-fil.

    Når resultatet er beregnet, kan brugerens egen oversætter oversætte data fra klassen og resultatfilen tilbage til brugerens ønskede format.

    """

    def __init__(self, dm: DataMapper):
        self._dm: DataMapper = dm
        self._data: InternalData = None
        self._fejl: Fejl = None

    def _check_status(self):
        if self._fejl is None:
            return
        raise RuntimeError(self._fejl)

    def _forbehandling(self):
        assert self._data is not None, f"Data ikke indlæst."
        self._data._filnavn_gama_inddata = f"{self._data.projektnavn}.xml"
        self._data._filnavn_gama_uddata = f"{self._data.projektnavn}-resultat.xml"
        self._data._filnavn_gama_rapport = f"{self._data.projektnavn}-resultat.html"

    def _opret_gama_inddatafil(self):
        assert self._data is not None, f"Data ikke indlæst."
        indhold = gama_inddata(
            self._data.projektbeskrivelse,
            self._data.fastholdte,
            self._data.estimerede,
            self._data.observationer,
        )
        # TODO (JOAMO): Kvalitetskontrol af filens indhold.
        with open(self._data._filnavn_gama_inddata, "wt") as gamafil:
            gamafil.write(indhold)

    def _kør_gama(self):
        assert self._data is not None, f"Data ikke indlæst."
        ifnavn = self._data._filnavn_gama_inddata
        ofnavn = self._data._filnavn_gama_uddata
        rapport = self._data._filnavn_gama_rapport
        assert Path(ifnavn).is_file(), f"Mangler inputfilen {ifnavn!r}"

        # TODO (JOAMO): Brug Popen og send output til log (evt. fil)
        ret = subprocess.run(
            [
                "gama-local",
                ifnavn,
                "--xml",
                ofnavn,
                "--html",
                rapport,
            ]
        )
        if ret.returncode == 0:
            return

        if not Path(ofnavn).is_file():
            self._fejl = Fejl(
                "Beregning ikke gennemført. "
                "Kontroller om nettet er sammenhængende, "
                "og ved flere net om der mangler fastholdte punkter."
            )
            return
        self._fejl = Fejl(f"Check {rapport}")

    def _efterbehandling(self):
        """
        Sammenhængen mellem rækkefølgen af elementer i Gamas punktliste (koteliste
        herunder) og varianserne i covariansmatricens diagonal er uklart beskrevet:

        *   I Gamas xml-resultatfil antydes at der skal foretages en ombytning.
        *   Men rækkefølgen anvendt her passer sammen med det Gama præsenterer i
            html-rapportudgaven af beregningsresultatet.

        """
        assert self._data is not None, f"Data ikke indlæst."

        # Læs resultater fra GNU Gamas outputfil
        with open(self._data._filnavn_gama_uddata) as fil:
            doc = xmltodict.parse(fil.read())

        koteliste = doc["gama-local-adjustment"]["coordinates"]["adjusted"]["point"]
        varliste = doc["gama-local-adjustment"]["coordinates"]["cov-mat"]["flt"]

        punkter = [punkt["id"] for punkt in koteliste]
        koter = [float(punkt["z"]) for punkt in koteliste]
        varianser = [float(var) for var in varliste]

        assert (
            len(punkter) == len(koter) == len(varianser)
        ), "Mismatch mellem antal punkter, koter og varianser"

        def fasthold_eller_ej(punkt_id: str) -> str:
            if punkt_id in self._data.fastholdte:
                return FASTHOLD
            return FASTHOLD_IKKE

        punkter = [
            Punkt(
                id=punkt_id,
                fasthold=fasthold_eller_ej(punkt_id),
                kote=ny_kote,
                sigma=math.sqrt(varians),
                gyldig=self._data.gyldighedsdato,
            )
            for punkt_id, ny_kote, varians in zip(punkter, koter, varianser)
        ]
        self._data.resultat = punkter

    def beregn(self, data):
        self._data = self._dm.til_intern(data)
        self._forbehandling()
        self._opret_gama_inddatafil()
        self._kør_gama()
        self._check_status()
        self._efterbehandling()

    @property
    def resultat(self):
        return self._dm.fra_intern(self._data)


def gama_inddata(
    projektbeskrivelse: str,
    fastholdte: dict[str, float],
    estimerede: Iterable[str],
    observationer: Iterable[Observation],
) -> str:
    """
    Opbyg indhold til GAMA input-fil.

    """
    # Om brugen af indbygget funktion `ascii()`: Gama kaster op over Windows-1252 tegn > 127
    preamble = f"""\
<?xml version='1.0' ?><gama-local>
<network angles='left-handed' axes-xy='en' epoch='0.0'>
<parameters
    algorithm='gso' angles='400' conf-pr='0.95'
    cov-band='0' ellipsoid='grs80' latitude='55.7' sigma-act='aposteriori'
    sigma-apr='1.0' tol-abs='1000.0'
/>

<description>
    {ascii(projektbeskrivelse)}
</description>
<points-observations>

"""
    # Fastholdte punkter
    fixed = "\n\n<!-- Fixed -->\n\n"
    for punkt, kote in fastholdte.items():
        fixed += f"<point fix='Z' id='{punkt}' z='{kote}'/>\n"

    # Punkter til udjævning
    adjusted = "\n\n<!-- Adjusted -->\n\n"
    for punkt in estimerede:
        adjusted += f"<point adj='z' id='{punkt}'/>\n"

    # Observationer
    observations = "<height-differences>\n"
    for observation in observationer:
        observations += (
            f"<dh from='{observation.fra}' "
            f"to='{observation.til}' "
            f"val='{observation.koteforskel:+.6f}' "
            f"dist='{observation.nivlaengde:.5f}' "
            f"stdev='{observation.spredning():.5f}' "
            f"extern='{observation.journal}'/>\n"
        )

    # Postambel
    postamble = """\
</height-differences>
</points-observations>
</network>
</gama-local>
"""
    return f"{preamble}{fixed}{adjusted}{observations}{postamble}"
