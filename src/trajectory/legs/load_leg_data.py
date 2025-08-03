import warnings


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
    # TODO: check if leg_category is needed. Delete it if not
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
