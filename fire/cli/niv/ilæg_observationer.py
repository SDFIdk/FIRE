import sys
from datetime import datetime
from typing import Tuple

import click
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire.cli import firedb
from fire import uuid

# Typingelementer fra databaseAPIet.
from fire.api.model import (
    EventType,
    Observation,
    Sag,
    Sagsevent,
    SagseventInfo,
)


from . import (
    ARKDEF_OBSERVATIONER,
    anvendte,
    check_om_resultatregneark_er_lukket,
    find_sag,
    find_sagsgang,
    niv,
    skriv_ark,
)

@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.argument(
    "sagsbehandler",
    nargs=1,
    type=str,
)
def ilæg_observationer(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyoprettede punkter i databasen"""
    check_om_resultatregneark_er_lukket(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print("Lægger nye observationer i databasen")
    obstype_trig = firedb.hent_observationstype("trigonometrisk_koteforskel")
    obstype_geom = firedb.hent_observationstype("geometrisk_koteforskel")

    til_registrering = []
    observationer = pd.read_excel(
        f"{projektnavn}.xlsx",
        sheet_name="Observationer",
        usecols=anvendte(ARKDEF_OBSERVATIONER),
    )
    # Fjern blanklinjer
    observationer = observationer[observationer["Fra"] == observationer["Fra"]]
    # Fjern allerede gemte
    observationer = observationer[observationer["uuid"] != observationer["uuid"]]
    observationer = observationer.reset_index(drop=True)

    alle_kilder = ", ".join(sorted(list(set(observationer.Kilde))))
    alle_uuider = observationer.uuid.astype(str)

    # Generer sagsevent
    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.OBSERVATION_INDSAT)
    sagseventtekst = f"Ilægning af observationer fra {alle_kilder}"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "observationsilægning",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)

    for i, obs in enumerate(observationer.itertuples(index=False)):
        # Ignorer allerede registrerede observationer
        if str(obs.uuid) not in ["", "None", "nan"]:
            continue

        # Vi skal bruge fra- og til-punkterne for at kunne oprette et
        # objekt af typen Observation
        try:
            punktnavn = obs.Fra
            punkt_fra = firedb.hent_punkt(punktnavn)
            punktnavn = obs.Til
            punkt_til = firedb.hent_punkt(punktnavn)
        except NoResultFound:
            fire.cli.print(f"Ukendt punkt: '{punktnavn}'", fg="red", bg="white")
            sys.exit(1)

        # For nivellementsobservationer er gruppeidentifikatoren identisk
        # med journalsidenummeret
        side = obs.Journal.split(":")[0]
        if side.isnumeric():
            gruppe = int(side)
        else:
            gruppe = None

        if obs.Type.upper() == "MTL":
            observation = Observation(
                antal=1,
                observationstype=obstype_trig,
                observationstidspunkt=obs.Hvornår,
                opstillingspunkt=punkt_fra,
                sigtepunkt=punkt_til,
                gruppe=gruppe,
                id=uuid(),
                value1=obs.ΔH,
                value2=obs.L,
                value3=obs.Opst,
                value4=obs.σ,
                value5=obs.δ,
            )
            observation.sagsevent = sagsevent

        elif obs.Type.upper() == "MGL":
            observation = Observation(
                antal=1,
                observationstype=obstype_geom,
                observationstidspunkt=obs.Hvornår,
                opstillingspunkt=punkt_fra,
                sigtepunkt=punkt_til,
                gruppe=gruppe,
                id=uuid(),
                value1=obs.ΔH,
                value2=obs.L,
                value3=obs.Opst,
                # value4=Refraktion, eta_1, sættes her til None
                value5=obs.σ,
                value6=obs.δ,
            )
        else:
            fire.cli.print(
                f"Ukendt observationstype: '{obs.Type}'", fg="red", bg="white"
            )
            sys.exit(1)
        alle_uuider[i] = observation.id
        til_registrering.append(observation)

    # Gør klar til at persistere
    observationer["uuid"] = alle_uuider

    # En lidt omstændelig dialog, for at fortælle at dette er en alvorlig ting.
    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    print(observationer[["Journal", "Fra", "Til", "uuid"]])
    fire.cli.print(f"Skriver {len(til_registrering)} observationer")
    fire.cli.print(
        "-->  HELT sikker på at du vil skrive observationerne til databasen (ja/nej)? ",
        bg="red",
        fg="white",
        bold=True,
        nl=False,
    )
    if input() != "ja":
        fire.cli.print("Dropper skrivning til database")
        return

    # Persister observationerne til databasen
    try:
        firedb.indset_flere_observationer(sagsevent, til_registrering)
    except Exception as ex:
        fire.cli.print(
            "Skrivning til databasen slog fejl", bg="red", fg="white", bold=True
        )
        fire.cli.print(f"Mulig årsag: {ex}")
        sys.exit(1)

    # Skriv resultater til resultatregneark
    resultater = {"Sagsgang": sagsgang, "Observationer": observationer}
    skriv_ark(projektnavn, resultater)
    fire.cli.print(
        f"Observationer registreret. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
    )
