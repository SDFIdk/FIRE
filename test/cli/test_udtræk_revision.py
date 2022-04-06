from dataclasses import dataclass

from fire.cli.niv._udtræk_revision import (
    lokations_streng,
    flyt_attributter_til_toppen,
)


def test_lokations_streng():

    lokation = (1.11111, 2.2222)
    expected = "2.222 m   1.111 m"
    result = lokations_streng(lokation)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    lokation = (4.4444, 5.5555)
    expected = "5.556 m   4.444 m"
    result = lokations_streng(lokation)
    assert result == expected, f'Expected {result!r} to be {expected!r}'

    lokation = (0.9994, 0.9995)
    expected = "1.000 m   0.999 m"
    result = lokations_streng(lokation)
    assert result == expected, f'Expected {result!r} to be {expected!r}'


def test_flyt_attributter_til_toppen():

    # Arrange
    @dataclass
    class _type:
        name: str

    @dataclass
    class _info:
        infotype: _type

        def __eq__(self, other):
            return self.infotype.name == other.infotype.name

        def __repr__(self):
            return self.infotype.name

    punkt_informationer = [
        _info(_type('c')),
        _info(_type('b')),
        _info(_type('a')),
        _info(_type('x')),
        _info(_type('y')),
        _info(_type('z')),
    ]

    prioritering = [
        'z',
        'y',
        'x',
    ]

    # Act
    result_all = flyt_attributter_til_toppen(punkt_informationer, prioritering)
    expected_all = [
        _info(_type('z')),
        _info(_type('y')),
        _info(_type('x')),
        _info(_type('a')),
        _info(_type('b')),
        _info(_type('c')),
    ]
    print(result_all)

    # Assert
    for result, expected in zip(result_all, expected_all):
        assert result == expected, f'Expected {result!r} to be {expected!r}'
