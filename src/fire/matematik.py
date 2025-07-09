from typing import Tuple
import functools

import numpy as np


@functools.cache
def Rxyz_neu(φ: float, λ: float) -> np.array:
    """
    Rotationsmatrix fra geocentriske kartesiske (ECEF, XYZ) koordinater
    til topocentriske (NEU).

    Input:

        φ: Breddegrad
        λ: Længdegrad

    Omregn med

        neu = R * xyz

    Hvor R er rotationsmatrixen, xyz en vektor med ECEF koordinater og neu er
    koordinaten i topocentrisk repræsentation. Samme tilgang kan benyttes med
    koordinatforskelle. Reference fra ESAs Navipedia:

    https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates


    Et tilsvarende princip kan *også* bruges til fx at konvertere en kovariansmatrix fra
    XYZ- til NEU-rum:

        cov_xyz = np.array(
            [
                [xx, xy, xz],
                [xy, yy, yz],
                [xz, yz, zz],
            ]
        )

        R = Rxyz_neu(lat, lon)
        cov_neu = R @ cov_xyz @ R.T

    Transponer rotationsmatrixen for at gå den anden vej (NEU->XYZ):

        cov_xyz = R.T @ cov_neu @ R

    For reference, se

        T. Soler & M. Chin, 1985, On Transformation of Covariance Matrices Between
        Local Cartesian Coordinate Systems and Communitative Diagrams

    Jf. denne artikel skal der ikke tages særligt højde for tilfældet hvor koordinaterne
    er relateret til ellipsoide frem for en kugle så længe den ellipsoidiske breddegrad
    benyttes når koordinaterne er baseret på en ellipsoide. ESA skriver en tilsvarende
    bemærkning.
    """
    sin = lambda x: np.sin(np.deg2rad(x))
    cos = lambda x: np.cos(np.deg2rad(x))

    # Bed Black om at holde fingrene væk - her ved vi bedre
    # fmt: off
    return np.array([
        [       -sin(λ),            cos(λ),       0],
        [-cos(λ)*sin(φ),    -sin(λ)*sin(φ),  cos(φ)],
        [ cos(λ)*cos(φ),     sin(λ)*cos(φ),  sin(φ)],
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
    R = Rxyz_neu(φ, λ)
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
    R = Rxyz_neu(φ, λ).T
    neu = np.array([n, e, u])

    return tuple(R @ neu)
