import getpass

import click
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound

import fire.cli
from fire import uuid
from fire.api.model import (
    EventType,
    Observation,
    Sagsevent,
    SagseventInfo,
)
from fire.io.regneark import arkdef

from . import (
    bekræft,
    find_faneblad,
    find_sag,
    find_sagsgang,
    niv,
    skriv_ark,
    er_projekt_okay,
)


@niv.command()
@fire.cli.default_options()
@click.argument(
    "projektnavn",
    nargs=1,
    type=str,
)
@click.option(
    "--sagsbehandler",
    default=getpass.getuser(),
    type=str,
    help="Angiv andet brugernavn end den aktuelt indloggede",
)
def ilæg_observationer(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nye observationer i databasen"""
    er_projekt_okay(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print(f"Sags/projekt-navn: {projektnavn}  ({sag.id})")
    fire.cli.print(f"Sagsbehandler:     {sagsbehandler}")

    obstype_trig = fire.cli.firedb.hent_observationstype("trigonometrisk_koteforskel")
    obstype_geom = fire.cli.firedb.hent_observationstype("geometrisk_koteforskel")
    til_registrering = []

    observationer = find_faneblad(projektnavn, "Observationer", arkdef.OBSERVATIONER)
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

        # Indlæs IKKE slukkede observationer i databasen
        if str(obs.Sluk) not in ["", "None", "nan"]:
            continue

        # Vi skal bruge fra- og til-punkterne for at kunne oprette et
        # objekt af typen Observation
        try:
            punktnavn = obs.Fra
            punkt_fra = fire.cli.firedb.hent_punkt(punktnavn)
            punktnavn = obs.Til
            punkt_til = fire.cli.firedb.hent_punkt(punktnavn)
        except NoResultFound:
            fire.cli.print(f"Ukendt punkt: '{punktnavn}'", fg="red", bg="white")
            raise SystemExit(1)

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
                value4=0.0,  # Refraktion, eta_1, er defineret som non-null, så vi sætter den til 0 istf. None
                value5=obs.σ,
                value6=obs.δ,
                value7=0,  # 1,2,3 henviser til 1.,2.,3. præcisionsnivellement. 0 til "ingen af dem"
            )
        else:
            fire.cli.print(
                f"Ukendt observationstype: '{obs.Type}'", fg="red", bg="white"
            )
            raise SystemExit(1)
        alle_uuider[i] = observation.id
        til_registrering.append(observation)

    # Gør klar til at persistere
    observationer["uuid"] = alle_uuider

    fire.cli.print(sagseventtekst, fg="yellow", bold=True)

    obs_rapport = observationer[observationer["Sluk"] == ""]
    fire.cli.print(str(obs_rapport[["Journal", "Fra", "Til", "uuid"]]))

    # Persister observationerne til databasen
    fire.cli.print(f"Skriver {len(til_registrering)} observationer")
    sagsevent.observationer = til_registrering
    fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)

    try:
        fire.cli.firedb.session.flush()
    except Exception as ex:
        # rul tilbage hvis databasen smider en exception
        fire.cli.firedb.session.rollback()
        fire.cli.print(
            f"Der opstod en fejl - observationer for '{projektnavn}' IKKE indlæst!"
        )
        fire.cli.print(f"Mulig årsag: {ex}")
    else:
        spørgsmål = click.style("Du indsætter nu ", fg="white", bg="red")
        spørgsmål += click.style(
            f"{len(til_registrering)} observationer ", fg="white", bg="red", bold=True
        )
        spørgsmål += click.style(f"i ", fg="white", bg="red")
        spørgsmål += click.style(
            f"{fire.cli.firedb.db}", fg="white", bg="red", bold=True
        )
        spørgsmål += click.style("-databasen - er du sikker?", fg="white", bg="red")

        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()

            # Skriv resultater til resultatregneark
            resultater = {"Sagsgang": sagsgang, "Observationer": observationer}
            skriv_ark(projektnavn, resultater)
            fire.cli.print(
                f"Observationer registreret. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
            )
        else:
            fire.cli.firedb.session.rollback()
            fire.cli.print(f"Observationer for '{projektnavn}' IKKE indlæst!")
