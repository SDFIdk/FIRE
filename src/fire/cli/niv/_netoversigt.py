import click
import pandas as pd

from fire.io.regneark import arkdef
import fire.cli
from fire.api.niv.regnemotor import (
    RegneMotor,
    GamaRegn,
)

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

    observationer = find_faneblad(projektnavn, "Observationer", arkdef.OBSERVATIONER)
    punktoversigt = find_faneblad(projektnavn, "Punktoversigt", arkdef.PUNKTOVERSIGT)

    # Fjern slukkede observationer
    observationer = observationer[observationer["Sluk"] != "x"]

    motor = GamaRegn.fra_dataframe(observationer, punktoversigt, projektnavn=projektnavn)

    # Analyser net
    net_uden_ensomme, ensomme_subnet, estimerbare_punkter = motor.netanalyse()
    if ensomme_subnet:
        fire.cli.print(f"ADVARSEL: Manglende fastholdt punkt i mindst et subnet! Forslag til fastholdte punkter i hvert subnet:", bg="yellow", fg="black")
        for i, forslag in enumerate(ensomme_subnet):
            fire.cli.print(f"  Subnet {i}: {forslag}", fg="red")

    resultater = byg_netgeometri_og_singulære(net_uden_ensomme, ensomme_subnet)

    skriv_ark(projektnavn, resultater, "-netoversigt")

    singulære_punkter = tuple(sorted(resultater["Singulære"]["Punkt"]))
    fire.cli.print(
        f"Fandt {len(singulære_punkter)} singulære punkter: {singulære_punkter}"
    )


def byg_netgeometri_og_singulære(net_uden_ensomme: dict[str,list], ensomme_subnet: list) -> dict[pd.DataFrame]:
    """Omsætter en netværksgraf og dens ensomme punkter til dataframes"""
    # Nu kommer der noget grimt...
    # Tving alle rækker til at være lige lange, så vi kan lave en dataframe af dem
    max_antal_naboer = max([len(net_uden_ensomme[e]) for e in net_uden_ensomme])
    nyt = {}
    for punkt in net_uden_ensomme:
        naboer = list(sorted(net_uden_ensomme[punkt])) + max_antal_naboer * [""]
        nyt[punkt] = tuple(naboer[0:max_antal_naboer])

    # Ombyg og omdøb søjler med smart "add_prefix"-trick fra
    # @piRSquared, https://stackoverflow.com/users/2336654/pirsquared
    # Se https://stackoverflow.com/questions/46078034/python-dict-with-values-as-tuples-to-pandas-dataframe
    netf = pd.DataFrame(nyt).T.rename_axis("Punkt").add_prefix("Nabo ").reset_index()
    netf.sort_values(by="Punkt", inplace=True)
    netf.reset_index(drop=True, inplace=True)

    ensomme_punkter = set().union(*ensomme_subnet)
    ensomme = pd.DataFrame(sorted(ensomme_punkter), columns=["Punkt"])

    return {"Netgeometri": netf, "Singulære": ensomme}
