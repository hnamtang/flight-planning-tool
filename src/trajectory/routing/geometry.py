import numpy as np
from geographiclib.geodesic import Geodesic

from ...utils import (
    R_EARTH_EQUATORIAL,
    RadiusError,
    SinVertexAngleZeroError,
    wgs84_tangent_fixed_radius_flyby_arc,
    wrap_to_90,
    wrap_to_180,
)

np.seterr(divide="raise")
_geod = Geodesic.WGS84


def create_straight(
    lat1, lon1, lat2, lon2, num_points, return_distance=False, exclude_start=False
):
    """
    Create straight route between 2 points. Straight route between 2 points is the
    shortest route and is referred to as the great circle route.

    Parameters
    ----------
    lat1 : float
        Latitude of the first point [deg]
    lon1 : float
        Longitude of the first point [deg]
    lat2 : float
        Latitude of the second point [deg]
    lon2 : float
        Longitude of the second point [deg]
    num_points : int
        Number of interpolated points
    return_distance : bool
        If True, the great circle distance is returned. Default is False
    exclude_start : bool
        If True, start point is excluded from the trajectory. Used for generating
        consecutive legs.

    Returns
    -------
    trajectory : list
        List of (lat, lon) tuples representing the trajectory, including coordinates of
        the start and end points [deg]
    total_distance : float
        Great circle distance between 2 points [m]
    """
    if exclude_start:
        trajectory = []
    else:
        trajectory = [(lat1, lon1)]

    geod_inverse_line = _geod.InverseLine(lat1, lon1, lat2, lon2)
    total_distance = geod_inverse_line.s13

    # Compute points along the arc
    for i in range(1, num_points + 1):
        distance = i * total_distance / (num_points + 1)
        result = geod_inverse_line.Position(distance)
        trajectory.append((result["lat2"], result["lon2"]))

    trajectory.append((lat2, lon2))

    if return_distance:
        return trajectory, total_distance
    else:
        return trajectory


def create_arc(
    lat1,
    lon1,
    lat2,
    lon2,
    center_lat,
    center_lon,
    num_points,
    return_distance=False,
    exclude_start=False,
):
    """
    Create arc route from point 1 to point 2. The arc connecting 2 points has a constant distance
    (radius) to the center point.

    Parameters
    ----------
    lat1 : float
        Latitude of the  point 1 [deg]
    lon1 : float
        Longitude of the point 1 [deg]
    lat2 : float
        Latitude of the  point 2 [deg]
    lon2 : float
        Longitude of the point 2 [deg]
    center_lat : float
        Latitude of the center point [deg]
    center_lon : float
        Longitude of the center point [deg]
    num_points : int
        Number of interpolated points
    return_distance : bool
        If True, arc distance is returned. Default is False
    exclude_start : bool
        If True, start point is excluded from the trajectory. Used for generating
        consecutive legs.

    Returns
    -------
    trajectory : list
        List of (lat, lon) tuples representing the trajectory [deg]
    total_distance : float
        Arc distance between 2 points [m]
    """
    if exclude_start:
        trajectory = []
    else:
        trajectory = [(lat1, lon1)]

    geod_inverse_center_to_1 = _geod.Inverse(center_lat, center_lon, lat1, lon1)
    geod_inverse_center_to_2 = _geod.Inverse(center_lat, center_lon, lat2, lon2)

    # Radius is the distance from arc center to point 1 or point 2 [m]
    radius = geod_inverse_center_to_1["s12"]

    # Extract courses from arc center to point 1 and point 2
    crs_center_to_1_at_center = geod_inverse_center_to_1["azi1"]
    crs_center_to_2_at_center = geod_inverse_center_to_2["azi1"]

    d_angle_center = wrap_to_180(crs_center_to_2_at_center - crs_center_to_1_at_center)

    # Compute points along the arc
    if return_distance:
        total_distance = 0
        coord_prev = (lat1, lon1)
    for i in range(1, num_points + 1):
        angle_increment = i * d_angle_center / (num_points + 1)
        angle = crs_center_to_1_at_center + angle_increment

        geod_direct_center_to_point = _geod.Direct(
            center_lat, center_lon, angle, radius
        )
        trajectory.append(
            (geod_direct_center_to_point["lat2"], geod_direct_center_to_point["lon2"])
        )
        if return_distance:
            total_distance += _geod.Inverse(*coord_prev, *trajectory[-1])["s12"]
            coord_prev = trajectory[-1]

    trajectory.append((lat2, lon2))

    if return_distance:
        return trajectory, total_distance
    else:
        return trajectory


def create_rhumb_line(
    lat1, lon1, lat2, lon2, num_points, return_distance=False, exclude_start=False
):
    """
    Create rhumb line route from point 1 to point 2. Rhumb line route is defined as a route
    with constant course.

    Parameters
    ----------
    lat1 : float
        Latitude of the point 1 [deg]
    lon1 : float
        Longitude of the point 1 [deg]
    lat2 : float
        Latitude of the point 2 [deg]
    lon2 : float
        Longitude of the point 2 [deg]
    num_points : int
        Number of interpolated points
    return_distance : bool
        If True, the rhumb line distance is returned. Default is False
    exclude_start : bool
        If True, start point is excluded from the trajectory. Used for generating
        consecutive legs.

    Returns
    -------
    trajectory : list
        List of (lat, lon) tuples representing the trajectory, including coordinates of
        the start and end points [deg]
    total_distace : float
        Rhumb line distance between 2 points [m]

    References:
        Rhumb Line Navigation - https://edwilliams.org/avform147.htm#Rhumb
    """

    def compute_rhumb_line_course_distance(lat1, lon1, lat2, lon2):
        # Compute rhumb line distance and course from point to point
        delta_lat = lat2 - lat1
        delta_lat = np.deg2rad(wrap_to_90(np.rad2deg(delta_lat)))
        delta_lon = lon2 - lon1
        delta_lon = np.deg2rad(wrap_to_180(np.rad2deg(delta_lon)))

        dphi = np.log(np.tan(lat2 / 2 + np.pi / 4) / np.tan(lat1 / 2 + np.pi / 4))

        if abs(delta_lat) < np.sqrt(TOL):
            q = np.cos(lat1)
        else:
            q = delta_lat / dphi

        # Rhumb line true course [rad]
        rhumb_line_course = np.atan2(delta_lon, dphi) % (2 * np.pi)

        # Total rhumb line distance [m]
        rhumb_line_distance = R_EARTH_EQUATORIAL * np.sqrt(
            (q * delta_lon) ** 2 + delta_lat**2
        )

        return rhumb_line_course, rhumb_line_distance

    # Initialize trajectory
    if exclude_start:
        trajectory = []
    else:
        trajectory = [(lat1, lon1)]

    # Define tolerance
    TOL = 1e-12

    # Convert coordinates to rad
    lat1_rad = np.deg2rad(lat1)
    lon1_rad = np.deg2rad(lon1)
    lat2_rad = np.deg2rad(lat2)
    lon2_rad = np.deg2rad(lon2)

    # Total rhumb line distance [m]
    true_course, total_distance = compute_rhumb_line_course_distance(
        lat1_rad, lon1_rad, lat2_rad, lon2_rad
    )

    # Compute rhumb line distance and course for num_points points
    step_distance = total_distance / (num_points + 1)
    step_distances = np.linspace(
        step_distance, num_points * total_distance / (num_points + 1), num_points
    )
    d_lats_rad = step_distances * np.cos(true_course) / R_EARTH_EQUATORIAL
    lats_rad = lat1_rad + d_lats_rad
    lats_rad = np.deg2rad(wrap_to_90(np.rad2deg(lats_rad)))  # wrap latitudes
    lats_deg = np.rad2deg(lats_rad)

    dphis = np.log(np.tan(lats_rad / 2 + np.pi / 4) / np.tan(lat1_rad / 2 + np.pi / 4))

    qs = np.empty_like(step_distances)
    qs[np.abs(d_lats_rad) < np.sqrt(TOL)] = np.cos(lat1_rad)
    idx = np.abs(d_lats_rad) >= np.sqrt(TOL)
    qs[idx] = d_lats_rad[idx] / dphis[idx]

    d_lons_rad = step_distances * np.sin(true_course) / (R_EARTH_EQUATORIAL * qs)
    lons_rad = lon1_rad + d_lons_rad
    lons_deg = wrap_to_180(np.rad2deg(lons_rad))  # wrap longitudes

    # trajectory.extend(zip(lats_deg.tolist(), lons_deg.tolist()))
    trajectory = [(lat, lon) for lat, lon in zip(lats_deg, lons_deg)]

    trajectory.append((lat2, lon2))

    if return_distance:
        return trajectory, total_distance
    else:
        return trajectory


def create_flyby(lat_prev, lon_prev, lat_wpt, lon_wpt, lat_next, lon_next, turn_radius):
    try:
        (
            flyby_center_lat,
            flyby_center_lon,
            flyby_start_lat,
            flyby_start_lon,
            flyby_end_lat,
            flyby_end_lon,
            _,
        ) = wgs84_tangent_fixed_radius_flyby_arc(
            lat_prev, lon_prev, lat_wpt, lon_wpt, lat_next, lon_next, turn_radius
        )
        is_flyby = True
    except (
        RadiusError,
        SinVertexAngleZeroError,
        FloatingPointError,
        ZeroDivisionError,
    ):
        flyby_center_lat = None
        flyby_center_lon = None
        flyby_start_lat = None
        flyby_start_lon = None
        flyby_end_lat = None
        flyby_end_lon = None
        is_flyby = False

    return (
        flyby_center_lat,
        flyby_center_lon,
        flyby_start_lat,
        flyby_start_lon,
        flyby_end_lat,
        flyby_end_lon,
        is_flyby,
    )
