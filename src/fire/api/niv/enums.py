from enum import Enum


class NivMetode(Enum):
    MGL = 1
    MotoriseretGeometriskNivellement = 1
    MTL = 2
    MotoriseretTrigonometriskNivellement = 2


class Nøjagtighed(Enum):
    P = 1
    Præcision = 1
    K = 2
    Kvalitet = 2
    D = 3
    Detail = 3
    U = 9
    Ukendt = 9
