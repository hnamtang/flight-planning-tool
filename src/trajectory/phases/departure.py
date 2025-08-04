from ...utils import load_leg_data
from ..legs import LEG_GENERATORS
from ..routing import create_flyby


class DepartureGenerator:
    def __init__(
        self, org_rwy_coords, wpts_dep, turn_radius, enroute_entry, num_interp_pnts
    ):
        """
        Generate lateral trajectory for the departure phase.

        Parameters
        ----------
        org_rwy_coords : list
            Latitude and longitude [deg] of the origin runway

        wpts_dep : dict
            A dictionary contains data of the SID waypoints. The relevant keys for
            this class are:

                * `lat` : list
                    A list contains latitudes of all corresponding waypoints [deg]
                * `lon` : list
                    A list contains longitudes of all corresponding waypoints [deg]
                * `leg_type` : str
                    Type of the leg associated with the waypoint
                * `center_lat` : float
                    Latitude of the center arc for RF leg [deg]
                * `center_lon` : float
                    Longitude of the center arc for RF leg [deg]

        turn_radius : float
            Turn radius of the aircraft given current altitude, TAS and bank angle

        enroute_entry : list
            Latitude and longitude [deg] of the en route entry waypoint in form (lat, lon)

        num_interp_pnts : int
            Number of interpolated points
        """
        self.org_rwy_coords = org_rwy_coords
        self.wpts_dep = wpts_dep
        self.turn_radius = turn_radius
        self.enroute_entry = enroute_entry
        self.num_interp_pnts = num_interp_pnts

    def generate(self, return_distance=False):
        trajectory = []
        if return_distance:
            travel_distance = 0

        # Generate legs from SID to SID exit point
        # Initialize variables
        number_wpts = len(self.wpts_dep["lat"])
        prev_coords = self.org_rwy_coords
        for wpt_idx in range(number_wpts):
            leg_type_current = self.wpts_dep["leg_type"][wpt_idx]

            if wpt_idx != number_wpts - 1:
                leg_type_next = self.wpts_dep["leg_type"][wpt_idx + 1]
            else:
                leg_type_next = "TF"  # all enroute legs considered as TF leg

            lat_prev, lon_prev = prev_coords
            lat_wpt = self.wpts_dep["lat"][wpt_idx]
            lon_wpt = self.wpts_dep["lon"][wpt_idx]

            # Determine is_flyby_current
            if leg_type_current in ["CF", "DF", "IF", "TF"] and leg_type_next != "RF":
                """
                ARINC424: "The previous leg and next leg associated with an RF leg should 
                have a course or track which is tangent to the RF leg. Skip fly-by."
                """
                if wpt_idx != number_wpts - 1:
                    lat_next = self.wpts_dep["lat"][wpt_idx + 1]
                    lon_next = self.wpts_dep["lon"][wpt_idx + 1]
                else:
                    lat_next = self.enroute_entry[0]
                    lon_next = self.enroute_entry[1]

                (
                    flyby_center_lat,
                    flyby_center_lon,
                    flyby_start_lat,
                    flyby_start_lon,
                    flyby_end_lat,
                    flyby_end_lon,
                    is_flyby_current,
                ) = create_flyby(
                    lat_prev,
                    lon_prev,
                    lat_wpt,
                    lon_wpt,
                    lat_next,
                    lon_next,
                    self.turn_radius,
                )
                if is_flyby_current:
                    lat_wpt = flyby_start_lat
                    lon_wpt = flyby_start_lon
            else:
                flyby_center_lat = None
                flyby_center_lon = None
                flyby_start_lat = None
                flyby_start_lon = None
                flyby_end_lat = None
                flyby_end_lon = None
                is_flyby_current = False

            kwargs_dict = {
                "is_flyby": is_flyby_current,
                "flyby_center_lat": flyby_center_lat,
                "flyby_center_lon": flyby_center_lon,
                "flyby_start_lat": flyby_start_lat,
                "flyby_start_lon": flyby_start_lon,
                "flyby_end_lat": flyby_end_lat,
                "flyby_end_lon": flyby_end_lon,
            }
            if leg_type_current == "CF":
                kwargs_dict["crs"] = self.wpts_dep["crs"][wpt_idx]
            elif leg_type_current == "RF":
                kwargs_dict.update(
                    center_lat=self.wpts_dep["center_lat"][wpt_idx],
                    center_lon=self.wpts_dep["center_lon"][wpt_idx],
                )

            leg_data = load_leg_data(
                lat_prev,
                lon_prev,
                lat_wpt,
                lon_wpt,
                leg_type_current,
                "sid",
                self.turn_radius,
                **kwargs_dict,
            )

            # Generate leg trajectory
            generator = LEG_GENERATORS[leg_data["leg_type"]](
                leg_data, self.num_interp_pnts
            )
            if return_distance:
                leg_trajectory, leg_distance = generator.generate(return_distance=True)
                travel_distance += leg_distance
            else:
                leg_trajectory = generator.generate(return_distance=False)

            # Save to departure trajectory
            trajectory.extend(leg_trajectory)

            # Re-assign prev_coords for the next iteration
            prev_coords = leg_trajectory[-1]

        if return_distance:
            return trajectory, travel_distance
        else:
            return trajectory
