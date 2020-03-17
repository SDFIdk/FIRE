from fire.api import FireDb

from fire.api.model.punkttyper import PunktInformationType


def test_has_session(firedb: FireDb):
    assert hasattr(firedb, "session")
