import getpass

import click
import pandas as pd


from fire.api.model import Sagsinfo
import fire.io.dataframe as frame
import fire.cli
from fire.cli.niv import (
    find_sag,
    niv as niv_command_group,
    bekræft,
    er_projekt_okay,
    find_sagsgang,
    skriv_ark,
)


@niv_command_group.command()
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
def åbn_sag(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """
    Åbn en lukket sag i databasen.

    Det hænder at en sag er blevet lukket for tidligt, og skal åbnes igen for
    fortsætte arbejdet. Det kan gøres med denne kommando.
    """
    er_projekt_okay(projektnavn)
    sag = find_sag(projektnavn, accepter_inaktiv=True)

    if sag.aktiv:
        fire.cli.print(
            f"Sag {sag.id} for {projektnavn} er allerede åben."
        )
        raise SystemExit(1)

    gammel_sagsinfo = sag.sagsinfos[-1]
    ny_sagsinfo = Sagsinfo(
        aktiv="true",
        journalnummer=gammel_sagsinfo.journalnummer,
        behandler=gammel_sagsinfo.behandler,
        beskrivelse=gammel_sagsinfo.beskrivelse,
        sag=sag,
    )
    fire.cli.firedb.session.add(ny_sagsinfo)

    try:
        # først må vi sikre at sagen står som aktiv...
        fire.cli.firedb.session.flush()

        # ... og så kan vi tilføje en sagsevent med en besked om at sagen genåbnes
        sagsevent = sag.ny_sagsevent(beskrivelse=f"Genåbning af sag {projektnavn}")
        fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)
        fire.cli.firedb.session.flush()
    except Exception as ex:
        fire.cli.firedb.session.rollback()
        fire.cli.print(
            f"Der opstod en fejl - sag {sag.id} for '{projektnavn}' IKKE åbnet!"
        )
        fire.cli.print(f"Mulig årsag: {ex}")
    else:
        spørgsmål = click.style(
            f"Er du sikker på at du vil åbne sagen {projektnavn}?",
            bg="red",
            fg="white",
        )
        if bekræft(spørgsmål):
            fire.cli.firedb.session.commit()
            fire.cli.print(f"Sag {sag.id} for '{projektnavn}' åbnet!")
        else:
            fire.cli.firedb.session.rollback()
            fire.cli.print(f"Sag {sag.id} for '{projektnavn}' IKKE åbnet!")

    # Generer dokumentation til fanebladet "Sagsgang"
    # -----------------------------------------------
    sagsgang = find_sagsgang(projektnavn)
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "sagsåbning",
        "Tekst": sagsevent.beskrivelse,
        "uuid": sagsevent.id,
    }
    sagsgang = frame.append(sagsgang, sagsgangslinje)
    fire.cli.print("Opdatér sagsgang i regneark")
    if skriv_ark(projektnavn, {"Sagsgang": sagsgang}):
        fire.cli.print(f"Sagen er nu åbnet i regnearket '{projektnavn}.xlsx'")
