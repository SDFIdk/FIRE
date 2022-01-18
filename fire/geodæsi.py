from math import sin
from math import cos
import datetime

import numpy as np


def neu2xyz(dN, dE, dU, lat, lon):
    """
    Convert from NEU-space to cartesian XYZ-space.
    NEU -> XYZ formula described in
    Nørbech, T., et al, 2003(?), "Transformation from a Common Nordic Reference
    Frame to ETRS89 in Denmark, Finland, Norway, and Sweden – status report"
    """
    dX = -sin(lat) * cos(lon) * dN - sin(lon) * dE + cos(lat) * cos(lon) * dU
    dY = -sin(lat) * sin(lon) * dN + cos(lon) * dE + cos(lat) * sin(lon) * dU
    dZ = cos(lat) * dN + sin(lat) * dU

    return (dX, dY, dZ)


def xyz2neu(dX, dY, dZ, lat, lon):
    """
    Convert from cartesian XYZ-space to NEU-space.
    Solves the inverse set of equations described in (Nørbech, 2003(?))
    numerically.
    """
    # b = Ax, solve for x
    b = np.array([dX, dY, dZ])
    A = np.array(
        [
            [-sin(lat) * cos(lon), -sin(lon), cos(lat) * cos(lon)],
            [-sin(lat) * sin(lon), cos(lon), cos(lat) * sin(lon)],
            [cos(lat), 0, sin(lat)],
        ]
    )

    x = np.linalg.solve(A, b)

    return (x[0], x[1], x[2])


def datetime2decimalår(date) -> float:
    """
    Modificeret fra https://stackoverflow.com/a/36949905
    """
    start = datetime.date(date.year, 1, 1).toordinal()
    year_length = datetime.date(date.year + 1, 1, 1).toordinal() - start
    return date.year + float(date.toordinal() - start) / year_length
