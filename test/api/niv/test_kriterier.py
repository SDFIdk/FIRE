from fire.api.niv.datatyper import (
    NivMetode,
    Nøjagtighed,
)
from fire.api.niv.kriterier import (
    FORKASTELSESKRITERIUM,
    EMPIRISK_SPREDNING,
    mildeste_kvalitetskrav,
)


def test_mildeste_kvalitetskrav():
    # Genveje
    # Medlemmer
    P, K, D = (Nøjagtighed.P, Nøjagtighed.K, Nøjagtighed.D)
    MGL, MTL = (NivMetode.MGL, NivMetode.MTL)
    # Aliaser
    P_alias, K_alias, D_alias = (
        Nøjagtighed.Præcision,
        Nøjagtighed.Kvalitet,
        Nøjagtighed.Detail,
    )
    MGL_alias, MTL_alias = (
        NivMetode.MotoriseretGeometriskNivellement,
        NivMetode.MotoriseretTrigonometriskNivellement,
    )

    # Test medlemmer
    test_data = (
        # EMPIRISK_SPREDNING
        ([P, K, D], [MGL], EMPIRISK_SPREDNING, 1.5),
        ([P, D], [MGL], EMPIRISK_SPREDNING, 1.5),
        ([K, D], [MGL], EMPIRISK_SPREDNING, 1.5),
        ([D], [MGL], EMPIRISK_SPREDNING, 1.5),
        ([P, K], [MGL], EMPIRISK_SPREDNING, 1.0),
        ([K], [MGL], EMPIRISK_SPREDNING, 1.0),
        ([P], [MGL], EMPIRISK_SPREDNING, 0.6),
        ([P_alias, K_alias, D_alias], [MGL_alias], EMPIRISK_SPREDNING, 1.5),
        ([P_alias, K_alias], [MGL_alias], EMPIRISK_SPREDNING, 1.0),
        ([P_alias], [MGL_alias], EMPIRISK_SPREDNING, 0.6),
        ([P, K, D], [MTL], EMPIRISK_SPREDNING, 3.0),
        ([P, K], [MTL], EMPIRISK_SPREDNING, 2.0),
        ([P], [MTL], EMPIRISK_SPREDNING, 1.5),
        ([P_alias, K_alias, D_alias], [MTL_alias], EMPIRISK_SPREDNING, 3.0),
        ([P_alias, K_alias], [MTL_alias], EMPIRISK_SPREDNING, 2.0),
        ([P_alias], [MTL_alias], EMPIRISK_SPREDNING, 1.5),
        # FORKASTELSESKRITERIUM
        ([P, K, D], [MGL], FORKASTELSESKRITERIUM, 3.0),
        ([P, K], [MGL], FORKASTELSESKRITERIUM, 2.5),
        ([P], [MGL], FORKASTELSESKRITERIUM, 2.0),
        ([P_alias, K_alias, D_alias], [MGL_alias], FORKASTELSESKRITERIUM, 3.0),
        ([P_alias, K_alias], [MGL_alias], FORKASTELSESKRITERIUM, 2.5),
        ([P_alias], [MGL_alias], FORKASTELSESKRITERIUM, 2.0),
        ([P, K, D], [MTL], FORKASTELSESKRITERIUM, 3.0),
        ([P, K], [MTL], FORKASTELSESKRITERIUM, 2.5),
        ([P], [MTL], FORKASTELSESKRITERIUM, 2.0),
        ([P_alias, K_alias, D_alias], [MTL_alias], FORKASTELSESKRITERIUM, 3.0),
        ([P_alias, K_alias], [MTL_alias], FORKASTELSESKRITERIUM, 2.5),
        ([P_alias], [MTL_alias], FORKASTELSESKRITERIUM, 2.0),
    )
    for *input_data, expected in test_data:
        result = mildeste_kvalitetskrav(*input_data)
        assert result == expected, f"Forventede, at {result!r} var {expected}."
