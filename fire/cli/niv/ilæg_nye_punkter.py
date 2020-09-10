from itertools import chain
from typing import List

import click
import pandas as pd

import fire.cli
from fire.cli import firedb
from fire import uuid
from fire.api.model import (
    GeometriObjekt,
    Point,
    Punkt,
    PunktInformation,
    Sag,
    Sagsevent,
    SagseventInfo,
)

from . import (
    anvendte,
    check_om_resultatregneark_er_lukket,
    find_nyetablerede,
    find_sag,
    find_sagsgang,
    niv,
    normaliser_placeringskoordinat,
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
def ilæg_nye_punkter(projektnavn: str, sagsbehandler: str, **kwargs) -> None:
    """Registrer nyoprettede punkter i databasen"""
    check_om_resultatregneark_er_lukket(projektnavn)
    sag = find_sag(projektnavn)
    sagsgang = find_sagsgang(projektnavn)

    fire.cli.print("Lægger nye punkter i databasen")

    # Opbyg oversigt over nyetablerede punkter
    nyetablerede = find_nyetablerede(projektnavn)
    nyetablerede = nyetablerede.reset_index()
    n = nyetablerede.shape[0]

    if n == 0:
        fire.cli.print("Ingen nyetablerede punkter at registrere")
        return

    landsnummer_pit = firedb.hent_punktinformationtype("IDENT:landsnr")
    beskrivelse_pit = firedb.hent_punktinformationtype("ATTR:beskrivelse")
    h_over_terræn_pit = firedb.hent_punktinformationtype("AFM:højde_over_terræn")
    assert landsnummer_pit is not None, "Rådden landsnummer_pit"
    assert beskrivelse_pit is not None, "Rådden beskrivelse_pit"
    assert h_over_terræn_pit is not None, "Rådden h_over_terræn_pit"

    # Vi samler de genererede punkter i en dict, så de kan persisteres samlet
    # under et enkelt sagsevent
    genererede_punkter = {}
    genererede_landsnumre = []
    anvendte_løbenumre = {}

    for i in range(n):
        # Et tomt tekstfelt kan repræsenteres på en del forskellige måder...
        # Punkter udstyret med uuid er allerede registrerede
        # if not (nyetablerede["uuid"][i] in ["", None] or pd.isna(nyetablerede["uuid"][i])):
        if str(nyetablerede.uuid[i]) not in ["", "None", "nan"]:
            continue
        print(f"Behandler punkt {nyetablerede['Foreløbigt navn'][i]}")

        lokation = normaliser_placeringskoordinat(
            nyetablerede["Øst"][i], nyetablerede["Nord"][i]
        )
        distrikt = nyetablerede["Landsnummer"][i]

        # Gør klar til at finde et ledigt landsnummer, hvis vi ikke allerede har et
        if 2 == len(distrikt.split("-")):
            if distrikt in anvendte_løbenumre:
                numre = anvendte_løbenumre[distrikt]
            else:
                numre = find_alle_løbenumre_i_distrikt(distrikt)
                anvendte_løbenumre[distrikt] = numre
                print(f"Fandt {len(numre)} punkter i distrikt {distrikt}")
        # Hvis der er anført et fuldt landsnummer må det hellere se ud som et
        elif 3 != len(distrikt.split("-")):
            fire.cli.print(f"Usselt landsnummer: {distrikt}")
            continue
        # Ellers har vi et komplet landsnummer, så punktet er allerede registreret
        else:
            continue

        # Hjælpepunkter har egen nummerserie
        if "ingen" == str(nyetablerede["Afmærkning"][i]).lower():
            nummerserie = range(90001, 100000)
        else:
            nummerserie = chain(range(9001, 10000), range(19001, 20000))

        # Så leder vi...
        for løbenummer in nummerserie:
            if løbenummer not in numre:
                # Lige nu laver vi kun numeriske løbenumre, men fx vandstandsbrædder
                # og punkter fra de gamle hovedstadsregistre har tekstuelle løbe"numre"
                if str(løbenummer).isnumeric():
                    landsnummer = f"{distrikt}-{løbenummer:05}"
                else:
                    landsnummer = f"{distrikt}-{løbenummer}"
                genererede_landsnumre.append(landsnummer)
                fire.cli.print(f"Anvender landsnummer {landsnummer}")
                numre.add(løbenummer)
                break
        # Hvis for-løkken løber til ende er vi løbet tør for løbenumre
        else:
            fire.cli.print(
                f"Løbet tør for landsnumre i distrikt {distrikt}", fg="red", bg="white"
            )
            continue

        # Skab nyt punktobjekt
        nyt_punkt = Punkt()
        nyt_punkt.id = uuid()

        # Tilføj punktets lokation som geometriobjekt
        geo = GeometriObjekt()
        geo.geometri = Point(lokation)
        nyt_punkt.geometriobjekter.append(geo)
        # Hvis lokationen i regnearket var UTM32, så bliver den nu længde/bredde
        nyetablerede.at[i, "Øst"] = lokation[0]
        nyetablerede.at[i, "Nord"] = lokation[1]

        # Tilføj punktets landsnummer som punktinformation
        pi_l = PunktInformation(
            infotype=landsnummer_pit, punkt=nyt_punkt, tekst=landsnummer
        )
        nyt_punkt.punktinformationer.append(pi_l)
        nyetablerede.at[i, "Landsnummer"] = landsnummer

        # Tilføj punktets højde over terræn som punktinformation, hvis anført
        try:
            ΔH = float(nyetablerede["Højde over terræn"][i])
        except (TypeError, ValueError):
            ΔH = 0
        if ΔH != ΔH:
            ΔH = 0.0
        if not pd.isna(nyetablerede["Højde over terræn"][i]):
            pi_h = PunktInformation(
                infotype=h_over_terræn_pit,
                punkt=nyt_punkt,
                tal=ΔH,
            )
            nyt_punkt.punktinformationer.append(pi_h)

        # Tilføj punktets afmærkning som punktinformation, selv hvis ikke anført
        afm_id = 4999  # AFM:4999 = "ukendt"
        afm_ids = {
            "ukendt": 4999,
            "bolt": 2700,
            "lodret bolt": 2701,
            "skruepløk": 2950,
            "ingen": 5998,
        }

        if not pd.isna(nyetablerede["Afmærkning"][i]):
            # Afmærkningsbeskrivelse
            afm = str(nyetablerede["Afmærkning"][i]).lower()
            # Første ord i afmærkningsbeskrivelsen
            afm_første = afm.split()[0].rstrip(":;,.- ").lstrip("afm:")

            if afm_første.isnumeric():
                afm_id = int(afm_første)
            else:
                afm_id = afm_ids.get(afm, 4999)

            afmærkning_pit = firedb.hent_punktinformationtype(f"AFM:{afm_id}")
            if afmærkning_pit is None:
                afm_id = 4999
                afmærkning_pit = firedb.hent_punktinformationtype("AFM:4999")
            beskrivelse = (
                afmærkning_pit.beskrivelse.replace("-\n", "")
                .replace("\n", " ")
                .rstrip(".")
                .strip()
            )
            nyetablerede.at[i, "Afmærkning"] = f"AFM:{afm_id} - {beskrivelse}"

        if afm_id == 4999:
            fire.cli.print(
                f"ADVARSEL: Nyoprettet punkt index {i} har ingen gyldig afmærkning anført",
                fg="red",
                bg="white",
                bold=True,
            )
        pi_a = PunktInformation(infotype=afmærkning_pit, punkt=nyt_punkt)
        nyt_punkt.punktinformationer.append(pi_a)

        # Tilføj punktbeskrivelsen som punktinformation, hvis anført
        if not pd.isna(nyetablerede["Beskrivelse"][i]):
            pi_b = PunktInformation(
                infotype=beskrivelse_pit,
                punkt=nyt_punkt,
                tekst=nyetablerede["Beskrivelse"][i],
            )
            nyt_punkt.punktinformationer.append(pi_b)

        genererede_punkter[i] = nyt_punkt

    if len(genererede_punkter) == 0:
        fire.cli.print("Ingen nyetablerede punkter at registrere")
        return

    # Gør klar til at persistere

    # Generer sagsevent
    sagsevent = Sagsevent(sag=sag)
    sagsevent.id = uuid()
    er = "er" if len(genererede_landsnumre) > 1 else ""
    sagseventtekst = f"Oprettelse af punkt{er} {', '.join(genererede_landsnumre)}"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    # Generer dokumentation til fanebladet "Sagsgang"
    sagsgangslinje = {
        "Dato": pd.Timestamp.now(),
        "Hvem": sagsbehandler,
        "Hændelse": "punktoprettelse",
        "Tekst": sagseventtekst,
        "uuid": sagsevent.id,
    }
    sagsgang = sagsgang.append(sagsgangslinje, ignore_index=True)

    # Persister punkterne til databasen
    fire.cli.print(sagseventtekst, fg="yellow", bold=True)
    if "ja" != input(
        "-->  HELT sikker på at du vil skrive punkterne til databasen (ja/nej)? "
    ):
        fire.cli.print("Dropper skrivning")
        return
    firedb.indset_flere_punkter(sagsevent, list(genererede_punkter.values()))

    # ... og marker i regnearket at det er sket
    for k in genererede_punkter:
        nyetablerede.at[k, "uuid"] = genererede_punkter[k].id
    # Drop numerisk index
    nyetablerede = nyetablerede.reset_index(drop=True)

    # Skriv resultater til resultatregneark
    resultater = {"Sagsgang": sagsgang, "Nyetablerede punkter": nyetablerede}
    skriv_ark(projektnavn, resultater)
    fire.cli.print(
        f"Punkter oprettet. Kopiér nu faneblade fra '{projektnavn}-resultat.xlsx' til '{projektnavn}.xlsx'"
    )


def find_alle_løbenumre_i_distrikt(distrikt: str) -> List[str]:
    pit = firedb.hent_punktinformationtype("IDENT:landsnr")
    landsnumre = (
        firedb.session.query(PunktInformation)
        .filter(
            PunktInformation.infotypeid == pit.infotypeid,
            PunktInformation.tekst.startswith(distrikt),
        )
        .all()
    )
    løbenumre = [n.tekst.split("-")[-1] for n in landsnumre if "-" in n.tekst]
    # Ikke-numeriske løbenumre (fx vandstandsbrædder) forbliver som tekst,
    # men numeriske vil vi gerne have gjort til tal
    numre = [int(n) if str(n).isnumeric() else n for n in løbenumre]
    return set(numre)
