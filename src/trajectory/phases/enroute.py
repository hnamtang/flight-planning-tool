from ...utils import load_leg_data
from ..legs import LEG_GENERATORS
from ..routing import create_flyby


class EnrouteGenerator:
    def __init__(self, wpts_enroute, turn_radius, sid_exit, wpts_arr, num_interp_pnts):
        self.wpts_enroute = wpts_enroute
        self.turn_radius = turn_radius
        self.sid_exit = sid_exit
        self.wpts_arr = wpts_arr
        self.num_interp_pnts = num_interp_pnts

    def generate(self, return_distance=False):
        trajectory = []
        if return_distance:
            travel_distance = 0

        # Generate legs from SID exit point to STAR entry point
        # Initialize variables
        number_wpts = len(self.wpts_enroute["lat"])
        # prev_coords = (self.wpts_dep["lat"][-1], self.wpts_dep["lon"][-1])
        prev_coords = self.sid_exit
        leg_type = "TF"  # all enroute legs considered as TF leg
        for wpt_idx in range(number_wpts):
            if wpt_idx != number_wpts - 1:
                leg_type_next = leg_type
            else:
                leg_type_next = self.wpts_arr["leg_type"][0]

            lat_prev, lon_prev = prev_coords
            lat_wpt = self.wpts_enroute["lat"][wpt_idx]
            lon_wpt = self.wpts_enroute["lon"][wpt_idx]

            # Determine is_flyby_current
            if leg_type_next != "RF":
                """
                ARINC424: "The previous leg and next leg associated with an RF leg should 
                have a course or track which is tangent to the RF leg. Skip fly-by."
                """
                if wpt_idx != number_wpts - 1:
                    lat_next = self.wpts_enroute["lat"][wpt_idx + 1]
                    lon_next = self.wpts_enroute["lon"][wpt_idx + 1]
                else:
                    lat_next = self.wpts_arr["lat"][0]
                    lon_next = self.wpts_arr["lon"][0]

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

            leg_data = load_leg_data(
                lat_prev,
                lon_prev,
                lat_wpt,
                lon_wpt,
                leg_type,
                "enroute",
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
