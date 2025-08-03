"""
Flight Managemnet and Procedure Design

Routines to read navigation data

Copyright (c) - TU Berlin, Flight Guidance and Air Transport

"""

import numpy as np

# import pandas as pd
from .constants import MAPPING_NAV_TO_CODE

"""
Get the latitude and longitude of a given waypoint from the table.

Parameters:
    table_wpts (pd.DataFrame): A DataFrame where the first column contains waypoint names,
                               the second column contains latitudes,
                               and the third column contains longitudes.
    wpt_name (str): The name of the waypoint.

Returns:
    tuple: (latitude, longitude) of the waypoint.
"""


def get_wpt(table_wpts, wpt_name):
    # Find the row where the first column matches the waypoint name
    row = table_wpts[table_wpts.iloc[:, 0] == wpt_name]

    if row.empty:
        raise ValueError(f"Waypoint '{wpt_name}' not found.")

    # Get latitude and longitude from the second and third columns
    lat = row.iloc[0, 1]
    lon = row.iloc[0, 2]

    return lat, lon


"""
Get the latitude, longitude, and altitude of a navigation aid.

Parameters:
    table_nav (pd.DataFrame): A DataFrame with navigation aid data.
                              Assumes:
                              - Column 0: Short name
                              - Column 1: Full name
                              - Column 6: Latitude
                              - Column 7: Longitude
                              - Column 8: Altitude
    nav_name_short (str): Short name of the navaid.
    nav_name (str): Full name of the navaid.

Returns:
    tuple: (latitude, longitude, altitude)
"""


def get_nav(table_nav, nav_name_short, nav_name):
    # Find the matching row
    row = table_nav[
        (table_nav.iloc[:, 0] == nav_name_short) & (table_nav.iloc[:, 1] == nav_name)
    ]

    if row.empty:
        raise ValueError(f"Navaid '{nav_name_short} / {nav_name}' not found.")

    lat = row.iloc[0, 6]
    lon = row.iloc[0, 7]
    alt = row.iloc[0, 8]

    return lat, lon, alt


"""
Extracts waypoints for a specific arrival and approach from an airport file.

Parameters:
    airport_filename (str): Path to the airport data file.
    arrival (str): Arrival procedure name.
    approach (str): Approach type.

Returns:
    tuple: Lists of waypoint latitudes, longitudes, and names.
"""


def get_arr(airport_filename, arrival, approach):
    wpt_lat = []
    wpt_lon = []
    wpt_name = []

    done = False

    with open(airport_filename, "r") as f:
        lines = f.readlines()
        i = 0

        while i < len(lines) and not done:
            line = lines[i].strip()
            parts = line.split(",")

            if len(parts) >= 4 and parts[1] == arrival and parts[2] == approach:
                i += 1  # Move to the next line where waypoints start
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        break  # Stop if blank line (end of section)

                    b = line.split(",")
                    if len(b) >= 5:
                        wpt_name.append(b[1])
                        try:
                            wpt_lat.append(float(b[2]))
                            wpt_lon.append(float(b[3]))
                        except ValueError:
                            wpt_lat.append(None)
                            wpt_lon.append(None)
                    i += 1

                done = True
            else:
                i += 1

    return wpt_lat, wpt_lon, wpt_name


"""
Reads an airport file and extracts STAR (Standard Terminal Arrival Route) names and runways.
"""


def get_stars(airport_filename):
    stars = []
    stars_rwys = []

    # Open the file for reading
    with open(airport_filename, "r") as star:
        for line in star:
            # Split the line by ','
            parts = line.strip().split(",")

            # Ensure the line has enough parts and is a SID entry
            if len(parts) >= 4 and parts[0] == "STAR":
                stars.append(parts[1])
                stars_rwys.append(parts[2])

    return stars_rwys, stars


"""
Reads an airport file and extracts SID (Standard Instrument Departure) names and runways.
"""


def get_sids(airport_filename):
    sids = []
    sids_rwys = []

    # Open the file for reading
    with open(airport_filename, "r") as fid:
        for line in fid:
            # Split the line by ','
            parts = line.strip().split(",")

            # Ensure the line has enough parts and is a SID entry
            if len(parts) >= 4 and parts[0] == "SID":
                sids.append(parts[1])
                sids_rwys.append(parts[2])

    return sids_rwys, sids


"""
Reads an airport file and extracts transition names, runways, and types.
"""


def get_transitions(airport_filename):
    transitions = {"name": ["---"], "rwys": ["---"], "types": ["---"]}

    # Open the file for reading
    with open(airport_filename, "r") as fid:
        for line in fid:
            # Split the line by ','
            parts = line.strip().split(",")

            # Ensure the line has enough parts and is an APPTR entry
            if len(parts) >= 4 and parts[0] == "APPTR":
                transitions["name"].append(parts[3])
                transitions["rwys"].append(parts[2])
                transitions["types"].append(parts[1])

    return transitions


"""
Reads an airport file and extracts approach runways and types.
"""


def get_approach_rwys(airport_filename):
    approaches = {"rwys": [], "types": [], "full": []}

    # Open the file for reading
    with open(airport_filename, "r") as fid:
        for line in fid:
            # Split the line by ','
            parts = line.strip().split(",")

            if len(parts) >= 4 and parts[0] == "FINAL":
                approaches["rwys"].append(parts[2])
                approaches["types"].append(parts[1])

                app_type = parts[1]

                if len(app_type) > 3 and app_type[3] in ("L", "C", "R"):
                    id_ = app_type[1:4]
                else:
                    id_ = app_type[1:3]

                extra = app_type[4:] if len(app_type) > 4 else ""

                nav = {
                    "D": "VOR",
                    "R": "RNAV (GPS)",
                    "J": "GLS",
                    "I": "ILS",
                    "Q": "NDB/DME",
                    "N": "NDB",
                }.get(app_type[0], "")

                approaches["full"].append(f"{nav} {extra} {id_}")

    return approaches


"""
Reads an airport file and extracts departure runways.
"""


def get_departure_rwys(airport_filename):
    rwys = []

    # Open the file for reading
    with open(airport_filename, "r") as fid:
        for line in fid:
            # Split the line by ','
            parts = line.strip().split(",")

            if len(parts) >= 4 and (parts[0] == "SID" or parts[0] == "FINAL"):
                if parts[2] != "ALL":
                    rwys.append(parts[2])

    # Remove duplicate entries
    rwys = sorted(set(rwys))

    return rwys


"""
Reads an airport file and extracts runway coordinates (latitude, longitude, and height).
"""


def get_rwy_coordinates(airport_filename, rwys):
    rwys_llh = [[0] * len(rwys) for _ in range(3)]  # Initialize 3xN array of zeros

    # Open the file for reading
    with open(airport_filename, "r") as fid:
        for line in fid:
            # Split the line by ','
            parts = line.strip().split(",")

            if len(parts) >= 4 and parts[1].startswith("RW"):
                for jj, rwy in enumerate(rwys):
                    s = "RW" + rwy
                    if parts[1] == s:
                        rwys_llh[0][jj] = float(parts[2])
                        rwys_llh[1][jj] = float(parts[3])
                        rwys_llh[2][jj] = float(parts[11]) - 50.0
                        break

    return rwys_llh


"""
Loads arrival data including approaches, transitions, and STARs.
"""


def load_arrivals(destination_filename):
    stars = get_stars(destination_filename)  # Get all STARs (STAR)
    approaches = get_approach_rwys(destination_filename)  # Get all runways (FINAL)
    transitions = get_transitions(
        destination_filename
    )  # Get approach transitions (APPTR)

    return approaches, transitions, stars


"""
Loads departure data including runways, SIDs, and runway coordinates.
"""


def load_departures(origin_filename):
    departure_rwys = get_departure_rwys(origin_filename)  # Get all departure runways
    rwys_llh = get_rwy_coordinates(
        origin_filename, departure_rwys
    )  # Get coordinates for all runways
    sids_rwys, sids = get_sids(origin_filename)  # Get all SIDs

    return departure_rwys, sids_rwys, sids, rwys_llh


def make_empty_wpts():
    return {
        "line": [],
        "leg_type": [],
        "name": [],
        "lat": [],
        "lon": [],
        "alt_constraint": [],
        "alt_top": [],
        "alt_bottom": [],
        "spd_constraint": [],
        "spd_value": [],
        "crs": [],
        "center_lat": [],
        "center_lon": [],
    }


def parse_waypoint_line(line, wpt, table_fixes):
    # wpt = make_empty_wpts()

    parts = line.split(",")
    wpt["line"].append(line)
    wpt["leg_type"].append(parts[0])
    wpt["name"].append(parts[1])

    if len(parts[0]) > 1 and parts[0][1] == "F":
        wpt["lat"].append(float(parts[2]))
        wpt["lon"].append(float(parts[3]))
    else:
        wpt["lat"].append(np.nan)
        wpt["lon"].append(np.nan)

    # Altitude and speed constraints handling
    if parts[0] in ["TF", "CF", "IF", "DF", "RF"]:
        indices = {
            "TF": (10, 11, 12, 13, 14, None, None),
            "CF": (10, 11, 12, 13, 14, 8, None),
            "IF": (7, 8, 9, 10, 11, None, None),
            "DF": (8, 9, 10, 11, 12, None, None),
            "RF": (8, 9, 10, 11, 12, None, 5),
        }
        idxs = indices[parts[0]]
        wpt["alt_constraint"].append(float(parts[idxs[0]]))
        wpt["alt_top"].append(float(parts[idxs[1]]))
        wpt["alt_bottom"].append(float(parts[idxs[2]]))
        wpt["spd_constraint"].append(float(parts[idxs[3]]))
        wpt["spd_value"].append(float(parts[idxs[4]]))
        wpt["crs"].append(float(parts[idxs[5]]) if idxs[5] else np.nan)

        if parts[0] == "RF":
            center_name = parts[idxs[6]]

            fix = table_fixes.loc[table_fixes.iloc[:, 0] == center_name]
            if not fix.empty:
                wpt["center_lat"].append(fix.iloc[0, 1])
                wpt["center_lon"].append(fix.iloc[0, 2])
            else:
                wpt["center_lat"].append(np.nan)
                wpt["center_lon"].append(np.nan)
        else:
            wpt["center_lat"].append(np.nan)
            wpt["center_lon"].append(np.nan)
    elif parts[0] == "CA":
        wpt["alt_constraint"].append(float(parts[3]))
        wpt["alt_top"].append(np.nan)
        wpt["alt_bottom"].append(float(parts[4]))
        wpt["spd_constraint"].append(0)
        wpt["spd_value"].append(np.nan)
        wpt["crs"].append(float(parts[2]))
        wpt["center_lat"].append(np.nan)
        wpt["center_lon"].append(np.nan)
    else:
        wpt["alt_constraint"].append(0)
        wpt["alt_top"].append(np.nan)
        wpt["alt_bottom"].append(np.nan)
        wpt["spd_constraint"].append(0)
        wpt["spd_value"].append(np.nan)
        wpt["crs"].append(np.nan)
        wpt["center_lat"].append(np.nan)
        wpt["center_lon"].append(np.nan)


def parse_waypoints(fid, table_fixes):
    wpt = make_empty_wpts()
    # table_fixes = None

    for idx, line in enumerate(fid):
        line = line.strip()
        if not line:
            continue

        parts = line.split(",")
        wpt["line"].append(line)
        wpt["leg_type"].append(parts[0])
        wpt["name"].append(parts[1])

        if len(parts[0]) > 1 and parts[0][1] == "F":
            wpt["lat"].append(float(parts[2]))
            wpt["lon"].append(float(parts[3]))
        else:
            wpt["lat"].append(np.nan)
            wpt["lon"].append(np.nan)

        # Altitude and speed constraints handling
        if parts[0] in ["TF", "CF", "IF", "DF", "RF"]:
            indices = {
                "TF": (10, 11, 12, 13, 14, None, None),
                "CF": (10, 11, 12, 13, 14, 8, None),
                "IF": (7, 8, 9, 10, 11, None, None),
                "DF": (8, 9, 10, 11, 12, None, None),
                "RF": (8, 9, 10, 11, 12, None, 5),
            }
            idxs = indices[parts[0]]
            wpt["alt_constraint"].append(float(parts[idxs[0]]))
            wpt["alt_top"].append(float(parts[idxs[1]]))
            wpt["alt_bottom"].append(float(parts[idxs[2]]))
            wpt["spd_constraint"].append(float(parts[idxs[3]]))
            wpt["spd_value"].append(float(parts[idxs[4]]))
            wpt["crs"].append(float(parts[idxs[5]]) if idxs[5] else np.nan)

            if parts[0] == "RF":
                center_name = parts[idxs[6]]
                # if table_fixes is None:
                #     table_fixes = pd.read_csv("Waypoints.txt")
                fix = table_fixes.loc[table_fixes.iloc[:, 0] == center_name]
                if not fix.empty:
                    wpt["center_lat"].append(fix.iloc[0, 1])
                    wpt["center_lon"].append(fix.iloc[0, 2])
                else:
                    wpt["center_lat"].append(np.nan)
                    wpt["center_lon"].append(np.nan)
            else:
                wpt["center_lat"].append(np.nan)
                wpt["center_lon"].append(np.nan)
        elif parts[0] == "CA":
            wpt["alt_constraint"].append(float(parts[3]))
            wpt["alt_top"].append(np.nan)
            wpt["alt_bottom"].append(float(parts[4]))
            wpt["spd_constraint"].append(0)
            wpt["spd_value"].append(np.nan)
            wpt["crs"].append(float(parts[2]))
            wpt["center_lat"].append(np.nan)
            wpt["center_lon"].append(np.nan)
        else:
            wpt["alt_constraint"].append(0)
            wpt["alt_top"].append(np.nan)
            wpt["alt_bottom"].append(np.nan)
            wpt["spd_constraint"].append(0)
            wpt["spd_value"].append(np.nan)
            wpt["crs"].append(np.nan)
            wpt["center_lat"].append(np.nan)
            wpt["center_lon"].append(np.nan)

    return wpt


def load_sid_waypoints(airport_filename, sid, runway, table_fixes):
    # Initialize an empty structure for output
    wpt = make_empty_wpts()

    # Go through the file and found the SID of interest
    sid_found = False

    with open(airport_filename, "r") as fid:
        for line in fid:
            parts = line.strip().split(",")

            # Check for the correct waypoint:
            # action: distinguish between all and actual runway
            if (
                parts[0] == "SID"
                and parts[1] == sid
                and (parts[2] == runway or parts[2] == "ALL")
            ):
                sid_found = True
            elif sid_found and len(parts) > 4:
                parse_waypoint_line(line, wpt, table_fixes)
            elif sid_found and len(parts) < 4:
                break
    return wpt


def load_star_waypoints(airport_filename, star, runway, table_fixes):
    # Initialize an empty structure for output
    wpt = make_empty_wpts()

    # Go through the file and found the STAR of interest
    star_found = False

    with open(airport_filename, "r") as fid:
        for line in fid:
            parts = line.strip().split(",")

            # Check for the correct waypoint:
            # action: distinguish between all and actual runway
            if (
                parts[0] == "STAR"
                and parts[1] == star
                and (parts[2] == runway or parts[2] == "ALL")
            ):
                star_found = True
            elif star_found and len(parts) > 4:
                parse_waypoint_line(line, wpt, table_fixes)
            elif star_found and len(parts) < 4:
                break
    return wpt


def load_apptr_waypoints(airport_filename, star, runway, nav, table_fixes):
    nav_code = MAPPING_NAV_TO_CODE[nav]

    # Initialize an empty structure for output
    wpt = make_empty_wpts()

    # Go through the file and found the APPTR of interest
    apptr_found = False

    with open(airport_filename, "r") as fid:
        for line in fid:
            parts = line.strip().split(",")

            # Check for the correct waypoint:
            if parts[0] == "APPTR" and parts[1] == nav_code + runway:
                apptr_found = True
            elif apptr_found and len(parts) > 4:
                parse_waypoint_line(line, wpt, table_fixes)
            elif apptr_found and len(parts) < 4:
                break
    return wpt


def load_final_waypoints(airport_filename, runway, nav, table_fixes):
    nav_code = MAPPING_NAV_TO_CODE[nav]

    # Initialize an empty structure for output
    wpt = make_empty_wpts()

    # Go through the file and found the FINAL of interest
    final_found = False

    with open(airport_filename, "r") as fid:
        for line in fid:
            parts = line.strip().split(",")

            # Check for the correct waypoint:
            if (
                parts[0] == "FINAL"
                and parts[1] == nav_code + runway
                and (parts[3] == nav[0] or parts[3] == nav_code)
            ):
                final_found = True
            elif final_found and len(parts) > 5:
                parse_waypoint_line(line, wpt, table_fixes)
            elif final_found and len(parts) < 5:
                break
    return wpt
