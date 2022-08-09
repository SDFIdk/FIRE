"""
Modul til håndtering af output til brugeren.

"""


def forkort(strenge: list[str], n: int=10) -> list[str]:
    """
    Forkorter en liste med tekst-strenge,
    så output til brugeren bliver nemmere at læse.

    """
    if n <= 3:
        return strenge
    if len(strenge) <= n:
        return strenge
    strenge[n - 2] = "..."
    strenge[n - 1] = strenge[-1]
    return strenge[:n]
