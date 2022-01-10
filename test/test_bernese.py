"""
Kør Bernese fillæser med testdata
"""
import math
from pathlib import Path

from fire.io.bernese import BerneseSolution, Kovarians


def test():
    """
    Indlæs og test output fra tre konkrete sæt med forskellige værdier og sektionsformater
    """
    # Datasæt 1 - første sæt, uden eksisterende COV-fil eller spredning

    reader1 = BerneseSolution(
        addneq_fil=Path(
            "test/data/ADDNEQ2_1273"  # denne fil har ingen spredningssektion
        ),
        crd_fil=Path("test/data/COMB1273.CRD"),
        cov_fil=None,
    )  # undlad at angive COV-fil
    assert reader1.gnss_uge == 1273
    assert reader1.epoke.year == 2004
    assert reader1.epoke.month == 6
    assert reader1.epoke.day == 2
    assert reader1.epoke.second == 0
    assert reader1.epoke.microsecond == 0
    assert reader1.datum == "IGb08"
    assert math.isclose(reader1.a_posteriori_RMS, 0.00102)
    assert reader1.__sizeof__() == 640
    assert reader1["MAR6"].spredning is None
    assert reader1["HERT"].kovarians is None
    assert reader1["HHLM"].flag == "A"
    assert reader1["BOR1"].obsstart.year == 2004
    assert reader1["BOR1"].obsstart.month == 6
    assert reader1["BOR1"].obsstart.day == 1
    assert reader1["BOR1"].obsstart.hour == 0
    assert reader1["BOR1"].obsstart.minute == 0
    assert reader1["BOR1"].obsstart.second == 0
    assert reader1["BOR1"].obsslut.year == 2004
    assert reader1["BOR1"].obsslut.month == 6
    assert reader1["BOR1"].obsslut.day == 3
    assert reader1["BOR1"].obsslut.hour == 23
    assert reader1["BOR1"].obsslut.minute == 59
    assert reader1["BOR1"].obsslut.second == 30
    assert str(reader1["BOR1"].obslængde) == "2 days, 23:59:30"
    assert math.isclose(a=float(reader1["BUDP"].koordinat.x), b=3513638.26170)
    assert math.isclose(a=float(reader1["BUDP"].koordinat.y), b=778956.38829)
    assert math.isclose(a=float(reader1["BUDP"].koordinat.z), b=5248216.43002)
    assert math.isclose(a=float(reader1["BOR1"].rms_fejl), b=0.00047)

    # Datasæt 2 - tidligste sæt med alle tre filer

    reader2 = BerneseSolution(
        addneq_fil=Path("test/data/ADDNEQ2_1886"),
        crd_fil=Path("test/data/COMB1886.CRD"),
        cov_fil=Path("test/data/COMB1886.COV"),
    )
    assert reader2.gnss_uge == 1886
    assert reader2.epoke.year == 2016
    assert reader2.epoke.month == 3
    assert reader2.epoke.day == 4
    assert reader2.epoke.second == 0
    assert reader2.epoke.microsecond == 0
    assert reader2.datum == "IGb08"
    assert math.isclose(reader2.a_posteriori_RMS, 0.00091)
    assert reader2.__sizeof__() == 1176
    assert math.isclose(a=float(reader2["MAR6"].spredning.n), b=0.12)
    assert math.isclose(a=float(reader2["MAR6"].spredning.e), b=0.11)
    assert math.isclose(a=float(reader2["MAR6"].spredning.u), b=0.36)
    assert reader2["ESBC"].kovarians == Kovarians(
        xx=0.1442016297,
        yy=0.02864337257,
        zz=0.2674335932,
        yx=0.01928893236,
        zx=0.1507957187,
        zy=0.02412103176,
    )
    assert reader2["FYHA"].flag == "A"
    assert math.isclose(a=float(reader2["BUDP"].koordinat.x), b=3513638.07857)
    assert math.isclose(a=float(reader2["BUDP"].koordinat.y), b=778956.56481)
    assert math.isclose(a=float(reader2["BUDP"].koordinat.z), b=5248216.53648)
    assert math.isclose(a=float(reader2["BUDP"].rms_fejl), b=0.00047)

    # Datasæt 3 - nyeste sæt med alle tre filer

    reader3 = BerneseSolution(
        addneq_fil=Path("test/data/ADDNEQ2_2096"),
        crd_fil=Path("test/data/COMB2096.CRD"),
        cov_fil=Path("test/data/COMB2096.COV"),
    )

    assert reader3.gnss_uge == 2096
    assert reader3.epoke.year == 2020
    assert reader3.epoke.month == 3
    assert reader3.epoke.day == 11
    assert reader3.epoke.second == 0
    assert reader3.epoke.microsecond == 0
    assert reader3.__sizeof__() == 1176
    assert reader3.datum == "IGS14"
    assert math.isclose(reader3.a_posteriori_RMS, 0.00101)
    assert reader3["RIKO"].obsstart.year == 2020
    assert reader3["RIKO"].obsstart.month == 3
    assert reader3["RIKO"].obsstart.day == 10
    assert reader3["RIKO"].obsstart.hour == 0
    assert reader3["RIKO"].obsstart.minute == 0
    assert reader3["RIKO"].obsstart.second == 0
    assert reader3["RIKO"].obsslut.year == 2020
    assert reader3["RIKO"].obsslut.month == 3
    assert reader3["RIKO"].obsslut.day == 12
    assert reader3["RIKO"].obsslut.hour == 23
    assert reader3["RIKO"].obsslut.minute == 59
    assert reader3["RIKO"].obsslut.second == 30

    assert math.isclose(a=float(reader3["MAR6"].spredning.n), b=0.91)
    assert math.isclose(a=float(reader3["MAR6"].spredning.e), b=1.02)
    assert math.isclose(a=float(reader3["MAR6"].spredning.u), b=2.98)
    assert reader3["ONSA"].kovarians == Kovarians(
        xx=0.06792032947,
        yy=0.01283152234,
        zz=0.1508975287,
        yx=0.01151628674,
        zx=0.07605137984,
        zy=0.01515196666,
    )
    assert reader3["FYHA"].flag == "A"
    assert math.isclose(a=float(reader3["BUDP"].koordinat.x), b=3513638.01440)
    assert math.isclose(a=float(reader3["BUDP"].koordinat.y), b=778956.62349)
    assert math.isclose(a=float(reader3["BUDP"].koordinat.z), b=5248216.57412)
    assert math.isclose(a=float(reader3["BUDP"].rms_fejl), b=0.00042)


if __name__ == "__main__":
    test()
