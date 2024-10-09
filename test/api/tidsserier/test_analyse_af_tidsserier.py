from typing import Type

import numpy as np
from numpy.polynomial import polynomial as P
import pytest

from fire.api.model import (
    Tidsserie,
    HøjdeTidsserie,
    GNSSTidsserie,
)
from fire.api.model.tidsserier import (
    PolynomieRegression1D,
    HypoteseTest,
    TidsserieEnsemble,
    beregn_fraktil_for_t_fordeling,
    beregn_fraktil_for_normalfordeling,
)


# Uafhængige funktioner
@pytest.mark.parametrize(
    "q, testfunktion",
    [
        (-1, np.isnan),
        (2, np.isnan),
        (0, np.isneginf),
        (1, np.isposinf),
        (0.5, lambda x: np.isclose(x, 0)),
    ],
)
def test_beregning_af_fraktil(q, testfunktion):
    """Test at beregninger af fraktiler virker som forventet ved forskellige inputs"""

    assert testfunktion(beregn_fraktil_for_t_fordeling(q, 123))
    assert testfunktion(beregn_fraktil_for_normalfordeling(q))


@pytest.mark.parametrize(
    "x, x_binned_forventet",
    [
        ([1, 15], [8]),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], [8]),
        ([1, 100, 110], [1, 105]),
        ([0, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 33], [20]),
        ([2, 4, 9, 17, 27], [5, 22]),
    ],
)
def test_binning(x, x_binned_forventet):
    """Test at GNSSTidsserie.binning virker som forventet."""

    # def tjek_binning_case(x, x_binned_forventet):
    x_binned, _ = GNSSTidsserie.binning(x, x, binsize=14 * 365.25)

    assert len(x_binned) == len(x_binned_forventet)
    assert np.all(x_binned == x_binned_forventet)


def test_normaliser_data():
    """Test at intet data ligger uden for a eller b intervalgrænserne."""
    x = np.linspace(2000, 2020, 1000)
    y = np.logspace(-3, 3, 1000)
    lr = PolynomieRegression1D(x, y, grad=1)

    a, b = -10, 10
    x_norm, y_norm = lr.normaliser_data(a, b)

    assert min(x_norm) == a and max(x_norm) == b
    assert min(y_norm) == a and max(y_norm) == b


# Initialiering af klasser
def test_initialiser_HypoteseTest():
    """Test at et HypoteseTest objekt kan oprettes."""
    alpha = 0.3

    kritiskværdi = beregn_fraktil_for_normalfordeling(1 - alpha / 2)
    std_est = 4.321
    H0 = 1.234
    hypotesetest = HypoteseTest(std_est, kritiskværdi, H0)

    assert hypotesetest.std_est == std_est
    assert hypotesetest.kritiskværdi == kritiskværdi
    assert hypotesetest.H0 == H0

    assert hasattr(hypotesetest, "score")
    assert isinstance(hypotesetest.score, float)
    assert hasattr(hypotesetest, "H0accepteret")
    assert isinstance(hypotesetest.H0accepteret, bool)


def test_initialiser_PolynomieRegression1D():
    """Test funktionalitet ved brug af klassen PolynomieRegression1D"""
    x = [1, 2, 4, 5, 7]
    y = [1, 2, 3, 4, 5]
    grad = 1

    lr = PolynomieRegression1D(x, y, grad=grad)

    assert isinstance(lr, PolynomieRegression1D)


def test_initialiser_TidsserieEnsemble():
    """Test initialisering af TidsserieEnsemble"""
    with pytest.raises(TypeError):
        ts_ensemble = TidsserieEnsemble()

    # Test oprettelse af tidsserie ensemble.
    ts_ensemble = TidsserieEnsemble(
        HøjdeTidsserie,
        min_antal_punkter=3,
        tidsseriegruppe="TEST",
        referenceramme="DVR90",
    )

    assert hasattr(ts_ensemble, "tidsserieklasse")
    assert hasattr(ts_ensemble, "tidsseriegruppe")
    assert hasattr(ts_ensemble, "referenceramme")
    assert hasattr(ts_ensemble, "min_antal_punkter")
    assert hasattr(ts_ensemble, "tidsserier")

    assert isinstance(ts_ensemble.tidsserieklasse, Type)
    assert isinstance(ts_ensemble.tidsseriegruppe, str)
    assert isinstance(ts_ensemble.referenceramme, str)
    assert isinstance(ts_ensemble.min_antal_punkter, int)
    assert isinstance(ts_ensemble.tidsserier, dict)

    assert ts_ensemble.tidsserieklasse == HøjdeTidsserie
    assert ts_ensemble.tidsseriegruppe == "TEST"
    assert ts_ensemble.referenceramme == "DVR90"
    assert ts_ensemble.min_antal_punkter == 3
    assert len(ts_ensemble.tidsserier) == 0


# GNSSTidsserier
def test_tidsseriegruppe(gnsstidsserie):
    """Test at GNSSTidseriegruppe kan udledes ved at splittes tidsseriens navn op."""

    assert gnsstidsserie.tidsseriegruppe == "TEST"


def test_forbered_lineær_regression(firedb, gnsstidsserie):
    """Test at forbered_lineær_regression opretter attributter af korrekt type"""
    firedb.session.flush()
    x = gnsstidsserie.decimalår
    y = gnsstidsserie.u
    gnsstidsserie.forbered_lineær_regression(x, y, grad=1, binsize=10)

    assert hasattr(gnsstidsserie, "linreg")
    assert isinstance(gnsstidsserie.linreg, PolynomieRegression1D)


# PolynomierRegression1D
@pytest.mark.parametrize("grad", [1, 2, 3, 4, 5, 10])
def test_fit_af_kendt_model(grad):
    """
    Test eksakt fitting af højere ordens polynomier.

    Genererer data ud fra et kendt sæt af tilfældigt valgte koefficienter og løser det
    inverse problem.
    """

    x = np.linspace(-1, 1, 1000)

    # Generer tilfældige polynomiekoefficienter i intervallerne [-10, -1] og [1, 10] (Må
    # ikke kunne være 0, da det i tilfældet af at alle koefficienter bliver 0, vil fejle
    # med den numpy Runtimewarning som der testes for i test_R2)
    koeffs = np.random.randint(1, 10, grad + 1) * np.random.choice([-1, 1], grad + 1)

    y = P.polyval(x, koeffs)

    lr = PolynomieRegression1D(x, y, grad=grad)

    lr.solve()

    # Teste om de fundne koefficienter er lig de kendte
    assert np.allclose(lr.beta, koeffs)

    # Test om residualer er 0
    assert np.isclose(lr.SSR, 0)
    assert np.isclose(lr.R2, 1)


@pytest.mark.parametrize(
    "grad, x, y, match",
    [
        (
            20,
            None,
            [1, 2, 3],
            "Antallet af punkter er mindre end eller lig antallet af parametre",
        ),
        (
            3,
            None,
            [1, 2, 4],
            "Antallet af punkter er mindre end eller lig antallet af parametre",
        ),
        (1, [1, 1, 1], [1, 1, 1], "for lav rang"),
    ],
)
def test_fit_model_fejlhåndtering(grad, x, y, match):
    if x is None:
        x = [1, 2, 4]

    lr = PolynomieRegression1D(x, y, grad=grad)

    with pytest.raises(ValueError, match=match):
        lr.solve()


def test_beregning_af_R2():
    """Test af bestemmelseskoefficienten R²"""
    x = np.linspace(0, 200, 1000)

    # y er konstant
    lr = PolynomieRegression1D(x, x**0, grad=1)
    lr.solve()

    # Test at der smides en Runtimewarning med en besked hvor der står noget om
    # zero division eller divide
    with pytest.raises(RuntimeWarning, match="(?=.*zero)((?=.*divide)|(?=.*division))"):
        lr.R2

    # y er stigende
    lr = PolynomieRegression1D(x, x, grad=1)
    lr.solve()

    # Modificerer hældningen og genberegner residualerne.
    lr.beta[1] *= -1
    lr.SSR = np.sum((lr._A @ lr.beta - lr.y) ** 2)

    # Test at R2 godt kan være negativ hvis modellen passer dårligere end et simpelt
    # gennemsnit.
    assert lr.R2 < 0


@pytest.mark.parametrize("grad", [0, 1, 2, 3, 4, 5, 6, 7, 8])
def test_matrix_algebra_i_PolynomieRegression1D(firedb, grad):
    """Test at dimensionerne af diverse matricer og vektorer er som forventet."""

    ts = firedb.hent_tidsserie("RDIO_5D_IGb08")

    x = ts.decimalår
    y = ts.u
    alpha = 0.123

    x_præd = np.linspace(x[0], x[-1], 100)

    lr = PolynomieRegression1D(x, y, grad=grad)

    # Normaliser data så polynomier af høj grad ikke giver numeriske problemer
    lr.x, lr.y = lr.normaliser_data()

    assert isinstance(lr._A, np.ndarray)
    assert isinstance(lr._invATA, np.ndarray)
    assert lr._A.shape == (lr.N, lr.grad + 1)
    assert lr._invATA.shape == (lr.grad + 1, lr.grad + 1)

    lr.solve()

    assert hasattr(lr, "beta")
    assert isinstance(lr.beta, np.ndarray)
    assert lr.beta.shape == (grad + 1,)

    assert isinstance(lr.SSR, float)
    assert isinstance(lr.var0, float)
    assert isinstance(lr.var_samlet, float)
    assert isinstance(lr.R2, float)
    assert isinstance(lr.KovariansMatrix(), np.ndarray)
    assert isinstance(lr.VarBeta(), np.ndarray)

    assert lr.var0 == lr.var_samlet

    assert lr._invATA.shape == lr.KovariansMatrix().shape
    assert lr.VarBeta().shape == lr.beta.shape

    ki = lr.beregn_konfidensinterval(alpha)
    assert isinstance(ki, np.ndarray)
    assert ki.shape == (2, lr.grad + 1)

    pr = lr.beregn_prædiktioner(x_præd)
    assert isinstance(pr, np.ndarray)
    assert pr.shape == (len(x_præd),)

    kb = lr.beregn_konfidensbånd(x_præd, alpha)
    assert isinstance(kb, np.ndarray)
    assert kb.shape == (2, len(x_præd))


def test_beregn_hypotesetest_i_PolynomieRegression1D():
    x = np.linspace(-1, 1, 1000)
    lr = PolynomieRegression1D(x, x, grad=1)
    lr.solve()

    hyptest = lr.beregn_hypotesetest_hældning()

    assert isinstance(hyptest, HypoteseTest)


# TidsserieEnsemble
def test_tilføj_tidsserie_i_TidsserieEnsemble(firedb, gnsstidsseriefabrik):
    """Test at tidsserier kan tilføjes ensemblet."""
    # Test oprettelse af tidsserie ensemble.
    ts_ensemble = TidsserieEnsemble(
        GNSSTidsserie,
        min_antal_punkter=3,
        tidsseriegruppe="TEST",
        referenceramme="FIRE",
    )

    for _ in range(10):
        ts_ensemble.tilføj_tidsserie(gnsstidsseriefabrik())

    assert len(ts_ensemble.tidsserier) == 10

    firedb.session.flush()


def test_tilføj_dårlig_tidsserie_i_TidsserieEnsemble(
    firedb, gnsstidsseriefabrik, højdetidsserie
):
    """Test at forsøg på at tilføje dårlige tidsserier afvises."""
    # Opret
    ts_ensemble = TidsserieEnsemble(
        GNSSTidsserie,
        min_antal_punkter=3,
        tidsseriegruppe="TEST",
        referenceramme="FIRE",
    )

    # Tidsserie af forkert klasse
    with pytest.raises(ValueError, match="kunne ikke valideres"):
        ts_ensemble._valider_tidsserie(højdetidsserie)

    # Tidsserie med for få punkter
    ts1 = gnsstidsseriefabrik()
    ts1.koordinater = ts1.koordinater[:2]

    with pytest.raises(ValueError, match="kunne ikke valideres"):
        ts_ensemble._valider_tidsserie(ts1)

    # Tidsserie i forkert tidsseriegruppe
    ts2 = gnsstidsseriefabrik()
    (tsid, tsgruppe, ts_reframme) = ts2.navn.split("_")
    ts2.navn = f"{tsid}_TESTEFAN_{ts_reframme}"

    with pytest.raises(ValueError, match="kunne ikke valideres"):
        ts_ensemble._valider_tidsserie(ts2)

    # Tidsserie med forkert referenceramme
    ts3 = gnsstidsseriefabrik()
    ts3.srid.kortnavn = "FEM"

    with pytest.raises(ValueError, match="kunne ikke valideres"):
        ts_ensemble._valider_tidsserie(ts3)

    # Test at tidsserierne ikke bliver tilføjet.
    ts_ensemble.tilføj_tidsserie(højdetidsserie)
    ts_ensemble.tilføj_tidsserie(ts1)
    ts_ensemble.tilføj_tidsserie(ts2)
    ts_ensemble.tilføj_tidsserie(ts3)
    assert len(ts_ensemble.tidsserier) == 0

    firedb.session.rollback()


def test_beregn_samlet_varians_i_TidsserieEnsemble(firedb):
    """Test beregninger af samlet varians for ensemblet."""

    ts_ensemble = TidsserieEnsemble(
        GNSSTidsserie,
        min_antal_punkter=3,
        tidsseriegruppe="5D",
        referenceramme="IGb08",
    )

    # Tomt ensemble
    with pytest.raises(ValueError, match="Ingen tidsserier i ensemble"):
        ts_ensemble.beregn_samlet_varians()

    ts = firedb.hent_tidsserie("RDIO_5D_IGb08")
    ts_ensemble.tilføj_tidsserie(ts)

    # Tidsserie har ikke linreg attribut af typen PolynomieRegression1D
    with pytest.raises(AttributeError, match="linreg"):
        ts_ensemble.beregn_samlet_varians()

    ts.forbered_lineær_regression(ts.decimalår, ts.u)

    # Lineær regression på tidsserie er ikke blevet løst med solve() endnu
    with pytest.raises(AttributeError, match="(SSR)|(dof)"):
        ts_ensemble.beregn_samlet_varians()

    ts.linreg.solve()

    ts_ensemble.beregn_samlet_varians()

    assert ts_ensemble.var_samlet is not None
    assert ts.linreg.var_samlet is not None
