import shutil

from fire.typologi import (
    adskil_filnavne,
    adskil_identer,
)


def test_adskil_filnavne(tmp_path, identer_gyldige, identer_ugyldige):
    subdir = tmp_path / "adskil_filnavne"
    subdir.mkdir()

    # Opret filer
    basenames = ("foo.geojson", "other.txt", "boing")
    filenames = [subdir / basename for basename in basenames]
    [filename.touch() for filename in filenames]
    # Filnavnene
    filnavne = [f"{fname}" for fname in filenames]

    # Smid nogle gyldige og ugyldige identer med, altså nogle ikke-filer.
    identer = identer_gyldige + identer_ugyldige

    # Saml det hele
    kandidater = filnavne + list(identer)

    result_filnavne, result_identer = adskil_filnavne(kandidater)
    for result in result_filnavne:
        assert result in filnavne, f"Forventede, at {result!r} var blandt {filnavne}."
    for result in result_identer:
        assert result in identer, f"Forventede, at {result!r} var blandt {identer}."

    shutil.rmtree(subdir)


def test_adskil_identer(identer_gyldige, identer_ugyldige):

    gyldige = identer_gyldige
    ugyldige = identer_ugyldige

    kandidater = gyldige + ugyldige
    result_gyldige, result_ugyldige = adskil_identer(kandidater)
    for result in result_gyldige:
        assert result in gyldige, f"Forventede, at {result!r} var blandt {gyldige!r}."
    for result in result_ugyldige:
        assert result in ugyldige, f"Forventede, at {result!r} var blandt {ugyldige!r}."
