import pandas as pd

from fire.cli.niv._netoversigt import (
    analyser_subnet,
    netgraf,
)


def test_analyser_subnet():
    """Test at analyser_subnet finder det korrekte antal subnet"""

    disjunkt_net = {}
    subnet = [i for i in range(3)]
    for N_subnet in range(1, 5):
        disjunkt_net.update({node: list(set(subnet) - {node}) for node in subnet})

        liste_af_subnet = analyser_subnet(disjunkt_net)

        assert len(liste_af_subnet) == N_subnet

        # lav et kopi af disjunkt net og forbind alle subnet.
        forbundet_net = {k: v for (k, v) in disjunkt_net.items()}

        # Forbind punkt "0" til første punkt i hvert subnet for at forbinde alle subnet
        forbundet_net[0] = list(
            set(forbundet_net[0] + [subn[0] for subn in liste_af_subnet])
        )

        liste_af_subnet = analyser_subnet(forbundet_net)
        assert len(liste_af_subnet) == 1

        subnet = [i + 100 for i in subnet]


def test_netgraf():
    """
    Test at netgraf returnerer det forventede antal punkter

    Der testes for antal forbundne punkter, antal singulære punkter, og antal
    kolonner i Netgeometri-dataframen (svarende til højeste antal naboer + 1).
    """
    N = 20
    alle_punkter = tuple(str(i) for i in range(N))
    fastholdte = (
        "3",
        "13",
    )

    # Observationer opbygges som en symmetrisk, rettet, cirkulær graf, for at
    # efterligne en lukket nivellementspolygon.
    obs = [
        {"Fra": str(i % N), "Til": str(j % N)} for i in range(N) for j in (i + 1, i - 1)
    ]
    observationer = pd.DataFrame.from_records(obs)
    (net, singulære) = netgraf(observationer, alle_punkter, fastholdte)

    # Check ingen singulære
    assert len(net) == N
    assert len(singulære) == 0
    assert len(net.keys()) == 3

    # Tilføj disjunkte net (singulære punkter)
    obs.append({"Fra": "RMV", "Til": "SKG"})
    obs.append({"Fra": "SKG", "Til": "RMV"})
    obs.append({"Fra": "Hjemme", "Til": "Ude"})
    obs.append({"Fra": "Ude", "Til": "Hjemme"})

    # ... og tilføj dem til alle_punkter
    alle_punkter += ("RMV", "SKG", "Hjemme", "Ude")

    observationer = pd.DataFrame.from_records(obs)
    (net, singulære) = netgraf(observationer, alle_punkter, fastholdte)

    assert len(net) == N
    assert len(singulære) == 4
    assert len(net.keys()) == 3

    # Fasthold nyt punkt
    fastholdte += ("RMV",)
    (net, singulære) = netgraf(observationer, alle_punkter, fastholdte)

    assert len(net) == N + 2
    assert len(singulære) == 2
    assert len(net.keys()) == 3

    # Fra-Til har ikke en tilsvarende modsatrettet observation
    obs.append({"Fra": "SKG", "Til": "Nord"})
    obs.append({"Fra": "SKG", "Til": "Syd"})
    obs.append({"Fra": "SKG", "Til": "Øst"})
    obs.append({"Fra": "SKG", "Til": "Vest"})

    alle_punkter += ("Nord", "Syd", "Øst", "Vest")

    observationer = pd.DataFrame.from_records(obs)
    (net, singulære) = netgraf(observationer, alle_punkter, fastholdte)

    assert len(net) == N + 6
    assert len(singulære) == 2
    assert len(net.keys()) == 6
