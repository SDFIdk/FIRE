import pandas as pd

from fire.io.dataframe import (
    append,
    append_df,
    append_series,
    append_iterable,
    insert,
    insert_series,
    insert_iterable,
)


def test_append():
    # General
    columns = (
        'A', 'B', 'C',
    )
    rows_initial = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
    )
    df = pd.DataFrame(rows_initial, columns=columns)

    row_to_be_appended = (3, 'c', 'z')

    rows_expected = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
        (3, 'c', 'z'),
    )
    expected = pd.DataFrame(rows_expected, columns=columns)

    # Append DataFrame
    records_df = pd.DataFrame([row_to_be_appended], columns=columns)
    result = append(df, records_df)
    assert all(result == expected)

    # Append Series
    record_series = pd.Series(row_to_be_appended, index=columns)
    result = append(df, record_series)
    assert all(result == expected)

    # Append dict
    record_dict = {k: v for (k, v) in zip(columns, row_to_be_appended)}
    result = append(df, record_dict)
    assert all(result == expected)

    # Append list / tuple
    result = append(df, list(row_to_be_appended))
    assert all(result == expected)

    result = append(df, tuple(row_to_be_appended))
    assert all(result == expected)


def test_append_df():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
    )
    row_to_be_appended = (3, 'c', 'z')

    rows_expected = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
        (3, 'c', 'z'),
    )

    df = pd.DataFrame(rows_initial, columns=columns)
    records = pd.DataFrame([row_to_be_appended], columns=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = append_df(df, records)

    assert all(result == expected)


def test_append_series():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
    )
    row_to_be_appended = (3, 'c', 'z')

    rows_expected = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
        (3, 'c', 'z'),
    )

    df = pd.DataFrame(rows_initial, columns=columns)
    record = pd.Series(row_to_be_appended, index=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = append_series(df, record)

    assert all(result == expected)


def test_append_dict():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = [
        [1, 'a', 'x'],
        [2, 'b', 'y'],
    ]
    row_to_be_appended = {
        'A': 3,
        'B': 'c',
        'C': 'z',
    }

    rows_expected = [
        [1, 'a', 'x'],
        [2, 'b', 'y'],
        [3, 'c', 'z'],
    ]

    df = pd.DataFrame(rows_initial, columns=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = append_iterable(df, row_to_be_appended)

    assert all(result == expected)

    # Case: When dict has not all columns of df
    row_to_be_appended = {
        'A': 3,
        'C': 'z',
    }
    rows_expected = [
        [1, 'a', 'x'],
        [2, 'b', 'y'],
        [3, None, 'z'],
    ]
    expected = pd.DataFrame(rows_expected, columns=columns)
    result = append_iterable(df, row_to_be_appended)

    assert all(result == expected)


def test_append_list():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = [
        [1, 'a', 'x'],
        [2, 'b', 'y'],
    ]
    row_to_be_appended = [3, 'c', 'z']

    rows_expected = [
        [1, 'a', 'x'],
        [2, 'b', 'y'],
        [3, 'c', 'z'],
    ]

    df = pd.DataFrame(rows_initial, columns=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = append_iterable(df, row_to_be_appended)

    assert all(result == expected)


def test_append_list_also_works_for_tuple_record():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
    )
    row_to_be_appended = (3, 'c', 'z')

    rows_expected = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
        (3, 'c', 'z'),
    )

    df = pd.DataFrame(rows_initial, columns=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = append_iterable(df, row_to_be_appended)

    assert all(result == expected)


def test_insert():
    # General
    columns = (
        'A', 'B', 'C',
    )
    rows_initial = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
    )
    df = pd.DataFrame(rows_initial, columns=columns)

    row_to_be_inserted = (3, 'c', 'z')

    rows_expected = (
        (1, 'a', 'x'),
        (3, 'c', 'z'), # index = 1
    )
    index = 1
    expected = pd.DataFrame(rows_expected, columns=columns)

    # Insert Series
    record_series = pd.Series(row_to_be_inserted, index=columns)
    result = insert(df, index, record_series)
    assert all(result == expected)

    # Insert dict
    record_dict = {k: v for (k, v) in zip(columns, row_to_be_inserted)}
    result = insert(df, index, record_dict)
    assert all(result == expected)

    # Insert list / tuple
    result = insert(df, index, list(row_to_be_inserted))
    assert all(result == expected)

    result = insert(df, index, tuple(row_to_be_inserted))
    assert all(result == expected)


def test_insert_series():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
    )
    row_to_be_inserted = (3, 'c', 'z')

    rows_expected = (
        (1, 'a', 'x'),
        (3, 'c', 'z'),  # index = 1
    )
    index = 1

    df = pd.DataFrame(rows_initial, columns=columns)
    record = pd.Series(row_to_be_inserted, index=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = insert_series(df, index, record)

    assert all(result == expected)


def test_insert_dict():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = [
        [1, 'a', 'x'],
        [2, 'b', 'y'],
    ]
    row_to_be_inserted = {
        'A': 3,
        'B': 'c',
        'C': 'z',
    }

    rows_expected = [
        [1, 'a', 'x'],
        [3, 'c', 'z'],  # index = 1
    ]
    index = 1

    df = pd.DataFrame(rows_initial, columns=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = insert_iterable(df, index, row_to_be_inserted)

    assert all(result == expected)


def test_insert_list():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = [
        [1, 'a', 'x'],
        [2, 'b', 'y'],
    ]
    row_to_be_inserted = [3, 'c', 'z']

    rows_expected = [
        [1, 'a', 'x'],
        [3, 'c', 'z'],  # index = 1
    ]
    index = 1

    df = pd.DataFrame(rows_initial, columns=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = insert_iterable(df, index, row_to_be_inserted)

    assert all(result == expected)


def test_insert_list_also_works_for_tuple_record():
    columns = (
        'A', 'B', 'C',
    )

    rows_initial = (
        (1, 'a', 'x'),
        (2, 'b', 'y'),
    )
    row_to_be_inserted = (3, 'c', 'z')

    rows_expected = (
        (1, 'a', 'x'),
        (3, 'c', 'z'),  # index = 1
    )
    index = 1

    df = pd.DataFrame(rows_initial, columns=columns)

    expected = pd.DataFrame(rows_expected, columns=columns)
    result = insert_iterable(df, index, row_to_be_inserted)

    assert all(result == expected)
