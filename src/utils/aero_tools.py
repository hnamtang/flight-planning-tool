import numpy as np
import math as math

def atmos(geom_alt):
    # Tabulated data (geometric altitude)
    Z = np.array([-10, 0, 2500, 5000, 10000, 11100, 15000, 20000, 47400, 51000])
    H = np.array([-10, 0, 2499, 4996, 9984, 11081, 14965, 19937, 47049, 50594])
    ppo = np.array([1, 1, 0.737, 0.533, 0.262, 0.221, 0.12, 0.055, 0.0011, 0.0007])
    rro = np.array([1, 1, 0.781, 0.601, 0.338, 0.293, 0.159, 0.073, 0.0011, 0.0007])
    T = np.array([288.15, 288.15, 271.906, 255.676, 223.252, 216.65, 216.65,
                  216.65, 270.65, 270.65])
    a = np.array([340.294, 340.294, 330.563, 320.545, 299.532, 295.069, 295.069,
                  295.069, 329.799, 329.799])

    # Constants
    R = 6367435.0       # Mean radius of the Earth (m)
    DENS0 = 1.225       # Sea level air density (kg/m³)
    PRES0 = 101300.0    # Sea level air pressure (N/m²)

    # Compute geopotential altitude
    geop_alt = R * geom_alt / (R + geom_alt)

    # Interpolate temperature and speed of sound
    temp = np.interp(geop_alt, Z, T)
    sound_speed = np.interp(geop_alt, Z, a)

    # Exponential interpolation for pressure and density
    air_pres = None
    air_dens = None
    for k in range(1, len(Z)):
        if geom_alt <= Z[k]:
            betap = np.log(ppo[k] / ppo[k - 1]) / (Z[k] - Z[k - 1])
            betar = np.log(rro[k] / rro[k - 1]) / (Z[k] - Z[k - 1])
            air_pres = PRES0 * ppo[k - 1] * np.exp(betap * (geom_alt - Z[k - 1]))
            air_dens = DENS0 * rro[k - 1] * np.exp(betar * (geom_alt - Z[k - 1]))
            break

    # If outside the tabulated range, return None
    if air_pres is None or air_dens is None:
        raise ValueError("Altitude out of interpolation range")

    return air_dens, air_pres, temp, sound_speed

"""
Convert Calibrated Airspeed (CAS) to True Airspeed (TAS)

Parameters:
    Vcas : float or np.ndarray
        Calibrated Airspeed (m/s)
    rho : float or np.ndarray
        Local air density (kg/m^3)
    p : float or np.ndarray
        Local air pressure (Pa)

Returns:
    Vtas : float or np.ndarray
        True Airspeed (m/s)
"""
def cas_to_tas(Vcas, rho, p):
    
    # Constants
    R = 287.05287         # Specific gas constant for air [J/(kg·K)]
    kappa = 1.4
    mu = (kappa - 1) / kappa

    # Sea-level reference conditions
    rho0, p0, temp0, soundSpeed0 = atmos(0.0)

    # Compute TAS
    temp1 = 1 + (mu / 2) * (rho0 / p0) * Vcas**2
    temp2 = temp1**(1 / mu) - 1
    temp3 = 1 + (p0 / p) * temp2
    temp4 = temp3**mu - 1
    temp5 = (2 / mu) * (p / rho) * temp4
    Vtas = np.sqrt(temp5)

    return Vtas

"""
Convert True Airspeed (TAS) to Calibrated Airspeed (CAS)

Parameters:
    Vtas : float or np.ndarray
        True Airspeed (m/s)
    rho : float or np.ndarray
        Local air density (kg/m^3)
    p : float or np.ndarray
        Local air pressure (Pa)

Returns:
    Vcas : float or np.ndarray
        Calibrated Airspeed (m/s)
"""
def tas_to_cas(Vtas, rho, p):
    
    # Constants
    R = 287.05287         # Specific gas constant [J/(kg·K)]
    gamma = 1.4
    mu = (gamma - 1) / gamma

    # Sea-level reference conditions
    rho0, p0, temp0, soundSpeed0 = atmos(0.0)

    # Compute CAS from TAS
    temp1 = 1 + (mu / 2) * (rho / p) * Vtas**2
    temp2 = temp1**(1 / mu) - 1
    temp3 = 1 + (p / p0) * temp2
    temp4 = temp3**mu - 1
    temp5 = (2 / mu) * (p0 / rho0) * temp4

    Vcas = np.sqrt(temp5)

    return Vcas


"""
Conversion from Mach number to True Airspeed (TAS)

Parameters:
M : float
    Mach number
rho : float
    Air density (kg/m^3)
p : float
    Air pressure (Pa)

Returns:
Vtas : float
    True Airspeed (m/s)
"""
def m_to_tas(M, rho, p):
    
    gamma = 1.4  # Ratio of specific heats for air
    Vtas = M * math.sqrt(gamma * p / rho)
    return Vtas

"""
Conversion from True Airspeed (TAS) to Mach number

Parameters:
Vtas : float
    True Airspeed (m/s)
rho : float
    Air density (kg/m^3)
p : float
    Air pressure (Pa)

Returns:
M : float
    Mach number
"""
def tas_to_m(Vtas, rho, p):
    
    gamma = 1.4  # Ratio of specific heats for air
    M = Vtas / math.sqrt(gamma * p / rho)
    return M