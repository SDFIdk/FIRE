from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import getpass

import click
import pandas as pd

from fire.io.regneark import arkdef
import fire.io.dataframe as frame
import fire.cli
from fire.cli.niv import (
    find_faneblad,
    find_sag,
    find_sagsgang,
    niv as niv_command_group,
    bekræft,
    er_projekt_okay,
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
def luk_sag(projektnavn: str, sagsbehandler, **kwargs) -> None:
    """
    Luk sag i databasen.

    Efter endt arbejde med en sag skal den lukkes. Når en sag lukkes fremgår
    den ikke længere af listen over åbne sager (se ``fire info sag``) og det
    muligheden for at ændre i den ophører. Når en sag lukkes gemmes
    sagsregneark, observationsfiler, beregningsrapporter og GeoJSON filer i
    databasen, så disse ved behov kan findes i fremtiden.
    """
    er_projekt_okay(projektnavn)
    sag = find_sag(projektnavn)

    # Find sagsmateriale og zip det for let indlæsning i databasen
    sagsmaterialer = [
        f"{projektnavn}.xlsx",
        f"{projektnavn}-revision.xlsx",
        f"{projektnavn}.xml",
        f"{projektnavn}-resultat.xml",
        f"{projektnavn}-resultat-endelig.html",
        f"{projektnavn}-observationer.geojson",
        f"{projektnavn}-punkter.geojson",
    ]
    filoversigt = find_faneblad(projektnavn, "Filoversigt", arkdef.FILOVERSIGT)
    sagsmaterialer.extend(list(filoversigt["Filnavn"]))
    zipped = BytesIO()
    with ZipFile(zipped, "w") as zipobj:
        for fil in sagsmaterialer:
            if Path(fil).exists():
                zipobj.write(fil)

    # Tilføj materiale til sagsevent
    sagsevent = sag.ny_sagsevent(
        beskrivelse=f"Sagsmateriale for {projektnavn}",
        materialer=[zipped.getvalue()],
    )
    fire.cli.firedb.indset_sagsevent(sagsevent, commit=False)
    fire.cli.firedb.luk_sag(sag, commit=False)
    try:
        # Indsæt alle objekter i denne session
        fire.cli.firedb.session.flush()
    except Exception as ex:
        # rul tilbage hvis databasen smider en exception
        fire.cli.firedb.session.rollback()
        fire.cli.print(
            f"Der opstod en fejl - sag {sag.id} for '{projektnavn}' IKKE lukket!"
        )
        fire.cli.print(f"Mulig årsag: {ex}")
        raise SystemExit(1)

    spørgsmål = click.style(
        f"Er du sikker på at du vil lukke sagen {projektnavn}?",
        bg="red",
        fg="white",
    )
    if bekræft(spørgsmål):
        fire.cli.firedb.session.commit()
        fire.cli.print(f"Sag {sag.id} for '{projektnavn}' lukket!")
    else:
        fire.cli.firedb.session.rollback()
        fire.cli.print(f"Sag {sag.id} for '{projektnavn}' IKKE lukket!")
        return

    # Generer dokumentation til fanebladet "Sagsgang"
    # -----------------------------------------------
    sagsgang = find_sagsgang(projektnavn)
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "sagslukning",
        "Tekst": sagsevent.beskrivelse,
        "uuid": sagsevent.id,
    }
    sagsgang = frame.append(sagsgang, sagsgangslinje)
    fire.cli.print("Opdatér sagsgang i regneark")
    if skriv_ark(projektnavn, {"Sagsgang": sagsgang}):
        fire.cli.print(f"Sagen er nu lukket i regnearket '{projektnavn}.xlsx'")
