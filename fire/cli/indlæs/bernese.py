import getpass
from typing import List
from io import BytesIO
from zipfile import ZipFile

import click
from rich.table import Table
from rich.console import Console
from rich import box
from sqlalchemy.exc import NoResultFound, IntegrityError

import fire.cli
from fire.cli import firedb
from fire.io.bernese import BerneseSolution
from fire.api.model import (
    GNSSTidsserie,
    Koordinat,
    Beregning,
    Observation,
    ObservationsLængde,
    KoordinatKovarians,
    ResidualKovarians,
    Punkt,
    Srid,
)
from fire.cli.niv import bekræft
from . import indlæs

SRIDINDEX = {
    "IGb08": "EPSG:9015",
    "IGS14": "EPSG:8227",
}


def find_relevante_punkter(
    solution: BerneseSolution,
    ignorer_station: List[str],
    ignorer_advarsler: bool,
) -> List[Punkt]:
    """
    Find relevante punkter blandt de mulige i den givne BerneseSolution.
    """
    relevante_punkter = [
        station.navn for station in solution.values() if station.flag == "A"
    ]

    for ignoreret_station in ignorer_station:
        if ignoreret_station in relevante_punkter:
            relevante_punkter.remove(ignoreret_station)

    punkter = firedb.hent_punkt_liste(relevante_punkter, ignorer_ukendte=True)
    punkter_i_db = [pkt.gnss_navn for pkt in punkter]
    manglende_punkter = [pkt for pkt in relevante_punkter if pkt not in punkter_i_db]

    if manglende_punkter and not ignorer_advarsler:
        fire.cli.print(f"ADVARSEL: Punkterne ")
        fire.cli.print(f"{', '.join(manglende_punkter)} er ikke oprettet i databasen")
        if not bekræft("Vil du fortsætte og ignorere data fra ikke oprettede punkter?"):
            raise SystemExit

    return punkter


def find_srid(solution: BerneseSolution) -> Srid:
    """
    Find det aktuelle SRID brugt i en BerneseSolution.
    """
    try:
        srid = firedb.hent_srid(SRIDINDEX[solution.datum])
    except IndexError:
        raise SystemExit(f"Ukendt referenceramme: {solution.datum}")
    except NoResultFound:
        raise SystemExit(
            f"{solution.datum} ({SRIDINDEX[solution.datum]}) findes ikke i databasen!"
        )
    return srid


def opret_nye_tidsserier(
    punkter: List[Punkt],
    srid: Srid,
    tidsserietype: str,
    solution: BerneseSolution,
) -> List[GNSSTidsserie]:
    """
    Opret tidsserier for punkter hvor en tidsserie af den givne type ikke
    allerede eksisterer.
    """
    nye_tidsserier = []
    for punkt in punkter:
        tidsserier = [ts for ts in punkt.tidsserier if ts.srid == srid]
        if not tidsserier:
            tidsserie = GNSSTidsserie(
                punkt=punkt,
                srid=srid,
                navn=f"{punkt.gnss_navn}_{tidsserietype}_{solution.datum}",
                formål=f"GNSS-tidsserie for {punkt.gnss_navn}",
                referenceramme=f"{solution.datum}",
            )
            nye_tidsserier.append(tidsserie)

    return nye_tidsserier


def opret_nye_gnss_observationer(
    punkter: List[Punkt],
    solution: BerneseSolution,
    kovarianser: bool,
) -> List[Observation]:
    """
    Opret GNSS observationer baseret på indholdet af den givne BerneseSolution.

    ObservationsLængder oprettes altid, KoordinatKovarianser og ResidualKovarians
    kun hvis `kovarianser` er True (== en COV-fil fra Bernese er tilgængelig).
    """
    nye_observationer = []
    for punkt in punkter:
        station = solution[punkt.gnss_navn]

        observationslængde = station.obslængde.total_seconds() / 3600  # angives i timer

        nye_observationer.append(
            ObservationsLængde(
                opstillingspunkt=punkt,
                observationstidspunkt=solution.epoke,
                varighed=observationslængde,
            )
        )

        if not kovarianser:
            continue

        nye_observationer.append(
            KoordinatKovarians(
                opstillingspunkt=punkt,
                observationstidspunkt=solution.epoke,
                xx=station.kovarians.xx,
                xy=station.kovarians.yx,
                xz=station.kovarians.zx,
                yy=station.kovarians.yy,
                yz=station.kovarians.zy,
                zz=station.kovarians.zz,
            )
        )

        residualkovariansmatrix = station.dagsresidualer.kovarians_neu
        nye_observationer.append(
            ResidualKovarians(
                opstillingspunkt=punkt,
                observationstidspunkt=solution.epoke,
                xx=residualkovariansmatrix[0][0],
                xy=residualkovariansmatrix[0][1],
                xz=residualkovariansmatrix[0][2],
                yy=residualkovariansmatrix[1][1],
                yz=residualkovariansmatrix[1][2],
                zz=residualkovariansmatrix[2][2],
            )
        )

    return nye_observationer


def print_koordinat_tabel(koordinater: List[Koordinat]) -> None:
    """
    Skriv liste med nye koordinater til indsættelse i databasen.
    """
    koordinattabel = Table("Station", "T", "X", "Y", "Z", box=box.SIMPLE)

    for k in koordinater:
        koordinattabel.add_row(
            k.punkt.gnss_navn, str(k.t), str(k.x), str(k.y), str(k.z)
        )

    console = Console()
    console.print(koordinattabel)


def komprimer(filer: List[click.File]) -> bytes:
    """
    Pak filer i zip-fil med henblik på indlæsning i databasen.
    """
    zipped = BytesIO()
    with ZipFile(zipped, "w") as zipobj:
        for fil in filer:
            if fil is None:
                continue
            zipobj.write(fil)

    return zipped.getvalue()


@indlæs.command()
@click.argument("addneqfil", type=click.Path(exists=True))
@click.argument("crdfil", type=click.Path(exists=True))
@click.argument("covfil", type=click.Path(exists=True), required=False, default=None)
@click.option(
    "--tidsserietype",
    "-tt",
    type=click.Choice(["5D", "CORS"], case_sensitive=False),
    help="Tilføj de indlæste koordinater til tidsserie(r) af den valgte type.",
)
@click.option(
    "--ignorer-advarsler",
    is_flag=True,
    help="Ignorer advarsler og fortsæt afvikling af programmet uden at spørge brugeren om programmet skal stoppes.",
)
@click.option(
    "--ignorer-station",
    "-I",
    multiple=True,
    help="Undlad at indlæse data fra en eller flere stationer.",
)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
@fire.cli.default_options()
def bernese(
    addneqfil: click.Path,
    crdfil: click.Path,
    covfil: click.Path,
    tidsserietype: str,
    ignorer_advarsler: bool,
    ignorer_station: list,
    sagsbehandler: str,
    **kwargs,
) -> None:
    """
    Indlæs koordinater fra en Bernese-beregning.

    Alle udjævnede koordinater (markeret med A i koordinatfil) indlæses i databasen.
    Output fra en Bernese-beregning består typisk af en ADDNEQ2-fil, en CRD-fil og
    en COV-fil. Sidstnævnte er ikke altid tilgængelig, det gælder især ved ældre
    beregninger.

    Som udgangspunkt indlæses koordinater i databasen uden at tilknytte dem til
    tidsserier. Hvis en tidsserietype specificeres med `--tidsserie` tilføjes
    koordinaterne også til de relevante tidsserier for de givne punkter. Disse kan
    efterfølgende tilgås via tidsseriens navn, fx "RDIO_5D_IGb08".

    Bemærk dog, at i langt de fleste tilfælde er det ønskeligt at tilføje
    koordinaterne til tidsserier for de berørte stationer.

    \b
    EKSEMPLER
    ---------

        Indlæs koordinater uden at tilknytte dem til tidsserier:

        > fire gnss bernese ADDNEQ2_2096 COMB2096.CRD COMB2096.COV

        Indlæs koordinater fra en 5D-beregning med tilhørende tilknytning til
        tidsserier:

        > fire gnss bernese --tidsserietype 5D ADDNEQ2_1373 COMB1713.CRD

        Undlad at indlæse koordinater fra udvalgte stationer:

        > fire gnss bernese --tidsserietype 5D -I BUDP -I SMID ADDNEQ2_1373 COMB1713.CRD

    """
    inkluder_koordinater_i_tidsserier = tidsserietype is not None

    solution = BerneseSolution(addneqfil, crdfil, covfil)
    punkter = find_relevante_punkter(solution, ignorer_station, ignorer_advarsler)
    srid = find_srid(solution)

    sag = firedb.ny_sag(
        sagsbehandler, f"fire gnss bernese: indlæsning af nye koordinater"
    )

    # Klargør tidsserier
    if inkluder_koordinater_i_tidsserier:
        nye_tidsserier = opret_nye_tidsserier(punkter, srid, tidsserietype, solution)

        sagsevent_tidsserier = sag.ny_sagsevent(
            tidsserier=nye_tidsserier,
            beskrivelse="fire gnss bernese: Automatisk oprettelse af tidsserier",
        )
        firedb.indset_sagsevent(sagsevent_tidsserier, commit=False)
        firedb.session.flush()

    # Indlæs "observationer"
    nye_observationer = opret_nye_gnss_observationer(
        punkter, solution, kovarianser=covfil is not None
    )

    sagsevent_observationer = sag.ny_sagsevent(
        observationer=nye_observationer,
        beskrivelse="fire gnss bernese: Indlæsning af observationer",
    )
    firedb.indset_sagsevent(sagsevent_observationer, commit=False)
    firedb.session.flush()

    # Her fra indlæses koordinater og tidsserier opdateres
    nye_koordinater = []
    opdaterede_tidsserier = []
    for punkt in punkter:
        # sikrer at evt nyoprettet tidsserie er tilgængelig
        firedb.session.refresh(punkt)

        station = solution[punkt.gnss_navn]

        if inkluder_koordinater_i_tidsserier:
            ts_navn = f"{punkt.gnss_navn}_{tidsserietype}_{solution.datum}"
            tidsserie = [ts for ts in punkt.tidsserier if ts.navn == ts_navn][0]

        koordinat = Koordinat(
            punkt=punkt,
            srid=srid,
            t=solution.epoke,
            x=station.koordinat.x,
            y=station.koordinat.y,
            z=station.koordinat.z,
            # spredning i FIRE angives i milimeter
            sx=station.koordinat.sx * 1000,
            sy=station.koordinat.sy * 1000,
            sz=station.koordinat.sz * 1000,
        )
        nye_koordinater.append(koordinat)

        if inkluder_koordinater_i_tidsserier:
            tidsserie.koordinater.append(koordinat)
            opdaterede_tidsserier.append(tidsserie)

    beregning = Beregning(
        koordinater=nye_koordinater,
        observationer=nye_observationer,
    )

    sagsevent_koordinater = sag.ny_sagsevent(
        koordinater=nye_koordinater,
        beregninger=[beregning],
        beskrivelse="fire gnss bernese: Indlæsning af koordinater",
        materialer=[komprimer([addneqfil, crdfil, covfil])],
    )
    firedb.indset_sagsevent(sagsevent_koordinater, commit=False)
    try:
        firedb.session.flush()
    except IntegrityError as ex:
        # Udløses ved forsøg på indsættelse af koordinat der er identisk med en
        # eksisterende. Trigger det unikke indeks KOORDINAT_UNIQ2_IDX. Vi antager
        # at det er en fejl, da et eksakt match på punkt, SRID, x, y, z og t er
        # højst usandsynligt.
        firedb.session.rollback()
        fejlende_punkt = firedb.hent_punkt(ex.params["punktid"])

        print(
            f"FEJL: Koordinat på station {fejlende_punkt.gnss_navn} findes allerede i databasen:"
        )
        print(
            f"({ex.params['x']}, {ex.params['y']}, {ex.params['z']}, {ex.params['t']})"
        )

        raise SystemExit(1)

    if inkluder_koordinater_i_tidsserier:
        sagsevent_tidsserier = sag.ny_sagsevent(
            tidsserier=opdaterede_tidsserier,
            beskrivelse="fire gnss bernese: Opdatering af tidsserier",
        )
        firedb.indset_sagsevent(sagsevent_tidsserier, commit=False)
        firedb.session.flush()

    firedb.luk_sag(sag, commit=False)
    firedb.session.flush()

    print_koordinat_tabel(nye_koordinater)

    spørgsmål = click.style(
        f"Er du sikker på at du vil indsætte ovenstående koordinater?",
        bg="red",
        fg="white",
    )
    if bekræft(spørgsmål):
        fire.cli.firedb.session.commit()
    else:
        fire.cli.firedb.session.rollback()
