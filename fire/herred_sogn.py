"""
Valideringsfunktionalitet for Herred/sogn

"""

import re


OPMÅLINGSDISTRIKT_MØNSTER = re.compile(r"^(\d{1,3}|[kK])-\d{2}$")
"Generaliseret mønster for landsnumre"


def kan_være_opmålingsdistrikt(s: str) -> bool:
    """
    Returnerer sand, hvis `s` matcher opmålingsdistrikt-mønsteret.

    """
    return OPMÅLINGSDISTRIKT_MØNSTER.match(s.strip())
