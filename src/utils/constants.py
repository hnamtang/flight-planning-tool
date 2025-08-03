"""
Relevant physical and aviation constants
"""

FT2M = 0.3048  # ft to m
NM2M = 1852  # NM to m
KTS2MPS = 0.514444  # kts to m/s
G_CONST = 9.80665  # gravity [m/s^2]
R_EARTH_EQUATORIAL = 6378137  # [m]

MAPPING_NAV_TO_CODE = {
    "VOR": "D",
    "RNAV": "R",
    "GLS": "J",
    "ILS": "I",
    "NDB/DME": "Q",
    "NDB": "N",
}
MAPPING_CODE_TO_NAV = {
    "D": "VOR",
    "R": "RNAV",
    "J": "GLS",
    "I": "ILS",
    "Q": "NDB/DME",
    "N": "NDB",
}
