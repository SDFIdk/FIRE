import pandas as pd

from fire.io.regneark import (
    nyt_ark,
    arkdef,
)

from fire.cli.niv._ilæg_revision import (
    udfyld_udeladte_identer,
)


def test_udfyld_udeladte_identer():
    test_data = "asdf"
    ark = nyt_ark(arkdef.REVISION)
