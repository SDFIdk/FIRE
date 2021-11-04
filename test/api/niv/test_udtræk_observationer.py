from fire.api.niv.udtræk_observationer import (
    filterkriterier,
    adskil_filnavne,
    adskil_identer,
    polygoner,
    klargør_geometrifiler,
    søgefunktioner_med_valgte_metoder,
    brug_alle_på_alle,
    observationer_inden_for_spredning,
    opstillingspunkter,
    timestamp,
    punkter_til_geojson,
)


def test_brug_alle_på_alle():

    operation = lambda s: s.upper()
    objekter = 'abc'
    results_expected = 'ABC'

    results = brug_alle_på_alle([operation], objekter)
    for result, expected in zip(results, results_expected):
        assert result == expected, f'Forventede, at {result!r} var {expected!r}.'
