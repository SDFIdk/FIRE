from fire.api import FireDb


def test_has_session(firedb: FireDb):
    assert hasattr(firedb, "session")


def test_konfiguration(firedb: FireDb):
    assert firedb.basedir_materiale == r"F:\GDB\FIRE\materiale"
    assert firedb.basedir_skitser == r"F:\GDB\FIRE\skitser"
