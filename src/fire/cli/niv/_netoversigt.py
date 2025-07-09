import click
import pandas as pd

from fire.io.regneark import arkdef
import fire.cli
from fire.api.niv.regnemotor import (
    RegneMotor,
    GamaRegn,
)

from . import (
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
    resultater = netanalyse(projektnavn, observationer, punktoversigt)

    skriv_ark(projektnavn, resultater, "-netoversigt")

    singulære_punkter = tuple(sorted(resultater["Singulære"]["Punkt"]))
    fire.cli.print(
        f"Fandt {len(singulære_punkter)} singulære punkter: {singulære_punkter}"
    )

# ------------------------------------------------------------------------------
def netanalyse(
    projektnavn, observationer: pd.DataFrame=None, punktoversigt: pd.DataFrame=None, motor: GamaRegn=None, **kwargs
) -> dict[str, pd.DataFrame]:
    """ Kan enten give en motor eller de relevante dataframes og kwargs til at starte en motor."""

    # Hvis motor ikke er givet så skal observationer og punktoversigt være givet. Dette er
    # så funktionen her både kan bruges af niv regn og niv netoversigt kommandoerne.
    if not motor:
        motor = GamaRegn.fra_dataframe(observationer, punktoversigt, projektnavn, **kwargs)

    # Analyser net
    net, subnet, ensomme_punkter, fastholdte_i_subnet = motor.netgraf()

    kontroller_net(projektnavn, motor, fastholdte_i_subnet, subnet)

    resultater = konstruer_netgeometri_og_singulære(net, ensomme_punkter)

    return resultater

def kontroller_net(projektnavn: str, motor: GamaRegn, fastholdte_i_subnet: list[str], subnet: list[list]):

    # Find de nyetablerede
    # KREBSLW: synes vi skal fjerne det her med de nyetablerede. Det er sygt forvirrende. Men kan ikke lige overskue konsekvensen...
    # Og det bliver måske mere besværligt at få det med i regnemotoren
    nyetablerede = find_faneblad(
        projektnavn, "Nyetablerede punkter", arkdef.NYETABLEREDE_PUNKTER
    )

    # KREBSLW: her laves noget fixfaxeri med nyetablerede punkter
    # Brug foreløbige navne hvis det ser ud som om der ikke er tildelt landsnumre endnu
    nye_punkter = set(list(nyetablerede["Landsnummer"]))
    if 0 == motor.observerede_punkter.intersection(nye_punkter):
        nye_punkter = set(list(nyetablerede["Foreløbigt navn"]))

    gamle_punkter = motor.observerede_punkter - nye_punkter

    # Vi vil gerne have de nye punkter først i listen, så vi sorterer gamle
    # og nye hver for sig
    nye_punkter = tuple(sorted(nye_punkter))
    alle_punkter = nye_punkter + tuple(sorted(gamle_punkter))

    # Sanity check af fastholdte punkter versus tilgængelige observationer
    afbryd = False
    for fastholdt_punkt in motor.fastholdte.keys():
        if fastholdt_punkt not in alle_punkter:
            fire.cli.print(
                f"FEJL: Observation(er) for fastholdt punkt {fastholdt_punkt} er slukket eller mangler",
                fg="white",
                bg="red",
            )
            afbryd = True
    if afbryd:
        raise SystemExit(1)

    # Skriv advarsel hvis ikke der er mindst et fastholdt punkt i hvert
    # subnet.
    if None in fastholdte_i_subnet:
        fire.cli.print(
            "ADVARSEL: Manglende fastholdt punkt i mindst et subnet! Forslag til fastholdte punkter i hvert subnet:",
            bg="yellow",
            fg="black",
        )
        for i, subnet_ in enumerate(subnet):
            if fastholdte_i_subnet[i]:
                fire.cli.print(f"  Subnet {i}: {fastholdte_i_subnet[i]}", fg="green")
            else:
                fire.cli.print(f"  Subnet {i}: {subnet_[0]}", fg="red")

    return

def konstruer_netgeometri_og_singulære(net: dict[str,list], ensomme_punkter: list) -> dict[pd.DataFrame]:
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

    return {"Netgeometri": netf, "Singulære": ensomme}
