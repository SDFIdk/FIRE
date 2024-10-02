from datetime import datetime

import click
import pandas as pd
from sqlalchemy.exc import NoResultFound

import fire.cli
from fire.api.model import (
    Tidsserie,
    HøjdeTidsserie,
)
from fire.cli.ts import (
    _find_tidsserie,
    _udtræk_tidsserie,
)
from fire.cli.ts.statistik_ts import (
    StatistikHts,
    beregn_statistik_til_hts_rapport,
)
from fire.cli.ts.plot_ts import (
    plot_tidsserie,
    plot_data,
    plot_fit,
    plot_konfidensbånd,
)

from . import ts

HTS_PARAMETRE = {
    "t": "t",
    "decimalår": "decimalår",
    "kote":"kote",
    "sz": "sz",
}

