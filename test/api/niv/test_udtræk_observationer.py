import json
import shutil

import pandas as pd
import pytest

from fire.api.model.geometry import (
    Geometry,
)
from fire.api.model import (
    Punkt,
    ObservationstypeID,
    GeometriskKoteforskel as GK,
    TrigonometriskKoteforskel as TK,
)
from fire.api.niv.enums import (
    NivMetode,
    Nøjagtighed,
)
from fire.api.niv.kriterier import (
    EMPIRISK_SPREDNING,
)

# Funktioner til test
from fire.api.niv.udtræk_observationer import (
    filterkriterier,
    polygoner,
    klargør_geometrifiler,
    søgefunktioner_med_valgte_metoder,
    brug_alle_på_alle,
    observationer_inden_for_spredning,
    opstillingspunkter,
    timestamp,
    punkter_til_geojson,
)


def test_filterkriterier():

    # Opsæt og test ét tilfælde
    nøjagtigheder = [Nøjagtighed.P, Nøjagtighed.K, Nøjagtighed.D]
    spredning = filterkriterier(nøjagtigheder)
    result = spredning[ObservationstypeID.geometrisk_koteforskel]
    expected = EMPIRISK_SPREDNING[(Nøjagtighed.D, NivMetode.MGL)]
    assert result == expected, f"Forventede, at {result!r} var {expected!r}."

    # Opsæt og test flere tilfælde

    # Observationstype-id
    mgl = ObservationstypeID.geometrisk_koteforskel
    mtl = ObservationstypeID.trigonometrisk_koteforskel

    # Anvendt kriteriumstabel
    E = EMPIRISK_SPREDNING

    # Nivellementsmetode
    MGL, MTL = NivMetode.MGL, NivMetode.MTL

    # Nøgagtighed
    P, K, D = Nøjagtighed.P, Nøjagtighed.K, Nøjagtighed.D

    test_data = (
        ([P, K, D], mgl, E[(D, MGL)]),
        ([P, K, D], mtl, E[(D, MTL)]),
        ([P, K], mgl, E[(K, MGL)]),
        ([P, K], mtl, E[(K, MTL)]),
        ([P], mgl, E[(P, MGL)]),
        ([P], mtl, E[(P, MTL)]),
        ([K, D], mgl, E[(D, MGL)]),
        ([K, D], mtl, E[(D, MTL)]),
        ([K], mgl, E[(K, MGL)]),
        ([K], mtl, E[(K, MTL)]),
        ([D], mgl, E[(D, MGL)]),
        ([D], mtl, E[(D, MTL)]),
    )
    for nøjagtigheder, obstypeid, expected in test_data:
        spredning = filterkriterier(nøjagtigheder)
        result = spredning[obstypeid]
        assert result == expected, f"Forventede, at {result!r} var {expected!r}."


def test_klargør_geometrifiler(tmp_path, geojson_rectangle):
    subdir = tmp_path / "klargør_geometrifiler"
    subdir.mkdir()
    geometrifil = subdir / "rectangle.geojson"
    with geometrifil.open("w+", encoding="utf-8") as f:
        json.dump(geojson_rectangle, f, indent=2)
    klargjort = klargør_geometrifiler([geometrifil])[0]
    assert isinstance(klargjort, Geometry), f""
    shutil.rmtree(subdir)


def test_søgefunktioner_med_valgte_metoder():
    metoder = [NivMetode.MGL, NivMetode.MTL]
    funktion = lambda observationsklasse: None
    partielle = søgefunktioner_med_valgte_metoder(funktion, metoder)
    result = "observationsklasse"
    for partiel in partielle:
        assert (
            result in partiel.keywords
        ), f"Forventede, at {result!r} var blandt {partiel.keywords!r}."


def test_brug_alle_på_alle():
    operation = lambda s: s.upper()
    objekter = "abc"
    results_expected = "ABC"

    results = brug_alle_på_alle([operation], objekter)
    for result, expected in zip(results, results_expected):
        assert result == expected, f"Forventede, at {result!r} var {expected!r}."

    operationer = [
        lambda s: range(int(s)),
    ]
    objekter = (
        "1",
        "5",
        "10",
    )
    expected = (
        0,
        0,
        1,
        2,
        3,
        4,
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
    )
    result = tuple(brug_alle_på_alle(operationer, objekter))
    assert result == expected, f"Forventede, at {result!r} var {expected!r}."


def test_observationer_inden_for_spredning():

    # Observationstype-id
    mgl = ObservationstypeID.geometrisk_koteforskel
    mtl = ObservationstypeID.trigonometrisk_koteforskel

    spredning = {mgl: 0.1, mtl: 0.1}
    gks_indenfor = {
        GK(spredning_afstand=0.01),
        GK(spredning_afstand=0.05),
        GK(spredning_afstand=0.1),
    }
    gks_udenfor = {
        GK(spredning_afstand=0.2),
        GK(spredning_afstand=0.5),
        GK(spredning_afstand=1.0),
    }
    tks_indenfor = {
        TK(spredning_afstand=0.01),
        TK(spredning_afstand=0.05),
        TK(spredning_afstand=0.1),
    }
    tks_udenfor = {
        TK(spredning_afstand=0.2),
        TK(spredning_afstand=0.5),
        TK(spredning_afstand=1.0),
    }

    gks = gks_indenfor | gks_udenfor
    tks = tks_indenfor | tks_udenfor

    result = set(observationer_inden_for_spredning(gks, spredning))
    expected = gks_indenfor
    assert result == expected, f"Forventede, at {result!r} var {expected!r}."

    result = set(observationer_inden_for_spredning(tks, spredning))
    expected = tks_indenfor
    assert result == expected, f"Forventede, at {result!r} var {expected!r}."


def test_opstillingspunkter():
    punkter = [Punkt() for _ in range(10)]
    observationer = [GK(opstillingspunkt=punkt) for punkt in punkter]
    result = set(opstillingspunkter(observationer))
    expected = set(punkter)
    assert result == expected, f"Forventede, at {result!r} var {expected!r}."


@pytest.mark.freeze_time("2021-11-01T21:21:00")
def test_timestamp_string():
    fmt = "%Y-%m-%dT%H%M%S"
    result = timestamp()
    expected = "2021-11-01T212100"
    assert result == expected, f"Forventede, at {result!r} var {expected!r}."


def test_punkter_til_geojson(ark_punktoversigt, række_punktoversigt):

    # Arrange
    øst = 8.0
    nord = 55.0

    række = {
        **række_punktoversigt,
        "Øst": øst,
        "Nord": nord,
    }
    # `data`-parameteren i pd.DataFrame
    # skal være en iterable med rækker.
    data = [række.values()]
    columns = række.keys()
    df_række = pd.DataFrame(data=data, columns=columns)
    ark = pd.concat([ark_punktoversigt, df_række], ignore_index=True)

    # Act
    geojson = punkter_til_geojson(ark)
    print(geojson)

    # Assert
    properties = geojson["features"][0]["properties"]
    geometry = geojson["features"][0]["geometry"]
    check = (
        (properties["Øst"], øst),
        (properties["Nord"], nord),
        (geometry["coordinates"][0], øst),
        (geometry["coordinates"][1], nord),
    )
    for result, expected in check:
        assert result == expected, f"Forventede, at {result!r} var {expected!r}."
