from math import isclose

import numpy as np

from fire.matematik import (
    neu2xyz,
    xyz2neu,
    Rneu_xyz,
)

W = 0.001 ** 2
XX = 0.9145031116e-01
XY = 0.1754111808e-01
YY = 0.1860172410e-01
XZ = 0.9706757931e-01
YZ = 0.2230707662e-01
ZZ = 0.1740501496e00

COV_XYZ = (
    np.array(
        [
            [XX, XY, XZ],
            [XY, YY, YZ],
            [XZ, YZ, ZZ],
        ]
    )
    * W
)


def test_neu2xyz_og_xyz2neu():
    """Test at neu2xyz og xyz2neu er hinandens inverse."""
    n = 0.01
    e = 0.025
    u = 0.003

    lat = 55.2
    lon = 12.2

    x, y, z = neu2xyz(n, e, u, lat, lon)
    N, E, U = xyz2neu(x, y, z, lat, lon)

    # undgå fejl pga floating point afrunding
    assert isclose(n, N)
    assert isclose(e, E)
    assert isclose(u, U)


def test_Rneu_xyz():
    """
    Test at rotationsmatrixen kan levere en fejlfri frem- og tilbage rotation.
    """

    R = Rneu_xyz(55.2, 12.2)
    cov_neu = R.T @ COV_XYZ @ R
    cov_xyz_return = R @ cov_neu @ R.T

    assert np.allclose(COV_XYZ, cov_xyz_return)
