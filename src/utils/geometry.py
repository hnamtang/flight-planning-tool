import numpy as np


def wrap_to_90(angle):
    """
    Wrap angle(s) to range [-90, 90]. This function is relevant for wrapping latitude(s).

    Parameters
    ----------
    angle : float or np.ndarray
        Angle(s) in deg

    Returns
    -------
    angle_wrap : float or np.ndarray
        Angle(s) in deg in range [-90, 90]
    """
    angle_arr = np.asarray(angle)
    angle_wrap = (angle_arr + 180) % 360 - 180  # range [-180, 180]
    angle_wrap = np.where(angle_wrap > 90, 180 - angle_wrap, angle_wrap)
    angle_wrap = np.where(angle_wrap < -90, -180 - angle_wrap, angle_wrap)

    return angle_wrap.item() if np.isscalar(angle) else angle_wrap


def wrap_to_180(angle):
    """
    Wrap angle(s) to range [-180, 180]. This function is relevant for wrapping longitude(s).

    Parameters
    ----------
    angle : float or np.ndarray
        Angle(s) in deg

    Returns
    -------
    angle_wrap : float or np.ndarray
        Angle(s) in deg in range [-180, 180]
    """
    angle_arr = np.asarray(angle)
    angle_wrap = (angle_arr + 180) % (2 * 180) - 180

    return angle_wrap.item() if np.isscalar(angle) else angle_wrap
