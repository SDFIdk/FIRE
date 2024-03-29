import pandas as pd

from fire.io.regneark import (
    nyt_ark,
    arkdef,
)

from fire.cli.niv._ilæg_revision import (
    udfyld_udeladte_identer,
)


def test_udfyld_udeladte_identer():
    input_data = [
        dict(Punkt="FYNO"),
        dict(Punkt=""),
        dict(Punkt=""),
        dict(Punkt="SKEJ"),
        dict(Punkt=""),
        dict(Punkt=""),
        dict(Punkt="BOBO"),
        dict(Punkt=""),
        dict(Punkt=""),
    ]
    df_input_data = pd.DataFrame(input_data)
    ark = pd.concat([nyt_ark(arkdef.REVISION), df_input_data], ignore_index=True)

    output_data = [
        dict(Punkt="FYNO"),
        dict(Punkt="FYNO"),
        dict(Punkt="FYNO"),
        dict(Punkt="SKEJ"),
        dict(Punkt="SKEJ"),
        dict(Punkt="SKEJ"),
        dict(Punkt="BOBO"),
        dict(Punkt="BOBO"),
        dict(Punkt="BOBO"),
    ]
    df_output_data = pd.DataFrame(output_data)
    expected = pd.concat([nyt_ark(arkdef.REVISION), df_output_data], ignore_index=True)

    result = udfyld_udeladte_identer(ark)
    assert all(
        result.Punkt == expected.Punkt
    ), f"Expected \n\n{result}\n\nto be\n\n{expected}\n\n."
