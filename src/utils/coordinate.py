import numpy as np
import pandas as pd
from pyproj import Transformer


def llh2ecef(llh):
    """
    Transform Latitude, Longitude, Height (WGS 84, EPSG code: 4979) to
    Earth-Centered-Earth-Fixed (WGS 84, EPSG code: 4978).

    Parameters
    ----------
    llh : list or np.ndarray or pd.DataFrame
        Latitude [deg], longitude [deg], height [m] coordinate.

            * llh : list
                A list contains tuples of the form (`lat`, `lon`, `height`)
                or (`lat`, `lon`). Each tuple is a point.
            * llh : np.ndarray
                A Numpy array with shape (n, 3) or shape (n, 2), where each row is a point
                and columns indicate latitude, longitude, and height in that order,
                if height values are provided.
            * llh : pd.DataFrame
                A Pandas DataFrame with of shape (n, 4) or shape (n, 3), where each row
                is a point and columns indicate ICAO id, latitude, longitude, and height
                in that order, if height values are provided. Column names may be provided
                but are not required.

    Returns
    -------
    ecef : list or np.ndarray or pd.DataFrame
        Earth-Centered-Earth-Fixed coordinate (x, y, z) stored with the same instance
        as input instance [m]

    Note
    ----
        Conversion using pyproj, which is a Python interface to PROJ (cartographic
        projections and coordinate transformations library).
    """
    transformer = Transformer.from_crs("epsg:4326", "epsg:4978", always_xy=True)

    if isinstance(llh, list):
        if len(llh[0]) == 2:
            lat, lon = zip(*llh)
            h = np.zeros(shape=(len(lat),))
        elif len(llh[0]) == 3:
            lat, lon, h = zip(*llh)
        x, y, z = transformer.transform(lon, lat, h)
        ecef = [(x_i, y_i, z_i) for x_i, y_i, z_i in zip(x, y, z)]
    elif isinstance(llh, np.ndarray):
        if llh.shape[1] == 2:
            lat, lon = llh.T
            h = np.zeros(shape=(llh.shape[0],))
        elif llh.shape[1] == 3:
            lat, lon, h = llh.T
        x, y, z = transformer.transform(lon, lat, h)
        ecef = np.column_stack([x, y, z])
    elif isinstance(llh, pd.DataFrame):
        column_names = pd.api.types.is_object_dtype(llh.columns)
        if llh.shape[1] == 3:
            if column_names:
                lat, lon = llh["lat"], llh["lon"]
            else:
                lat, lon = llh.iloc[:, 1], llh.iloc[:, 2]
            h = np.zeros(shape=(llh.shape[0],))
        elif llh.shape[1] == 4:
            if column_names:
                lat, lon, h = llh["lat"], llh["lon"], llh["h"]
            else:
                lat, lon, h = (
                    llh.iloc[:, 1],
                    llh.iloc[:, 2],
                    llh.iloc[:, 3],
                )
        x, y, z = transformer.transform(lon, lat, h)
        ecef = pd.DataFrame({"name": llh["name"], "x": x, "y": y, "z": z})
    else:
        raise TypeError("Unsupported input type.")

    return ecef


def ecef2llh(ecef):
    """
    Transform Earth-Centered-Earth-Fixed (WGS 84, EPSG code: 4978) to
    Latitude, Longitude, Height (WGS 84, EPSG code: 4979).

    Parameters
    ----------
    ecef : list or np.ndarray or pd.DataFrame
        x, y, z coordinate [m].

            * ecef : list
                A list contains tuples of the form (`x`, `y`, `z`). Each tuple is a point.
            * ecef : np.ndarray
                A Numpy array with shape (n, 3), where each row is a point
                and columns indicate x, y, z coordinate in that order.
            * ecef : pd.DataFrame
                A Pandas DataFrame with of shape (n, 3), where each row is a point and
                columns indicate x, y, z in that order. Column names may be provided
                but are not required.

    Returns
    -------
    llh : list or np.ndarray or pd.DataFrame
        Latitude, Longitude coordinate (lat, lon) stored with the same instance
        as input instance [deg]

    Note
    ----
        Conversion using pyproj, which is a Python interface to PROJ (cartographic
        projections and coordinate transformations library).
    """
    transformer = Transformer.from_crs("epsg:4978", "epsg:4326", always_xy=True)

    if isinstance(ecef, list):
        x, y, z = zip(*ecef)
        lon, lat, _ = transformer.transform(x, y, z)
        llh = [(lat_i, lon_i) for lat_i, lon_i in zip(lat, lon)]
    elif isinstance(ecef, np.ndarray):
        x, y, z = ecef.T
        lon, lat, _ = transformer.transform(x, y, z)
        llh = np.column_stack([lat, lon])
    elif isinstance(ecef, pd.DataFrame):
        column_names = pd.api.types.is_object_dtype(ecef.columns)
        if column_names:
            x, y, z = ecef["x"], ecef["y"], ecef["z"]
        else:
            x, y, z = ecef.iloc[:, 0], ecef.iloc[:, 1], ecef.iloc[:, 2]
        lon, lat, _ = transformer.transform(x, y, z)
        llh = pd.DataFrame({"name": ecef["name"], "lat": lat, "lon": lon})
    else:
        raise TypeError("Unsupported input type.")

    return llh
