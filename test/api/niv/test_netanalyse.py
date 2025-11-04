import numpy as np

from fire.api.niv.regnemotor import (
    NivKote,
    NivObservation,
    RegneMotor,
    GamaRegn,
)

from fire.cli.niv._netoversigt import (
    byg_netgeometri_og_singulære,
)
from fire.api.niv.lukkesum import (
    LukkesumStats,
    lukkesum_af_polygon,
    aggreger_multidigraf,
)


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
        NivObservation(
            str(i % N),  # fra
            str(j % N),  # til
            *(6 * [None]),
        )
        for i in range(N)
        for j in (i + 1, i - 1)
    ]

    gamle_koter = [
        NivKote(p, None, None, None, True if p in fastholdte else False)
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
    observationer.append(NivObservation("RMV", "SKG", *(6 * [None])))
    observationer.append(NivObservation("SKG", "RMV", *(6 * [None])))
    observationer.append(NivObservation("Hjemme", "Ude", *(6 * [None])))
    observationer.append(NivObservation("Ude", "Hjemme", *(6 * [None])))

    # ... og tilføj dem til alle_punkter
    gamle_koter.extend(
        [NivKote(p, *(3 * [None])) for p in ("RMV", "SKG", "Hjemme", "Ude")]
    )
    motor = GamaRegn(observationer=observationer, gamle_koter=gamle_koter)

    net, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    net, singulære = byg_netgeometri_og_singulære(net, ensomme_subnet).values()

    assert len(net) == N
    assert len(singulære) == 4
    assert len(net.keys()) == 3

    # Fasthold nyt punkt
    for gk in gamle_koter:
        if gk.punkt == "RMV":
            gk.fasthold = True
            break
    motor = GamaRegn(observationer=observationer, gamle_koter=gamle_koter)

    net, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    net, singulære = byg_netgeometri_og_singulære(net, ensomme_subnet).values()

    assert len(net) == N + 2
    assert len(singulære) == 2
    assert len(net.keys()) == 3

    # Fra-Til har ikke en tilsvarende modsatrettet observation
    observationer.append(NivObservation("SKG", "Nord", *(6 * [None])))
    observationer.append(NivObservation("SKG", "Syd", *(6 * [None])))
    observationer.append(NivObservation("SKG", "Øst", *(6 * [None])))
    observationer.append(NivObservation("SKG", "Vest", *(6 * [None])))

    # ... og tilføj dem til alle_punkter
    gamle_koter.extend(
        [NivKote(p, *(3 * [None])) for p in ("Nord", "Syd", "Øst", "Vest")]
    )
    motor = GamaRegn(observationer=observationer, gamle_koter=gamle_koter)
    net, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    net, singulære = byg_netgeometri_og_singulære(net, ensomme_subnet).values()

    assert len(net) == N + 6
    assert len(singulære) == 2
    assert len(net.keys()) == 6


def test_lukkesum():
    """
    Tester et nivellement-netværk som dette:
    A ------ B ------ E ------ F
    |        |
    |        |
    D ------ C
    Fra     Til     delta H
    A       B        1.1
    B       A       -1.
    B       C        2.1
    C       B       -2.
    C       D        3.1
    D       C       -3.
    D       A       -6
    A       D        5.7
    B       E        2.5
    E       B       -2.4
    E       F        1.3
    F       E       -1.2
    """
    obs = [
        ["A", "B", 1.1],
        ["B", "A", -1.0],
        ["B", "C", 2.1],
        ["C", "B", -2.0],
        ["C", "D", 3.1],
        ["D", "C", -3.0],
        ["D", "A", -6],
        ["A", "D", 5.7],
        ["B", "E", 2.5],
        ["E", "B", -2.4],
        ["E", "F", 1.3],
        ["F", "E", -1.2],
    ]
    # Opret observationer
    observationer = [
        NivObservation(
            o[0],  # fra
            o[1],  # til
            None,
            None,
            1,  # afstand
            o[2],  # delta H
            None,
            None,
        )
        for o in obs
    ]

    motor = GamaRegn(observationer=observationer, gamle_koter=[])
    digraf = aggreger_multidigraf(motor.multidigraf)

    kredse = motor.beregn_lukkesummer()
    # tjek at der findes 1 kreds
    assert len(kredse) == 1

    # Test en lukket polygon
    polygon: LukkesumStats = lukkesum_af_polygon(digraf, ["A", "B", "C", "D"])
    (summa_rho, lukkesum, H_frem, H_tilbage) = (
        polygon.summa_rho,
        polygon.lukkesum,
        polygon.lukkesum_frem,
        polygon.lukkesum_tilbage,
    )
    deltaH = [ls.deltaH_mean for ls in polygon.linjer]
    rho = [ls.rho for ls in polygon.linjer]

    assert np.isclose(summa_rho, 0)
    assert np.isclose(lukkesum, 0.3)
    assert np.isclose(H_frem, 0.3)
    assert np.isclose(H_tilbage, -0.3)
    assert np.allclose(rho, [0.1, 0.1, 0.1, -0.3])
    assert np.allclose(deltaH, [1.05, 2.05, 3.05, -5.85])

    # Test en blind linje ("åben" polygon)
    polygon = lukkesum_af_polygon(digraf, ["B", "E", "F"], lukket=False)
    (summa_rho, lukkesum, H_frem, H_tilbage) = (
        polygon.summa_rho,
        polygon.lukkesum,
        polygon.lukkesum_frem,
        polygon.lukkesum_tilbage,
    )
    deltaH = [ls.deltaH_mean for ls in polygon.linjer]
    rho = [ls.rho for ls in polygon.linjer]

    assert np.isclose(summa_rho, 0.2)
    assert np.isclose(lukkesum, 3.7)
    assert np.isclose(H_frem, 3.8)
    assert np.isclose(H_tilbage, -3.6)
    assert np.allclose(rho, [0.1, 0.1])
    assert np.allclose(deltaH, [2.45, 1.25])
