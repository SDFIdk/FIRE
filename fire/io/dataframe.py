"""
Værktøjer til at manipulere dataframes

Med pandas 1.4+ er pandas.DataFrame.append(...) forældet praksis, og man skal bruge pandas.concat() i stedet.

Da de to tilgange ikke er ækvivalente, er der brug for nogle andre fremgangsmåder i koden.

Typiske opgaver i FIRE-kodebasen:

*   Man skal nemt kunne tilføje en enkelt post i forlængelse af en eksisterende dataframe.
    -   Eksempel: Tilføj ny linje til sagsgang.

*   Man skal nemt kunne tilføje flere poster i forlængelse af en eksisterende dataframe.
    -   Eksempel: Tilføj fem blanke linjer i punktoversigt.

*   Man skal nemt kunne opdatere en eksisterende række i en dataframe.
    -   Eksempel: Opdatér kote-koordinat på et punkt.

"""
from typing import (
    Any,
    Union,
)
import pandas as pd


def append(df: pd.DataFrame, row: Any, /, **kwargs) -> pd.DataFrame:
    """
    Tilføj rækken i forlængelse af de eksisterende rækker.

    """
    if isinstance(row, pd.DataFrame):
        return append_df(df, row, **kwargs)

    if isinstance(row, pd.Series):
        return append_series(df, row, **kwargs)

    if isinstance(row, dict):
        any_key = list(row.keys())[0]
        if isinstance(row.get(any_key), (list, tuple)):
            return append(df, pd.DataFrame(row), **kwargs)

        return append_iterable(df, row, **kwargs)

    if isinstance(row, (list, tuple)):
        if isinstance(row[0], dict):
            return append(df, pd.DataFrame(row), **kwargs)

        return append_iterable(df, row, **kwargs)

    raise NotImplementedError(f"Det er ikke muligt at tilføje en {type(row)!r}.")


def append_df(df: pd.DataFrame, new: pd.DataFrame, /, **kwargs) -> pd.DataFrame:
    kwargs = {**kwargs, 'ignore_index': True}
    return pd.concat([df, new], **kwargs)


def append_series(df: pd.DataFrame, row: pd.Series, /, **kwargs) -> pd.DataFrame:
    if set(df.columns) ^ set(row.keys()):
        raise ValueError("Kolonner i ark og række skal matche.")

    if kwargs.pop('ignore_index', None) is not None or kwargs.pop('axis', None) is not None:
        raise RuntimeError(f"Funktionaliteten kræver `axis=1` og `ignore_index=True`.")

    return pd.concat([df.T, row], axis=1, ignore_index=True, **kwargs).T


def append_iterable(df: pd.DataFrame, row: Union[dict, list, tuple], /, **kwargs) -> pd.DataFrame:
    return append_series(df, pd.Series(row, index=df.columns), **kwargs)


append_df.__doc__ = append.__doc__
append_series.__doc__ = append.__doc__
append_iterable.__doc__ = append.__doc__


def insert(df: pd.DataFrame, index: int, row: Any, /) -> pd.DataFrame:
    """
    Indsæt én enkelt post i arket på den givne indeks-værdi.

    """
    if isinstance(row, pd.Series):
        return insert_series(df, index, row)

    if isinstance(row, (dict, list, tuple)):
        return insert_iterable(df, index, row)

    raise NotImplementedError(f"Det er ikke muligt at tilføje en {type(row)!r}.")


def insert_series(df: pd.DataFrame, index: int, row: pd.Series, /) -> pd.DataFrame:
    df.loc[index] = row
    return df


def insert_iterable(df: pd.DataFrame, index: int, row: Union[dict, list, tuple], /) -> pd.DataFrame:
    # Note: df.loc[index] = row will add the dict keys and not the values.
    # Note: df.loc[index] = row.values() works but has no assurance of correct order.
    # Therefore, use pd.Series which will provide the column names.
    return insert(df, index, pd.Series(row, index=df.columns))


insert_series.__doc__ = insert.__doc__
insert_iterable.__doc__ = insert.__doc__
