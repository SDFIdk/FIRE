"""
System Til Ekstraktion Af Koordinater fra Bernese (STEAK Bernese)
"""

from dataclasses import dataclass
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from typing import Union
import re

"""
Dataklasser for et samlet sæt af beregninger (for en uge?), indsamlet fra ADDNEQ, CRD og COV output-filer fra
Bernese.
"""


@dataclass(order=True, eq=True)
class Kovarians:
    """
    Kovariansdata (XX,YY,ZZ,XY,XZ,YZ) indsamlet fra en datalinje i COV-output fil.
    """

    xx: float
    yy: float
    zz: float
    yx: float
    zx: float
    zy: float


@dataclass(order=True, eq=True)
class Koordinat:
    """
    XYZ-koordinat indsamlet fra en datalinje i CRD-output fil. Ikke at forveksle med fire.api.model.Koordinat
    """

    x: float = None
    y: float = None
    z: float = None
    sx: float = None
    sy: float = None
    sz: float = None


@dataclass(order=True, eq=True)
class RMS:
    """
    RMS spredning (North, East, Up) og residualer indsamlet fra ADDNEQ-output fil.
    """

    n_residualer: list
    e_residualer: list
    u_residualer: list
    n: float = None
    e: float = None
    u: float = None


@dataclass(order=True, eq=True)
class Station:
    """
    Dataklasse, der indeholder udvalgte data fra ADDNEQ, CRD og COV output for en enkelt station
    """

    navn: str
    koordinat: Koordinat
    kovarians: Kovarians
    spredning: RMS
    obsstart: datetime
    obsslut: datetime
    flag: str = None

    @property
    def obslængde(self):
        """
        Returnerer forskellen (af typen timedelta) mellem observationens begyndelses- og sluttidspunkt
        """
        if self.obsslut and self.obsstart:
            return self.obsslut - self.obsstart
        return None


def crdcov_parse_weekline(line: str) -> int:
    """
    Parse GNSS-ugenummer fra CRD eller COV, linje 1
    En typisk linje 1 ser således ud:

    "COMB week 1273                                                   01-OCT-13 12:02"

    Vi splitter derfor linjen til en liste af ord og vælger det tredje ord = ugenummeret 1273
    """
    params = line.split()
    week = re.sub("[^0-9]", "", params[2])
    return int(week)


def crd_parse_epochdatumline(line: str) -> dict:
    """
    Parse datum og epoke fra CRD, linje 3
    En typisk linje 3 ser således ud:

    "LOCAL GEODETIC DATUM: IGb08             EPOCH: 2016-03-04 00:00:00"

    Vi splitter derfor linjen til en liste af ord og vælger det tredje ord : datum IGb08 og femte og sjette ord :
    epoke 2016-03-04 00:00:00
    """
    params = line.split()
    datum = params[3]
    epoch = params[5] + " " + params[6]
    return dict(zip_longest(["DATUM", "EPOCH"], [datum, epoch]))


def crd_parse_dataline(line: str) -> dict:
    """
    Parse datasektionen fra en CRD-linje og udtræk observationsfelterne - vi skal senere bruge navn, XYZ og flag

    Linjerne følger efter denne header:
    NUM  STATION NAME           X (M)          Y (M)          Z (M)     FLAG

    Eks.:
    11  MYGD              3379477.56441   598261.61665  5358170.54980    A
    12  ONSA              3370658.55007   711877.13000  5349786.94625    W
    13  POTS              3800689.64574   882077.37588  5028791.31542    W
    14  RIGA              3183899.20266  1421478.48081  5322810.79151
    """
    params = line.split()
    return dict(zip_longest(["NR", "STATION NAME", "X", "Y", "Z", "FLAG"], params))


def addneq_parse_observationline(line: str) -> dict:
    """
    Parse en observationslinje fra en ADDNEQ-fil, udtræk stationsnavn, samt observationens begyndelse og ende
    Her matcher overskrifterne ikke 1-1 på whitespace-adskilte kolonner, så det er nødvendigt at benytte indeks på
    linjer af fast bredde

    Linjerne følger efter denne header:
    Sol Station name         Typ Correction  Estimated value  RMS error   A priori value Unit    From                To                  MJD           Num Abb

    Eks.:

      1 BOR1                   X    0.00216    3738358.26267    0.00035    3738358.26051 meters  2016-03-03 00:00:00 2016-03-04 23:59:30 57450.99983     1 #CRD
      1 BOR1                   Y    0.00056    1148173.88492    0.00015    1148173.88436 meters  2016-03-03 00:00:00 2016-03-04 23:59:30 57450.99983     2 #CRD
      1 BOR1                   Z    0.00187    5021815.87371    0.00046    5021815.87184 meters  2016-03-03 00:00:00 2016-03-04 23:59:30 57450.99983     3 #CRD
      1 BUDP                   X    0.00011    3513638.07857    0.00034    3513638.07846 meters  2016-03-03 00:00:00 2016-03-04 23:59:30 57450.99983     4 #CRD
      1 BUDP                   Y    0.00020     778956.56481    0.00015     778956.56461 meters  2016-03-03 00:00:00 2016-03-04 23:59:30 57450.99983     5 #CRD

    """
    station = line[5:9]
    komponent = line[28]
    koordinat = line[43:57]
    obsfra = line[94:113]
    obstil = line[114:133]
    spredning = line[61:68]
    return dict(
        zip_longest(
            ["STATION NAME", "TYPE", "VALUE", "FROM", "TO", "RMS_ERROR"],
            [station, komponent, koordinat, obsfra, obstil, spredning],
        )
    )


def addneq_parse_stddevline(line: str) -> dict:
    """
    Parse en linje med RMS-spredning fra en ADDNEQ-fil, udtræk stationsnavn, samt retning (N/E/U), spredning og
    derefter et vilkårligt antal døgnresidualer.
    En serie linjer kan se således ud:

    GESR             N    0.07      0.02   -0.06
    GESR             E    0.10     -0.00   -0.10
    GESR             U    0.23     -0.10    0.20

    """
    params = line.split()
    return {
        "STATION NAME": params[0],
        "DIRECTION": params[1],
        "STDDEV": params[2],
        "RES": params[3:],
    }


def cov_parse_dataline(line: str) -> dict:
    """
    Parse datasektionen fra en COV-linje og udtræk observationsfelterne - station 1 og 2, deres koordinatpar-labels
    og matriceelement.

    En sektion kan begynde sådan her:

    STATION 1        XYZ    STATION 2        XYZ FLG    MATRIX ELEMENT

    BOR1              X     BOR1              X         0.9326975128D-01

    BOR1              Y     BOR1              X         0.2008472992D-01
    BOR1              Y     BOR1              Y         0.1634563313D-01

    BOR1              Z     BOR1              X         0.9670543502D-01
    BOR1              Z     BOR1              Y         0.2236056402D-01
    BOR1              Z     BOR1              Z         0.1607287392D+00

    BUDP              X     BOR1              X        -0.1649457919D-02

    """
    params = line.split()
    return dict(
        zip_longest(
            ["STATION 1", "XYZ 1", "STATION 2", "XYZ 2", "MATRIX ELEMENT"], params
        )
    )


class BerneseSolution(dict):
    gnss_uge: int = None
    epoke: datetime = None
    a_posteriori_RMS: None
    datum: str = None

    def __init__(
        self,
        addneq_fil: Union[str, Path],
        crd_fil: Union[str, Path],
        cov_fil: Union[str, Path] = None,
    ) -> None:
        """
        Læs og ekstraher Bernese data fra et sæt af matchende ADDNEQ, CRD og (valgfrit) COV filer

        Pointen er at skabe en liste med Station'er baseret på indholdet af filerne og tilknytte koordinater (CRD-fil),
        kovarians matrix (COV-fil) og andre informationer (ADDNEQ-filen)

        addneq_fil: sti til en Bernese ADDNEQ fil (påkrævet)
        crd_fil   : sti til en Bernese CRD (påkrævet)
        cov_fil   : sti til en Bernese COV (valgfri)

        """
        super().__init__()

        # konverter til Path's - antag input er str hvis ikke Path
        if not isinstance(addneq_fil, Path):
            addneq_fil = Path(addneq_fil)

        if not isinstance(crd_fil, Path):
            crd_fil = Path(crd_fil)

        if cov_fil and not isinstance(cov_fil, Path):
            cov_fil = Path(cov_fil)

        # Tjek at filerne er til stede
        if not addneq_fil.exists():
            raise FileNotFoundError(f"ADDNEQ-fil {addneq_fil} ikke fundet!")

        if not crd_fil.exists():
            raise FileNotFoundError(f"CRD-fil {crd_fil} ikke fundet!")

        if cov_fil and not cov_fil.exists():
            raise FileNotFoundError(f"COV-fil {cov_fil} ikke fundet")

        # Begynd med at indlæse og opbygge stationer fra CRD-fil
        with open(crd_fil, "r") as crd:
            self.crd_parse(crd.readlines())

        # Dernæst tilføj kovariansmatricer fra COV-fil hvis den eksisterer
        if cov_fil:
            with open(cov_fil, "r") as cov:
                self.cov_parse(cov.readlines())

        # Endelig tilføjes observationslængde og spredning fra ADDNEQ-fil
        with open(addneq_fil, "r") as addneq:
            self.addneq_parse(addneq.readlines())

    def __repr__(self):
        s = f"BerneseSolution(gnss_uge={self.gnss_uge}, epoke={self.epoke}, datum={self.datum}, stationer="
        s += str(list(self.keys())) + ")"

        return s

    def crd_parse(self, crd_data: list) -> None:
        """
        Parse header og datalinjerne fra en koordinat (CRD) fil og opret stationer
        """
        for linje_nr, line in enumerate(crd_data, start=1):
            if linje_nr == 1:  # header med ugenr/comb week
                self.gnss_uge = crdcov_parse_weekline(line)
                continue
            if linje_nr == 3:  # header med datum og epoke
                headerlinje = crd_parse_epochdatumline(line)
                self.datum = headerlinje["DATUM"]
                self.epoke = datetime.strptime(
                    headerlinje["EPOCH"], "%Y-%m-%d %H:%M:%S"
                )
                continue
            if linje_nr < 7 or line.isspace():  # data begynder på linje 7 i CRD-filer
                continue
            datalinje = crd_parse_dataline(line)  # tabel med koordinater og flag
            station = Station(
                navn=datalinje["STATION NAME"],
                flag=datalinje["FLAG"],
                koordinat=Koordinat(),
                kovarians=None,
                spredning=None,
                obsstart=None,
                obsslut=None,
            )  # koordinat, kovarians, spredning og observationstider bliver sat senere
            self[datalinje["STATION NAME"]] = station

    def cov_parse(self, cov_data: list) -> None:
        """
        Parse datalinjerne fra en kovarians (COV) fil og indsæt dem i resultatset
        """
        linje_nr = 0
        temp_table = {station: {} for station in self}
        for line in cov_data:
            linje_nr = linje_nr + 1
            if linje_nr == 1:
                if crdcov_parse_weekline(line) != self.gnss_uge:
                    raise ValueError("Forskellige GNSS uger i CRD og COV!")
            if linje_nr < 12 or line.isspace():  # data begynder på linje 12 i COV-filer
                continue
            temp = cov_parse_dataline(line)
            if (
                temp["STATION 1"] == temp["STATION 2"]
            ):  # data er kun interessant hvis det er samme station
                koordinatpar = temp["XYZ 1"] + temp["XYZ 2"]
                # vi er nødt til at erstatte D med E pga. Fortran/Python forskelle i videnskabelig notation
                temp_table[temp["STATION 1"]][koordinatpar] = float(
                    temp["MATRIX ELEMENT"].replace("D", "E")
                )
        for station, covarians in temp_table.items():
            if not covarians:
                continue  # ignorer stationer fra CRD som vi ikke har kovarianser for i COV-filen
            self[station].kovarians = Kovarians(
                xx=covarians["XX"],
                yy=covarians["YY"],
                zz=covarians["ZZ"],
                yx=covarians["YX"],
                zx=covarians["ZX"],
                zy=covarians["ZY"],
            )

    def addneq_parse(self, addneq_data: list) -> None:
        """
        Parse linjerne fra en ADDNEQ fil og indsæt dem i resultatset
        """
        # Vi finder observationslængdeafsnittet ved at finde indeks ud fra overskriften
        første_sektion_begyndelse = (
            addneq_data.index(
                " Sol Station name         Typ Correction  Estimated value  RMS error   A priori value Unit    From                To                  MJD           Num Abb  \n"
            )
            + 2
        )
        # Vi kan desværre ikke antage rækkefølge på sektionerne, men denne sektion ser ud til at være færdig når den
        # efterfølges af 1-2 tomme linjer
        første_sektion_ende = addneq_data.index("\n", første_sektion_begyndelse)
        første_sektion = addneq_data[første_sektion_begyndelse:første_sektion_ende]

        # Så skal der udtrækkes koordinater og observationslængder fra den første
        # udklippede sektion. Data for hver station strækker sig over tre linjer,
        # hvor hver linjer repræsenterer en koordinatkomponent.
        for linje in første_sektion:
            if not linje.isspace():  # skip evt. tomme linjer
                observation = addneq_parse_observationline(linje)
                station = observation["STATION NAME"]

                if self[station].obsstart is None:
                    self[station].obsstart = datetime.strptime(
                        observation["FROM"], "%Y-%m-%d %H:%M:%S"
                    )
                    self[station].obsslut = datetime.strptime(
                        observation["TO"], "%Y-%m-%d %H:%M:%S"
                    )

                if observation["TYPE"] == "X":
                    self[station].koordinat.x = float(observation["VALUE"])
                    self[station].koordinat.sx = float(observation["RMS_ERROR"])
                if observation["TYPE"] == "Y":
                    self[station].koordinat.y = float(observation["VALUE"])
                    self[station].koordinat.sy = float(observation["RMS_ERROR"])
                if observation["TYPE"] == "Z":
                    self[station].koordinat.z = float(observation["VALUE"])
                    self[station].koordinat.sz = float(observation["RMS_ERROR"])

        # Det samme gør sig ikke gældende med afsnittet om spredninger - der er som regel en tom linje efter hver
        # station, men der synes overskriften altid at være den samme
        # Dog er denne sektion til tider slet ikke til stede - i så fald skipper vi den
        try:
            anden_sektion_begynd = (
                addneq_data.index(" Comparison of individual solutions:\n") + 3
            )
            anden_sektion_ende = addneq_data.index(
                " Variance-covariance scaling factors:\n"
            )
            anden_sektion = addneq_data[anden_sektion_begynd:anden_sektion_ende]

            # Og spredning fra den anden udklippede sektion
            stations_rms = {}
            for station in self:
                stations_rms[station] = {}  # opret en tabel med navne fra CRD parsing
            for linje in anden_sektion:
                if not linje.isspace():  # skip evt. tomme linjer
                    spredningslinje = addneq_parse_stddevline(linje)
                    stations_rms[spredningslinje["STATION NAME"]][
                        spredningslinje["DIRECTION"]
                    ] = spredningslinje["STDDEV"]
                    stations_rms[spredningslinje["STATION NAME"]][
                        spredningslinje["DIRECTION"] + "RES"
                    ] = spredningslinje["RES"]
            for station in stations_rms:
                if not stations_rms[station]:  # spring over stationer uden værdier
                    continue
                n = stations_rms[station]["N"]
                e = stations_rms[station]["E"]
                u = stations_rms[station]["U"]
                nres = stations_rms[station]["NRES"]
                eres = stations_rms[station]["ERES"]
                ures = stations_rms[station]["URES"]
                rms = RMS(
                    n=n,
                    e=e,
                    u=u,
                    n_residualer=nres,
                    e_residualer=eres,
                    u_residualer=ures,
                )
                self[station].spredning = rms
        except ValueError:
            pass

        # Endelig skal vi bestemme RMS-spredning a posteriori fra en linje et tredje sted
        tredje_sektion_begyndelse = (
            addneq_data.index(" Statistics:                           \n")
            + 13  # trettende linje efter overskriften finder vi 'A posteriori RMS of unit weight'
        )
        self.a_posteriori_RMS = float(addneq_data[tredje_sektion_begyndelse].split()[6])
