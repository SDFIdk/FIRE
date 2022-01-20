from typing import Tuple
import functools

import numpy as np


@functools.cache
def Rneu_xyz(φ: float, λ: float) -> np.array:
    """
    Rotationsmatrix fra topocentriske (NEU) til geocentriske (XYZ) koordinater.

    Input:

        φ: Breddegrad
        λ: Længdegrad

    Brug rotationsmatrixen til fx at konvertere en kovariansmatrix fra NEU- til XYZ-rum:

        cov_xyz = np.array(
            [
                [xx, xy, xz],
                [xy, yy, yz],
                [xz, yz, zz],
            ]
        )

        R = Rxyz_neu(lat, lon)
        cov_xyz = R @ cov_neu @ R.T

    Transponer rotationsmatrixen for at gå den anden vej (XYZ->NEU):

        cov_neu = R.T @ cov_xyz @ R

    For reference, se

        T. Soler & M. Chin, 1985, On Transformation of Covariance Matrices Between
        Local Cartesian Coordinate Systems and Communitative Diagrams

    Jf. denne artikel skal der ikke tages særligt højde for tilfældet hvor koordinaterne
    er relateret til ellipsoide frem for en kugle så længe den ellipsoidiske breddegrad
    benyttes når koordinaterne er baseret på en ellipsoide.
    """
    sin = lambda x: np.sin(np.deg2rad(x))
    cos = lambda x: np.cos(np.deg2rad(x))
    # Bed Black om at holde fingrene væk - her ved vi bedre
    # fmt: off
    return np.array([
        [-sin(φ)*cos(λ), -sin(λ), cos(φ)*cos(λ)],
        [-sin(φ)*sin(λ),  cos(λ), cos(φ)*sin(λ)],
        [        cos(φ),       0,        sin(φ)],
    ])
    # fmt: on


def xyz2neu(
    x: float, y: float, z: float, φ: float, λ: float
) -> Tuple[float, float, float]:
    """
    Konverter koordinatdifferenser fra geocentrisk (XYZ) til topocentrisk (NEU) rum

    Input:

        x: x-komponent af geocentrisk koordinat
        y: y-komponent af geocentrisk koordinat
        z: z-komponent af geocentrisk koordinat
        φ: Breddegrad
        λ: Længdegrad

    Output:

        n: n-komponent af topocentrisk koordinat
        e: e-komponent af topocentrisk koordinat
        u: u-komponent af topocentrisk koordinat
    """
    R = Rneu_xyz(φ, λ).T
    xyz = np.array([x, y, z])

    return tuple(R @ xyz)


def neu2xyz(
    n: float, e: float, u: float, φ: float, λ: float
) -> Tuple[float, float, float]:
    """
    Konverter koordinatdifferenser fra topocentrisk (NEU) til geocentrisk (XYZ) rum

    Input:

        n: n-komponent af topocentrisk koordinat
        e: e-komponent af topocentrisk koordinat
        u: u-komponent af topocentrisk koordinat
        φ: Breddegrad
        λ: Længdegrad

    Output:

        x: x-komponent af geocentrisk koordinat
        y: y-komponent af geocentrisk koordinat
        z: z-komponent af geocentrisk koordinat
    """
    R = Rneu_xyz(φ, λ)
    neu = np.array([n, e, u])

    return tuple(R @ neu)
