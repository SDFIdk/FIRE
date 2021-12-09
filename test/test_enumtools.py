from fire.enumtools import (
    enum_names,
    enum_aliases,
    enum_members,
    default_enums,
    selected_or_default,
    enum_values,
)


def test_enum_names(enumeration):
    expected = ['medlem1', 'medlem2', 'medlem3', 'medlem4']
    result = enum_names(enumeration)
    assert result == expected, f'Expected {result!r} to be {expected!r}'


def test_enum_aliases(enumeration):
    expected = ['alias1', 'alias2', 'alias3', 'alias4']
    result = enum_aliases(enumeration)
    assert result == expected, f'Expected {result!r} to be {expected!r}'


def test_enum_members(enumeration):
    expected = [enumeration.medlem1, enumeration.medlem3]
    result = enum_members(enumeration, ['medlem1', 'medlem3'])
    assert result == expected, f'Expected {result!r} to be {expected!r}'


def test_default_enums(enumeration):
    expected = [enumeration.medlem1, enumeration.medlem2, enumeration.medlem3, enumeration.medlem4]
    result = default_enums(enumeration)
    assert result == expected, f'Expected {result!r} to be {expected!r}'


def test_enum_values(enumeration):
    expected = {1, 2, 'test', 'bob'}
    result = enum_values(enumeration)
    assert not (expected - result), f'Expected {result!r} to be {expected!r}'
    assert not (result - expected), f'Expected {result!r} to be {expected!r}'
