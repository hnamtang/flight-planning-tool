from ..routing import create_arc


class RFLegGenerator:
    def __init__(self, leg_data, num_interp_pnts):
        """
        Generate Radius to Fix leg.

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
                    True if the current waypoint is a fly-by waypoint. Here, False
                * `turn_radius` : float
                    Turn radius calculated from current altitude, TAS and bank angle [m]
                * `flyby_center_lat`, `flyby_center_lon` : float
                    Latitude and longitude of the center arc [deg]
                * `flyby_start_lat`, `flyby_start_lon` : float
                    Latitude and longitude of the arc start [deg]
                * `flyby_end_lat`, `flyby_end_lon` : float
                    Latitude and longitude of the arc end [deg]
                * `center_lat`, `center_lon` : float
                    Latitude and longitude of the leg center [deg]
                * `leg_type` : str
                    Type of the current leg. Here, 'RF'

        num_interp_pnts : int
            Number of interpolated points.
        """
        self.leg_data = leg_data
        self.num_interp_pnts = num_interp_pnts

    def generate(self, return_distance=False):
        """
        Generate Radius to Fix leg.

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
        lat_from, lat_to = self.leg_data["lat"][:2]
        lon_from, lon_to = self.leg_data["lon"][:2]
        center_lat = self.leg_data["center_lat"]
        center_lon = self.leg_data["center_lon"]

        if return_distance:
            trajectory, travel_distance = create_arc(
                lat_from,
                lon_from,
                lat_to,
                lon_to,
                center_lat,
                center_lon,
                self.num_interp_pnts,
                return_distance=True,
                exclude_start=True,
            )
        else:
            trajectory = create_arc(
                lat_from,
                lon_from,
                lat_to,
                lon_to,
                center_lat,
                center_lon,
                self.num_interp_pnts,
                return_distance=False,
                exclude_start=True,
            )

        if return_distance:
            return trajectory, travel_distance
        else:
            return trajectory
