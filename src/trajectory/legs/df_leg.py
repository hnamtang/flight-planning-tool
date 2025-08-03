from ..routing import create_arc, create_straight


class DFLegGenerator:
    def __init__(self, leg_data, num_interp_pnts):
        """
        Generate Direct to Fix leg using great circle path.

        Parameters
        ----------
        leg_data : dict
            A dictionary contains navigation information. The dictionary contains
            the following keys:

                * `lat` : list
                    A list contains 3 latitudes of 3 consecutive waypoints [deg]
                * `lon` : list
                    A list contains 3 longitudes of 3 consecutive waypoints [deg]
                * `is_flyby` : bool
                    True if the current waypoint is a fly-by waypoint
                * `flyby_center_lat`, `flyby_center_lon` : float
                    Latitude and longitude of the center arc [deg]
                * `flyby_start_lat`, `flyby_start_lon` : float
                    Latitude and longitude of the arc start [deg]
                * `flyby_end_lat`, `flyby_end_lon` : float
                    Latitude and longitude of the arc end [deg]
                * `leg_type` : str
                    Type of the current leg

        num_interp_pnts : int
            Number of interpolated points.
        """
        self.leg_data = leg_data
        self.num_interp_pnts = num_interp_pnts

    def generate(self, return_distance=False):
        """
        Generate Direct to Fix leg using great circle path.

        Parameters
        ----------
        return_distance : bool
            If True, the travel distance is returned in addition to trajectory [m]

        Returns
        -------
        trajectory : list
            List of (lat, lon) tuples representing the trajectory [deg]
        travel_distance : float
            Travel distance [m]
        """
        trajectory = []
        if return_distance:
            travel_distance = 0

        # Straight part (DF)
        lat_from = self.leg_data["lat"][0]
        lon_from = self.leg_data["lon"][0]

        if not self.leg_data["is_flyby"]:
            num_pnts_straight = self.num_interp_pnts

            lat_to = self.leg_data["lat"][1]
            lon_to = self.leg_data["lon"][1]
        else:
            num_pnts_straight = self.num_interp_pnts * 80 // 100
            num_pnts_arc = self.num_interp_pnts - num_pnts_straight

            lat_to = self.leg_data["flyby_start_lat"]
            lon_to = self.leg_data["flyby_start_lon"]

        if return_distance:
            straight_part, distance_straight = create_straight(
                lat_from,
                lon_from,
                lat_to,
                lon_to,
                num_pnts_straight,
                return_distance=True,
                exclude_start=True,
            )
            travel_distance += distance_straight
        else:
            straight_part = create_straight(
                lat_from,
                lon_from,
                lat_to,
                lon_to,
                num_pnts_straight,
                return_distance=False,
                exclude_start=True,
            )
        trajectory.extend(straight_part)

        # Arc part if fly-by
        if self.leg_data["is_flyby"]:
            lat_from, lon_from = straight_part[-1]
            lat_to = self.leg_data["flyby_end_lat"]
            lon_to = self.leg_data["flyby_end_lon"]
            center_lat = self.leg_data["flyby_center_lat"]
            center_lon = self.leg_data["flyby_center_lon"]

            if return_distance:
                arc_part, distance_arc = create_arc(
                    lat_from,
                    lon_from,
                    lat_to,
                    lon_to,
                    center_lat,
                    center_lon,
                    num_pnts_arc,
                    return_distance=True,
                    exclude_start=True,
                )
                travel_distance += distance_arc
            else:
                arc_part = create_arc(
                    lat_from,
                    lon_from,
                    lat_to,
                    lon_to,
                    center_lat,
                    center_lon,
                    num_pnts_arc,
                    return_distance=False,
                    exclude_start=True,
                )
            trajectory.extend(arc_part)

        if return_distance:
            return trajectory, travel_distance
        else:
            return trajectory
