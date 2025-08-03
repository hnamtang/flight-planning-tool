import warnings

import numpy as np
from scipy.spatial import KDTree

from ...utils import ecef2llh, llh2ecef


def select_enroute_waypoints(
    route_llh, all_wpts_llh, number_wpts_selected=5, DISTANCE_THRESHOLD=1000
):
    """
    Select waypoints for en route flight phase. This function implement K-D Tree algorithm
    to quickly look for the closest waypoints to the great circle route, which connects
    SID exit point and STAR entry point.

    Parameters
    ----------
    route_llh : list
        A list of (lat, lon) tuples representing the en route trajectory [deg].
    all_wpts_llh : pd.DataFrame
        A DataFrame contains all global waypoints coordinates.
    number_wpts_selected : int
        Number of en route waypoints
    DISTANCE_THRESHOLD : float
        Waypoints within `DISTANCE_THRESHOLD` [m] of the SID exit or STAR entry point are
        excluded from en route waypoint selection

    Returns
    -------
    wpts_selected_llh_dict : dict
        A dictionary contains ICAO code, latitude, longitude of the `number_wpts_selected`
        closest waypoints to the great circle route [deg]
    """
    # Exclude both end points
    route_llh = np.asarray(route_llh)
    sid_llh = route_llh[[0]]
    star_llh = route_llh[[-1]]
    route_llh = route_llh[1:-1]
    n_route_pnts = len(route_llh)
    if (
        number_wpts_selected > n_route_pnts
    ):  # since route_llh includes SID and STAR points
        number_wpts_selected = 3
        warnings.warn(
            f"Number of waypoints selected (route samples) between SID exit point and STAR entry point for the en route cannot exceed {len(route_llh) - 2}; using {number_wpts_selected} waypoints as fallback.",
            UserWarning,
        )

    # Sample number_wpts evely spaced points along the great circle route
    route_indices = np.linspace(0, n_route_pnts - 1, number_wpts_selected, dtype=int)
    route_samples = route_llh[route_indices, :]

    # Convert route samples from LLH to ECEF
    route_ecef = llh2ecef(route_samples)

    # Convert waypoints from LLH to ECEF
    all_wpts_ecef = llh2ecef(all_wpts_llh)
    wpts_ecef = all_wpts_ecef.loc[:, ["x", "y", "z"]].to_numpy()

    # Initialize K-D Tree
    # tree = KDTree(all_wpts_ecef)
    tree = KDTree(wpts_ecef)

    # Query the 3 closest waypoints for each point on the great circle route
    k = 5
    _, wpt_indices = tree.query(route_ecef, k=k)

    # Convert SID/STAR from LLH to ECEF for filtering
    sid_ecef = llh2ecef(sid_llh)
    star_ecef = llh2ecef(star_llh)

    # Filtering waypoints to avoid coincidence with SID and STAR waypoints (using distance)
    # and to ensure that en route waypoints lie between SID exit and STAR entry point (using vector dot product)
    selected_indices = []
    sid_to_star = star_ecef - sid_ecef
    n = 0
    for i in range(number_wpts_selected):  # loop through each route sample
        for j in range(k):
            wpt_idx = wpt_indices[i, j]
            candidate = all_wpts_ecef.iloc[wpt_idx, 1:].values
            sid_to_wpt = candidate - sid_ecef
            star_to_wpt = candidate - star_ecef

            # Ensure candidate lies between SID and STAR (dot product test)
            if sid_to_star @ sid_to_wpt.T > 0 and -sid_to_star @ star_to_wpt.T > 0:
                dist_to_sid = np.linalg.norm(sid_to_wpt)
                dist_to_star = np.linalg.norm(star_to_wpt)
                if (
                    dist_to_sid > DISTANCE_THRESHOLD
                    and dist_to_star > DISTANCE_THRESHOLD
                ):
                    n += 1
                    selected_indices.append(wpt_idx)
                    break

    _, unique_idx = np.unique(selected_indices, return_index=True)
    ordered_unique = np.array(selected_indices)[np.sort(unique_idx)]

    # If fewer than number_wpts_selected, fill by increasing k in query or reducing spacing
    if len(ordered_unique) < number_wpts_selected:
        raise ValueError(
            f"Not enough unique nearby waypoints found. Found {len(ordered_unique)}"
        )

    wpts_selected_llh = all_wpts_llh.iloc[ordered_unique, :]

    wpts_selected_llh_dict = {
        "name": wpts_selected_llh["name"].values.tolist(),
        "lat": wpts_selected_llh["lat"].values.tolist(),
        "lon": wpts_selected_llh["lon"].values.tolist(),
    }

    return wpts_selected_llh_dict
