from fire.io.formattering import (
    forkort,
)


def test_forkortet():
    test_data = list('abcdefghij')
    expected = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    result = forkort(test_data)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    test_data = list('abcdefghijklmn')
    expected = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', '...', 'n']
    result = forkort(test_data)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    test_data = list('abc')
    expected = ['a', 'b', 'c']
    result = forkort(test_data)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    test_data = list('abc')
    expected = test_data
    result = forkort(test_data, n=3)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    test_data = list('abc')
    expected = test_data
    result = forkort(test_data, n=2)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    test_data = list('abc')
    expected = test_data
    result = forkort(test_data, n=0)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    test_data = list('abc')
    expected = test_data
    result = forkort(test_data, n=-1)
    assert result == expected, f'Expected {result!r} to be {expected!r}'
