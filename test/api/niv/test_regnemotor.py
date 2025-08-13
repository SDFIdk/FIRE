from pathlib import Path

from click.testing import CliRunner

from fire.api.niv.regnemotor import (
    RegneMotor,
    GamaRegn,
)
from fire.cli.niv import (
    find_faneblad,
)
from fire.io.regneark import arkdef


def test_fra_dataframe():
    """Tester at man kan instantiere et RegneMotor objekt via dataframes"""
    runner = CliRunner()

    filename = "test_regn.xlsx"
    projektnavn = "test_regn"
    with open(Path(__file__).resolve().parents[2] / "niv" / filename, "rb") as f:
        filedata = f.read()

    with runner.isolated_filesystem():
        # kopier filer til isoleret filsystem
        with open(filename, "wb") as f:
            f.write(filedata)

        observationer = find_faneblad(
            projektnavn, "Observationer", arkdef.OBSERVATIONER
        )
        punktoversigt = find_faneblad(
            projektnavn, "Punktoversigt", arkdef.PUNKTOVERSIGT
        )

        # Test at en regnemotor kan instantieres ud fra en dataframe
        motor = GamaRegn.fra_dataframe(
            observationer, punktoversigt, projektnavn=projektnavn
        )

        assert isinstance(motor, RegneMotor)

        # Test motorens forskellige attributter
        assert len(motor.observationer) == len(observationer)
        assert len(motor.gamle_koter) == len(punktoversigt)
        assert len(motor.fastholdte) == sum(punktoversigt["Fasthold"] != "")
