from .cf_leg import CFLegGenerator
from .df_leg import DFLegGenerator
from .load_leg_data import load_leg_data
from .rf_leg import RFLegGenerator
from .tf_leg import TFLegGenerator

__all__ = [
    "CFLegGenerator",
    "DFLegGenerator",
    "RFLegGenerator",
    "TFLegGenerator",
    load_leg_data,
]

LEG_GENERATORS = {
    "CF": CFLegGenerator,
    "DF": DFLegGenerator,
    "RF": RFLegGenerator,
    "TF": TFLegGenerator,
}
