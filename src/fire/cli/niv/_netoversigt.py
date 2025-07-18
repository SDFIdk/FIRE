from collections import Counter, deque
from typing import Dict, List, Set, Tuple

import click
import pandas as pd

from fire.io.regneark import arkdef
import fire.cli

from fire.cli.niv import (
    find_faneblad,
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
def netoversigt(projektnavn: str, **kwargs) -> None:
    """Opbyg netoversigt"""
    er_projekt_okay(projektnavn)
    fire.cli.print("Så kører vi")

    resultater = netanalyse(projektnavn)
    skriv_ark(projektnavn, resultater, "-netoversigt")
    singulære_punkter = tuple(sorted(resultater["Singulære"]["Punkt"]))
    fire.cli.print(
        f"Fandt {len(singulære_punkter)} singulære punkter: {singulære_punkter}"
    )


# ------------------------------------------------------------------------------
def netanalyse(
    projektnavn: str, faneblad: str = "Punktoversigt"
) -> Dict[str, pd.DataFrame]:
    observationer = find_faneblad(projektnavn, "Observationer", arkdef.OBSERVATIONER)
    punktoversigt = find_faneblad(projektnavn, faneblad, arkdef.PUNKTOVERSIGT)
    nyetablerede = find_faneblad(
        projektnavn, "Nyetablerede punkter", arkdef.NYETABLEREDE_PUNKTER
    )

    observationer = observationer[observationer["Sluk"] != "x"]
    observerede_punkter = set(list(observationer["Fra"]) + list(observationer["Til"]))

    # Brug foreløbige navne hvis det ser ud som om der ikke er tildelt landsnumre endnu
    nye_punkter = set(list(nyetablerede["Landsnummer"]))
    if 0 == observerede_punkter.intersection(nye_punkter):
        nye_punkter = set(list(nyetablerede["Foreløbigt navn"]))

    gamle_punkter = observerede_punkter - nye_punkter

    # Vi vil gerne have de nye punkter først i listen, så vi sorterer gamle
    # og nye hver for sig
    nye_punkter = tuple(sorted(nye_punkter))
    alle_punkter = nye_punkter + tuple(sorted(gamle_punkter))
    observerede_punkter = tuple(sorted(observerede_punkter))

    # Opbyg net ud fra de fastholdte punkter, eller ud fra det mest observerede
    # punkt, hvis der endnu ikke er fastholdte punkter (dette er fx tilfældet
    # umiddelbart efter indlæsning af observationer)
    fastholdte = tuple(punktoversigt[punktoversigt["Fasthold"] == "x"]["Punkt"])
    if 0 == len(fastholdte):
        alle_obs = list(observationer["Fra"]) + list(observationer["Til"])
        c = Counter(alle_obs)
        fastholdte = tuple([c.most_common(1)[0][0]])

    # Udfør netanalyse
    (net, singulære) = netgraf(observationer, alle_punkter, fastholdte)
    return {"Netgeometri": net, "Singulære": singulære}


# ------------------------------------------------------------------------------
def netgraf(
    observationer: pd.DataFrame,
    alle_punkter: Tuple[str, ...],
    fastholdte_punkter: Tuple[str, ...],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    fire.cli.print("Analyserer net")
    assert len(fastholdte_punkter) > 0, "Netanalyse kræver mindst et fastholdt punkt"
    # Initialiser
    net = {}

    # Sanity check af fastholdte punkter versus tilgængelige observationer
    afbryd = False
    for fastholdt_punkt in fastholdte_punkter:
        if fastholdt_punkt not in alle_punkter:
            fire.cli.print(
                f"FEJL: Observation(er) for fastholdt punkt {fastholdt_punkt} er slukket eller mangler",
                fg="white",
                bg="red",
            )
            afbryd = True
    if afbryd:
        raise SystemExit(1)

    for punkt in alle_punkter:
        net[punkt] = set()

    # Tilføj forbindelser alle steder hvor der er observationer
    for fra, til in zip(observationer["Fra"], observationer["Til"]):
        net[fra].add(til)
        net[til].add(fra)

    # Undersøg om der er nettet består af flere ikke-sammenhængende subnet.
    subnet = analyser_subnet(net)
    forbundne_punkter = set()
    ensomme_punkter = set()

    fastholdte_i_subnet = [None for _ in subnet]
    for i, subnet_ in enumerate(subnet):
        for punkt in fastholdte_punkter:
            if punkt in subnet_:
                fastholdte_i_subnet[i] = punkt
                forbundne_punkter.update(subnet_)
                break
        else:
            ensomme_punkter.update(subnet_)

    # De ensomme punkter skal ikke med i netgrafen
    for punkt in ensomme_punkter:
        net.pop(punkt, None)

    # Skriv advarsel hvis ikke der er mindste et fastholdt punkt i hvert
    # subnet.

    if None in fastholdte_i_subnet:
        fire.cli.print(
            "ADVARSEL: Manglende fastholdt punkt i mindst et subnet! Forslag til fastholdte punkter i hvert subnet:",
            bg="yellow",
            fg="black",
        )
        for i, subnet_ in enumerate(subnet):
            if fastholdte_i_subnet[i]:
                fire.cli.print(f"  Subnet {i}: {fastholdte_i_subnet[i]}", fg="green")
            else:
                fire.cli.print(f"  Subnet {i}: {subnet_[0]}", fg="red")

    # Nu kommer der noget grimt...
    # Tving alle rækker til at være lige lange, så vi kan lave en dataframe af dem
    max_antal_naboer = max([len(net[e]) for e in net])
    nyt = {}
    for punkt in net:
        naboer = list(sorted(net[punkt])) + max_antal_naboer * [""]
        nyt[punkt] = tuple(naboer[0:max_antal_naboer])

    # Ombyg og omdøb søjler med smart "add_prefix"-trick fra
    # @piRSquared, https://stackoverflow.com/users/2336654/pirsquared
    # Se https://stackoverflow.com/questions/46078034/python-dict-with-values-as-tuples-to-pandas-dataframe
    netf = pd.DataFrame(nyt).T.rename_axis("Punkt").add_prefix("Nabo ").reset_index()
    netf.sort_values(by="Punkt", inplace=True)
    netf.reset_index(drop=True, inplace=True)

    ensomme = pd.DataFrame(sorted(ensomme_punkter), columns=["Punkt"])
    return netf, ensomme


def analyser_subnet(net: dict[set]) -> list[list]:
    """
    Find selvstændige net i et større net

    Bruger breadth first search (BFS).
    Baseret på materiale fra: https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/
    """

    # Funktion til breadth first search
    def bfs(net, besøgt, startpunkt, subnet=[]):
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
