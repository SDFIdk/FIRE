from fire.api.niv.regnemotor import (
    InternKote,
    InternNivObservation,
    RegneMotor,
    GamaRegn,
)

from fire.cli.niv._netoversigt import (
    byg_netgeometri_og_singulære,
)


def test_analyser_subnet():
    """Test at analyser_subnet finder det korrekte antal subnet"""

    disjunkt_net = {}
    subnet = [i for i in range(3)]
    for N_subnet in range(1, 5):
        disjunkt_net.update({node: list(set(subnet) - {node}) for node in subnet})

        liste_af_subnet = RegneMotor.find_subnet(disjunkt_net)

        assert len(liste_af_subnet) == N_subnet

        # lav et kopi af disjunkt net og forbind alle subnet.
        forbundet_net = {k: v for (k, v) in disjunkt_net.items()}

        # Forbind punkt "0" til første punkt i hvert subnet for at forbinde alle subnet
        forbundet_net[0] = list(
            set(forbundet_net[0] + [subn[0] for subn in liste_af_subnet])
        )

        liste_af_subnet = RegneMotor.find_subnet(forbundet_net)
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

    # Opbyg observationer som vi kan starte en motor ud fra.
    # Observationer opbygges som en symmetrisk, rettet, cirkulær graf, for at
    # efterligne en lukket nivellementspolygon.
    observationer = [
        InternNivObservation(
            str(i % N), # fra
            str(j % N), # til
            *(6*[None]),
        )
        for i in range(N) for j in (i + 1, i - 1)
    ]

    gamle_koter = [
        InternKote(
            p, None,None,None,
            True if p in fastholdte else False
        )
        for p in alle_punkter
    ]

    motor = GamaRegn(observationer=observationer, gamle_koter=gamle_koter)

    # Analyser net
    net, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    # Byg dataframes
    net, singulære = byg_netgeometri_og_singulære(net, ensomme_subnet).values()
    # Check ingen singulære
    assert len(net) == N
    assert len(singulære) == 0
    assert len(net.keys()) == 3

    # Tilføj disjunkte net (singulære punkter)
    observationer.append(InternNivObservation("RMV", "SKG", *(6*[None])))
    observationer.append(InternNivObservation("SKG", "RMV", *(6*[None])))
    observationer.append(InternNivObservation("Hjemme", "Ude", *(6*[None])))
    observationer.append(InternNivObservation("Ude", "Hjemme", *(6*[None])))

    # ... og tilføj dem til alle_punkter
    gamle_koter.extend(
        [
            InternKote(p, *(3*[None])) for p in ("RMV", "SKG", "Hjemme", "Ude")
        ]
    )
    motor = GamaRegn(observationer=observationer, gamle_koter=gamle_koter)

    net, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    net, singulære = byg_netgeometri_og_singulære(net, ensomme_subnet).values()

    assert len(net) == N
    assert len(singulære) == 4
    assert len(net.keys()) == 3

    # Fasthold nyt punkt
    for gk in gamle_koter:
        if gk.punkt=='RMV':
            gk.fasthold = True
            break
    motor = GamaRegn(observationer=observationer, gamle_koter=gamle_koter)

    net, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    net, singulære = byg_netgeometri_og_singulære(net, ensomme_subnet).values()

    assert len(net) == N + 2
    assert len(singulære) == 2
    assert len(net.keys()) == 3

    # Fra-Til har ikke en tilsvarende modsatrettet observation
    observationer.append(InternNivObservation("SKG", "Nord", *(6*[None])))
    observationer.append(InternNivObservation("SKG", "Syd", *(6*[None])))
    observationer.append(InternNivObservation("SKG", "Øst", *(6*[None])))
    observationer.append(InternNivObservation("SKG", "Vest", *(6*[None])))

    # ... og tilføj dem til alle_punkter
    gamle_koter.extend(
        [
            InternKote(p, *(3*[None])) for p in ("Nord", "Syd", "Øst", "Vest")
        ]
    )
    motor = GamaRegn(observationer=observationer, gamle_koter=gamle_koter)
    net, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    net, singulære = byg_netgeometri_og_singulære(net, ensomme_subnet).values()

    assert len(net) == N + 6
    assert len(singulære) == 2
    assert len(net.keys()) == 6
