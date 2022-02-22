from fire.api import FireDb


def test_has_session(firedb: FireDb):
    assert hasattr(firedb, "session")
