import pathlib
from typing import (
    Iterable,
)

from fire.ident import (
    kan_være_ident,
)
from fire.herred_sogn import (
    kan_være_opmålingsdistrikt,
)

# TODO (JOAMO): DRY


def adskil_filnavne(tekststrenge: Iterable[str]) -> tuple[list[str], list[str]]:
    """
    Adskiller filnavne på eksisterende filer fra den givne liste med tekststrenge.

    Returnerer to lister med adskilte og tilbageværende tekststrenge med de enkelte
    tekststrenge repræsenteret én gang.

    """
    tekststrenge = set(tekststrenge)
    adskilte = {
        tekststreng
        for tekststreng in tekststrenge
        if pathlib.Path(tekststreng).is_file()
    }
    return list(adskilte), list(tekststrenge - adskilte)


def adskil_identer(tekststrenge: Iterable[str]) -> tuple[list[str], list[str]]:
    """
    Adskiller mulige identer fra den givne liste med tekststrenge.

    Returnerer to lister med adskilte og tilbageværende tekststrenge med de enkelte
    tekststrenge repræsenteret én gang.

    """
    tekststrenge = set(tekststrenge)
    adskilte = {
        tekststreng for tekststreng in tekststrenge if kan_være_ident(tekststreng)
    }
    return list(adskilte), list(tekststrenge - adskilte)


def adskil_distrikter(tekststrenge: Iterable[str]) -> tuple[list[str], list[str]]:
    """
    Adskiller mulige opmålingsdistrikter fra den givne liste med tekststrenge.

    Returnerer to lister med adskilte og tilbageværende tekststrenge med de enkelte
    tekststrenge repræsenteret én gang.

    """
    tekststrenge = set(tekststrenge)
    adskilte = {
        tekststreng
        for tekststreng in tekststrenge
        if kan_være_opmålingsdistrikt(tekststreng)
    }
    return list(adskilte), list(tekststrenge - adskilte)
