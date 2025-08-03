import csv
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

from .config import DATA_DIR, PROJECT_ROOT


def load_airport_codes(airports_dir_path):
    airport_codes = sorted([f.stem for f in airports_dir_path.glob("*.txt")])

    return airport_codes


def load_rwy_coords(airport_icao, rwy_id):
    airports_file_path = DATA_DIR / "Airports.txt"

    airport_found = False
    with open(airports_file_path, "r") as fid:
        for line in fid:
            parts = line.strip().split(",")
            if parts[0] == "A" and parts[1] == airport_icao.upper():
                airport_found = True
            elif airport_found and parts[0] == "R" and parts[1] == rwy_id.upper():
                rwy_lat = float(parts[8])
                rwy_lon = float(parts[9])
                break
    return rwy_lat, rwy_lon


def load_wpt_coords(wpt_file_path):
    df = pd.read_csv(wpt_file_path, delimiter=",", header=None, index_col=False)
    df_wpts = df.iloc[:, 0:3]
    df_wpts.insert(3, 3, np.zeros(shape=(len(df),)))
    df_wpts.columns = ["name", "lat", "lon", "h"]

    return df_wpts


def load_leg_data(
    lat_prev,
    lon_prev,
    lat_wpt,
    lon_wpt,
    leg_type,
    leg_category,
    turn_radius,
    **kwargs,
):
    """
    Generate required leg data with flyby information if exists.

    Parameters
    ----------
    lat_prev, lon_prev : float
        Latitude and longitude of the previous point [deg]
    lat_wpt, lon_wpt : float
        Latitude and longitude of the current point [deg]
    leg_type : str
        Type of the current leg
    leg_category : str
        Category of the leg 'sid', 'enroute', or 'star'
    turn_radius : float
        Turn radius calculated from current altitude, TAS and bank angle [m]
    kwargs : dict
        A mandatory dictionary that contains fly-by data. If no fly-by, set the value
        to `None`. The required dictionary keys and values are:

            # * `is_flyby_prev` : bool
            #     If True, the previous waypoint is a fly-by waypoint. It helps the leg
            #     generation funcion pick the correct starting point coordinate
            * `is_flyby_current` : bool
                If True, the current waypoint is a fly-by waypoint. It helps the leg
                generation function pick the correct end point coordinate
            * 'flyby_center_lat', 'flyby_center_lon' : float or None
                Latitude and longitude of the center arc [deg]
            * 'flyby_start_lat', 'flyby_start_lon' : float or None
                Latitude and longitude of the arc start [deg]
            * 'flyby_end_lat', 'flyby_end_lon' : float or None
                Latitude and longitude of the arc end [deg]
            * 'crs' : float
                Predefined constant magnetic course [deg]. Required for 'CF' leg
            * 'center_lat', 'center_lon' : float
                Latitude and longitude of the center of the RF leg [deg]. Required for
                'RF' leg

    Returns
    -------
    leg_data : dict
        A dictionary contains all required information for leg generation
    """
    # Validate leg_category
    leg_category = leg_category.lower()
    if leg_category not in ("sid", "enroute", "star"):
        raise ValueError(
            f"leg_category must be one of 'sid', 'enroute', 'star'. Got {leg_category}"
        )

    # Validate leg_type
    leg_types = {
        "IF",
        "TF",
        "CF",
        "DF",
        "FA",
        "FC",
        "FD",
        "FM",
        "CA",
        "CD",
        "CI",
        "CR",
        "RF",
        "AF",
        "VA",
        "VD",
        "VI",
        "VM",
        "VR",
        "PI",
        "HA",
        "HF",
        "HM",
    }
    supported_leg_types = {"CF", "DF", "RF", "TF"}
    if leg_type == "IF":
        warnings.warn(
            "IF leg indicates start of IFP. Use TF leg type as fallback.",
            UserWarning,
        )
        leg_type = "TF"
    elif leg_type in leg_types - supported_leg_types:
        raise ValueError(f"{leg_type} leg currently not supported.")
    elif leg_type not in supported_leg_types:
        raise ValueError("Invalid leg_type")

    # Validate kwargs
    expected_keys = {
        "is_flyby",
        "flyby_center_lat",
        "flyby_center_lon",
        "flyby_start_lat",
        "flyby_start_lon",
        "flyby_end_lat",
        "flyby_end_lon",
    }
    if leg_type.upper() == "RF":
        expected_keys.update(("center_lat", "center_lon"))
    elif leg_type.upper() == "CF":
        expected_keys.add("crs")
    kwargs_keys = set(kwargs.keys())
    if kwargs_keys != expected_keys:
        missing_keys = expected_keys - kwargs_keys
        extra_keys = kwargs_keys - expected_keys
        err_msg = []
        if missing_keys:
            err_msg.append(f"Missing key(s): {sorted(missing_keys)}")
        if extra_keys:
            err_msg.append(f"Invalid key(s): {sorted(extra_keys)}")
        err_msg = "; ".join(err_msg)
        raise ValueError(f"Invalid keyword arguments. {err_msg}")

    # Create required leg data
    is_flyby = kwargs["is_flyby"]
    leg_data = {
        "lat": [lat_prev, lat_wpt],
        "lon": [lon_prev, lon_wpt],
        "is_flyby": is_flyby,
        "turn_radius": turn_radius,
    }
    if is_flyby:
        leg_data.update(
            flyby_center_lat=kwargs["flyby_center_lat"],
            flyby_center_lon=kwargs["flyby_center_lon"],
            flyby_start_lat=kwargs["flyby_start_lat"],
            flyby_start_lon=kwargs["flyby_start_lon"],
            flyby_end_lat=kwargs["flyby_end_lat"],
            flyby_end_lon=kwargs["flyby_end_lon"],
        )
    if leg_type.upper() == "RF":
        leg_data.update(
            center_lat=kwargs["center_lat"],
            center_lon=kwargs["center_lon"],
            leg_type="RF",
        )
    elif leg_type.upper() == "CF":
        leg_data.update(crs=kwargs["crs"], leg_type=leg_type.upper())
    else:
        leg_data["leg_type"] = leg_type.upper()

    return leg_data


def save_trajectory_to_csv(
    trajectory,
    org_airport,
    dest_airport,
):
    """
    Save trajectory data to a CSV file with columns: id, lat, lon, segment
    """
    output_dir_path = PROJECT_ROOT / "output"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    time_formatted = now.strftime("%Y-%m-%d_%H-%M")
    output_filename = f"{org_airport}-{dest_airport}_{time_formatted}"
    output_file_path = output_dir_path / f"{output_filename}.csv"

    with open(output_file_path, "w", newline="\n") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["lat", "lon", "segment"])  # Header

        # SID
        for lat, lon in trajectory["departure_phase"]:
            writer.writerow([lat, lon, "SID"])
        # En route
        for lat, lon in trajectory["enroute_phase"]:
            writer.writerow([lat, lon, "Enroute"])
        # STAR
        for lat, lon in trajectory["arrival_phase"]:
            writer.writerow([lat, lon, "STAR"])

    print(f"Trajectory saved to: {output_file_path}")
