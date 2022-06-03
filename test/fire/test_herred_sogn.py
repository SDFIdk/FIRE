from fire.herred_sogn import (
    kan_være_opmålingsdistrikt,
)


def test_kan_være_opmålingsdistrikt():
    opmålingsdistrikter = [
        # fmt: off
        "15-04",  "25-11",  "29-10",  "33-06",  "39-02",  "45-01",
        "47-10",  "47-12",  "47-14",  "48-18",  "48-11",  "54-11",
        "56-01",  "59-01",  "59-02",  "62-12",  "62-06",  "69-05",
        "69-02",  "70-01",  "70-09",  "78-06",  "82-14",  "82-07",
        "87-04",  "93-11",  "93-13", "104-04", "104-07", "113-01",
        "119-20", "134-13", "137-02", "138-03", "138-04", "140-04",
        # fmt: on
    ]
    for kandidat in opmålingsdistrikter:
        assert kan_være_opmålingsdistrikt(
            kandidat
        ), f"{kandidat=} burde være et opmålingsdistrikt."

    ej_opmålingsdistrikter = [
        "asdf",
    ]
    for kandidat in ej_opmålingsdistrikter:
        assert not kan_være_opmålingsdistrikt(
            kandidat
        ), f"{kandidat=} burde ikke være et opmålingsdistrikt."
