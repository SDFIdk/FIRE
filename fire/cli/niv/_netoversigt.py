from collections import Counter
from typing import Dict, List, Set, Tuple

import click
import pandas as pd

import fire.cli

from . import (
    ARKDEF_NYETABLEREDE_PUNKTER,
    ARKDEF_OBSERVATIONER,
    ARKDEF_PUNKTOVERSIGT,
    find_faneblad,
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
def netoversigt(projektnavn: str, **kwargs) -> None:
    """Opbyg netoversigt"""
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
    observationer = find_faneblad(projektnavn, "Observationer", ARKDEF_OBSERVATIONER)
    punktoversigt = find_faneblad(projektnavn, faneblad, ARKDEF_PUNKTOVERSIGT)
    nyetablerede = find_faneblad(
        projektnavn, "Nyetablerede punkter", ARKDEF_NYETABLEREDE_PUNKTER
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
    punktoversigt = punktoversigt.replace("nan", "")
    fastholdte = tuple(punktoversigt[punktoversigt["Fasthold"] != ""]["Punkt"])
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
    for punkt in alle_punkter:
        net[punkt] = set()

    # Tilføj forbindelser alle steder hvor der er observationer
    for fra, til in zip(observationer["Fra"], observationer["Til"]):
        net[fra].add(til)
        net[til].add(fra)

    # Undersøg om der er nettet består af flere ikke-sammenhængende subnet.
    # Skriv advarsel hvis ikke der er mindste et fastholdt punkt i hvert
    # subnet.
    subnet = analyser_subnet(net)
    if len(subnet) > 1:
        fastholdte_i_subnet = [None for _ in subnet]
        for i, subnet_ in enumerate(subnet):
            for subnetpunkt in subnet_:
                if subnetpunkt in fastholdte_punkter:
                    fastholdte_i_subnet[i] = subnetpunkt
                    continue

        if None in fastholdte_i_subnet:
            fire.cli.print(
                "ADVARSEL: Manglende fastholdt punkt i mindst et subnet! Forslag til fastholdte punkter i hvert subnet:",
                bg="yellow",
                fg="black",
            )
            for i, subnet_ in enumerate(subnet):
                if fastholdte_i_subnet[i]:
                    fire.cli.print(
                        f"  Subnet {i}: {fastholdte_i_subnet[i]}", fg="green"
                    )
                else:
                    fire.cli.print(f"  Subnet {i}: {subnet_[0]}", fg="red")

    # Tilføj forbindelser fra alle fastholdte punkter til det første fastholdte punkt
    udgangspunkt = fastholdte_punkter[0]
    for punkt in fastholdte_punkter:
        if punkt != udgangspunkt:
            net[udgangspunkt].add(punkt)
            net[punkt].add(udgangspunkt)

    # Analysér netgraf
    forbundne_punkter = set()
    ensomme_punkter = set()
    for punkt in alle_punkter:
        if path_to_origin(net, udgangspunkt, punkt) is None:
            ensomme_punkter.add(punkt)
        else:
            forbundne_punkter.add(punkt)

    # Vi vil ikke have de kunstige forbindelser mellem fastholdte punkter med
    # i output, så nu genopbygger vi nettet uden dem
    net = {}
    for punkt in alle_punkter:
        net[punkt] = set()
    for fra, til in zip(observationer["Fra"], observationer["Til"]):
        net[fra].add(til)
        net[til].add(fra)

    # De ensomme punkter skal heller ikke med i netgrafen
    for punkt in ensomme_punkter:
        net.pop(punkt, None)

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


# ------------------------------------------------------------------------------
# path_to_origin - eksempel:
#
# graph = {
#     'A': {'B', 'C'},
#     'B': {'C', 'D'},
#     'C': {'D'},
#     'D': {'C'},
#     'E': {'F'},
#     'F': {'C'},
#     'G': {}
# }
#
# print (path_to_origin (graph, 'A', 'C'))
# print (path_to_origin (graph, 'A', 'G'))
# ------------------------------------------------------------------------------
def path_to_origin(
    graph: Dict[str, Set[str]], start: str, origin: str, path: List[str] = []
):
    """
    Mikroskopisk backtracking netkonnektivitetstest. Baseret på et
    essay af Pythonstifteren Guido van Rossum, publiceret 1998 på
    https://www.python.org/doc/essays/graphs/. Koden er her
    moderniseret fra Python 1.5 til 3.7 og modificeret til at
    arbejde på dict-over-set (originalen brugte dict-over-list)
    """
    path = path + [start]
    if start == origin:
        return path
    if start not in graph:
        return None
    for node in graph[start]:
        if node not in path:
            newpath = path_to_origin(graph, node, origin, path)
            if newpath:
                return newpath
    return None


def analyser_subnet(net):
    """
    Find selvstændige net i et større net

    Med inspiration fra https://www.geeksforgeeks.org/connected-components-in-an-undirected-graph/
    """

    def depth_first_search(net, visited, vertex, subnet):
        visited[vertex] = True
        subnet.append(vertex)

        for adjacent_vertex in net[vertex]:
            if not visited[adjacent_vertex]:
                net, visited, vertex, subnet = depth_first_search(
                    net, visited, adjacent_vertex, subnet
                )

        return net, visited, vertex, subnet

    visited = {vertex: False for vertex in net.keys()}
    connected_vertices = []
    for vertex in net.keys():
        if not visited[vertex]:
            subnet = []
            net, visited, vertex, subnet = depth_first_search(
                net, visited, vertex, subnet
            )
            connected_vertices.append(subnet)

    return connected_vertices
