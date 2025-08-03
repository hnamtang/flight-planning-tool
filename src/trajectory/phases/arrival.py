from ...utils import load_leg_data
from ..legs import LEG_GENERATORS
from ..routing import create_flyby


class ArrivalGenerator:
    def __init__(
        self,
        dest_rwy,
        dest_rwy_coords,
        wpts_star,
        # TODO: add final approach, missed approach
        # wpts_apptr,
        # wpts_final,
        # nav_code,
        turn_radius,
        enroute_exit,
        num_interp_pnts,
    ):
        self.dest_rwy = dest_rwy
        self.dest_rwy_coords = dest_rwy_coords
        self.wpts_star = wpts_star
        # TODO: add final approach, missed approach
        # self.wpts_apptr = wpts_apptr
        # self.wpts_final = wpts_final
        # self.nav_code = nav_code
        self.turn_radius = turn_radius
        self.enroute_exit = enroute_exit
        self.num_interp_pnts = num_interp_pnts

    def generate(
        self,
        # TODO: add final approach, missed approach
        # generate_missed_appr=False,
        return_distance=False,
    ):
        if return_distance:
            # STAR
            star_trajectory, star_distance = self._generate_star(return_distance=True)

            # TODO: add final approach, missed approach
            # # APPTR
            # star_exit = (star_trajectory[-1][0], star_trajectory[-1][1])
            # apptr_trajectory, apptr_distance = self._generate_apptr(
            #     star_exit, return_distance=True
            # )

            # # FINAL
            # apptr_exit = (apptr_trajectory[-1][0], apptr_trajectory[-1][1])
            # final_trajectory, final_distance = self._generate_final(
            #     apptr_exit,
            #     self.dest_rwy,
            #     generate_missed_appr=generate_missed_appr,
            #     return_distance=True,
            # )

            # trajectory = star_trajectory + apptr_trajectory + final_trajectory
            # travel_distance = star_distance + apptr_distance + final_distance

            trajectory = star_trajectory
            travel_distance = star_distance

            return trajectory, travel_distance

        else:
            # STAR
            star_trajectory = self._generate_star(return_distance=False)

            # TODO: add final approach, missed approach
            # # APPTR
            # star_exit = (star_trajectory[-1][0], star_trajectory[-1][1])
            # apptr_trajectory = self._generate_apptr(star_exit, return_distance=False)

            # # FINAL
            # apptr_exit = (apptr_trajectory[-1][0], apptr_trajectory[-1][1])
            # final_trajectory = self._generate_final(
            #     apptr_exit,
            #     generate_missed_appr=generate_missed_appr,
            #     return_distance=False,
            # )

            # trajectory = star_trajectory + apptr_trajectory + final_trajectory

            trajectory = star_trajectory

            return trajectory

    def _generate_star(self, return_distance):
        star_trajectory = []
        if return_distance:
            star_distance = 0

        # Generate legs from SID exit point to STAR entry point
        # Initialize variables
        number_wpts = len(self.wpts_star["lat"])
        prev_coords = self.enroute_exit
        for wpt_idx in range(number_wpts):
            leg_type_current = self.wpts_star["leg_type"][wpt_idx]

            if wpt_idx != number_wpts - 1:
                leg_type_next = self.wpts_star["leg_type"][wpt_idx + 1]
            else:
                # TODO: add final approach, missed approach
                # leg_type_next = self.wpts_apptr["leg_type"][0]
                leg_type_next = "CF"

            lat_prev, lon_prev = prev_coords
            lat_wpt = self.wpts_star["lat"][wpt_idx]
            lon_wpt = self.wpts_star["lon"][wpt_idx]

            # Determine is_flyby_current
            if leg_type_current in ["CF", "DF", "IF", "TF"] and leg_type_next != "RF":
                """
                ARINC424: "The previous leg and next leg associated with an RF leg should 
                have a course or track which is tangent to the RF leg. Skip fly-by."
                """
                if wpt_idx != number_wpts - 1:
                    lat_next = self.wpts_star["lat"][wpt_idx + 1]
                    lon_next = self.wpts_star["lon"][wpt_idx + 1]
                else:
                    # TODO: add final approach, missed approach
                    # lat_next = self.wpts_apptr["lat"][0]
                    # lon_next = self.wpts_apptr["lon"][0]
                    lat_next = self.dest_rwy_coords[0]
                    lon_next = self.dest_rwy_coords[1]

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
                kwargs_dict["crs"] = self.wpts_star["crs"][wpt_idx]
            elif leg_type_current == "RF":
                kwargs_dict.update(
                    center_lat=self.wpts_star["center_lat"][wpt_idx],
                    center_lon=self.wpts_star["center_lon"][wpt_idx],
                )

            leg_data = load_leg_data(
                lat_prev,
                lon_prev,
                lat_wpt,
                lon_wpt,
                leg_type_current,
                "star",
                self.turn_radius,
                **kwargs_dict,
            )

            # Generate leg trajectory
            generator = LEG_GENERATORS[leg_data["leg_type"]](
                leg_data, self.num_interp_pnts
            )
            if return_distance:
                leg_trajectory, leg_distance = generator.generate(return_distance=True)
                star_distance += leg_distance
            else:
                leg_trajectory = generator.generate(return_distance=False)

            star_trajectory.extend(leg_trajectory)

            # Re-assign prev_coords for the next iteration
            prev_coords = leg_trajectory[-1]

        if return_distance:
            return star_trajectory, star_distance
        else:
            return star_trajectory

    def _generate_apptr(self, star_exit, return_distance):
        apptr_trajectory = []
        if return_distance:
            apptr_distance = 0

        # Generate legs from STAR exit point to APPTR entry point
        # Initialize variables
        number_wpts = len(self.wpts_apptr["lat"])
        prev_coords = star_exit
        for wpt_idx in range(number_wpts):
            leg_type_current = self.wpts_apptr["leg_type"][wpt_idx]

            if wpt_idx != number_wpts - 1:
                leg_type_next = self.wpts_apptr["leg_type"][wpt_idx + 1]
            else:
                leg_type_next = self.wpts_final["leg_type"][0]

            lat_prev, lon_prev = prev_coords
            lat_wpt = self.wpts_apptr["lat"][wpt_idx]
            lon_wpt = self.wpts_apptr["lon"][wpt_idx]

            # Determine is_flyby_current
            if leg_type_current in ["CF", "DF", "IF", "TF"] and leg_type_next != "RF":
                """
                ARINC424: "The previous leg and next leg associated with an RF leg should 
                have a course or track which is tangent to the RF leg. Skip fly-by."
                """
                if wpt_idx != number_wpts - 1:
                    lat_next = self.wpts_apptr["lat"][wpt_idx + 1]
                    lon_next = self.wpts_apptr["lon"][wpt_idx + 1]
                else:
                    lat_next = self.wpts_final["lat"][0]
                    lon_next = self.wpts_final["lon"][0]

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
                kwargs_dict["crs"] = self.wpts_apptr["crs"][wpt_idx]
            elif leg_type_current == "RF":
                kwargs_dict.update(
                    center_lat=self.wpts_apptr["center_lat"][wpt_idx],
                    center_lon=self.wpts_apptr["center_lon"][wpt_idx],
                )

            leg_data = load_leg_data(
                lat_prev,
                lon_prev,
                lat_wpt,
                lon_wpt,
                leg_type_current,
                "star",
                self.turn_radius,
                **kwargs_dict,
            )

            # Generate leg trajectory
            generator = LEG_GENERATORS[leg_data["leg_type"]](
                leg_data, self.num_interp_pnts
            )
            if return_distance:
                leg_trajectory, leg_distance = generator.generate(return_distance=True)
                apptr_distance += leg_distance
            else:
                leg_trajectory = generator.generate(return_distance=False)

            apptr_trajectory.extend(leg_trajectory)

            # Re-assign prev_coords for the next iteration
            prev_coords = leg_trajectory[-1]

        if return_distance:
            return apptr_trajectory, apptr_distance
        else:
            return apptr_trajectory

    def _generate_final(
        self, apptr_exit, dest_rwy, generate_missed_appr, return_distance
    ):
        final_appr_trajectory = []
        if return_distance:
            final_appr_distance = 0

        # Extract waypoints for final approach and missed approach
        wpts_final_appr, wpts_missed_appr = ArrivalGenerator.extract_missed_appr_wpts(
            self.wpts_final
        )

        # Generate legs from APPTR exit point to end of final approach
        number_wpts = len(wpts_final_appr["lat"])
        prev_coords = apptr_exit
        for wpt_idx in range(number_wpts):
            leg_type_current = wpts_final_appr["leg_type"][wpt_idx]

            if wpt_idx != number_wpts - 1:
                leg_type_next = wpts_final_appr["leg_type"][wpt_idx + 1]
            else:
                leg_type_next = wpts_missed_appr["leg_type"][0]

            lat_prev, lon_prev = prev_coords
            lat_wpt = wpts_final_appr["lat"][wpt_idx]
            lon_wpt = wpts_final_appr["lon"][wpt_idx]

            # Determine is_flyby_current
            if leg_type_current in ["CF", "DF", "IF", "TF"] and leg_type_next != "RF":
                """
                ARINC424: "The previous leg and next leg associated with an RF leg should 
                have a course or track which is tangent to the RF leg. Skip fly-by."
                """
                if wpt_idx != number_wpts - 1:
                    lat_next = wpts_final_appr["lat"][wpt_idx + 1]
                    lon_next = wpts_final_appr["lon"][wpt_idx + 1]
                else:
                    lat_next, lon_next = self.dest_rwy_coords

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
                kwargs_dict["crs"] = wpts_final_appr["crs"][wpt_idx]
            elif leg_type_current == "RF":
                kwargs_dict.update(
                    center_lat=wpts_final_appr["center_lat"][wpt_idx],
                    center_lon=wpts_final_appr["center_lon"][wpt_idx],
                )

            leg_data = load_leg_data(
                lat_prev,
                lon_prev,
                lat_wpt,
                lon_wpt,
                leg_type_current,
                "star",
                self.turn_radius,
                **kwargs_dict,
            )

            # Generate leg trajectory
            generator = LEG_GENERATORS[leg_data["leg_type"]](
                leg_data, self.num_interp_pnts
            )
            if return_distance:
                leg_trajectory, leg_distance = generator.generate(return_distance=True)
                final_appr_distance += leg_distance
            else:
                leg_trajectory = generator.generate(return_distance=False)

            final_appr_trajectory.extend(leg_trajectory)

            # Re-assign prev_coords for the next iteration
            prev_coords = leg_trajectory[-1]

        # Generate legs from Final approach exit point to end of missed approach
        if generate_missed_appr:
            missed_appr_trajectory = []
            if return_distance:
                missed_appr_distance = 0

            number_wpts = len(wpts_missed_appr["lat"])
            prev_coords = apptr_exit
            for wpt_idx in range(number_wpts):
                leg_type_current = wpts_missed_appr["leg_type"][wpt_idx]

                if wpt_idx != number_wpts - 1:
                    leg_type_next = wpts_missed_appr["leg_type"][wpt_idx + 1]
                else:
                    leg_type_next = "TF"

                lat_prev, lon_prev = prev_coords
                lat_wpt = wpts_missed_appr["lat"][wpt_idx]
                lon_wpt = wpts_missed_appr["lon"][wpt_idx]

                # Determine is_flyby_current
                if (
                    leg_type_current in ["CF", "DF", "IF", "TF"]
                    and leg_type_next != "RF"
                    and wpt_idx != number_wpts - 1
                ):
                    """
                    ARINC424: "The previous leg and next leg associated with an RF leg should 
                    have a course or track which is tangent to the RF leg. Skip fly-by."
                    """
                    lat_next = wpts_missed_appr["lat"][wpt_idx + 1]
                    lon_next = wpts_missed_appr["lon"][wpt_idx + 1]

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
                    kwargs_dict["crs"] = wpts_missed_appr["crs"][wpt_idx]
                elif leg_type_current == "RF":
                    kwargs_dict.update(
                        center_lat=wpts_missed_appr["center_lat"][wpt_idx],
                        center_lon=wpts_missed_appr["center_lon"][wpt_idx],
                    )

                leg_data = load_leg_data(
                    lat_prev,
                    lon_prev,
                    lat_wpt,
                    lon_wpt,
                    leg_type_current,
                    "star",
                    self.turn_radius,
                    **kwargs_dict,
                )

                # Generate leg trajectory
                generator = LEG_GENERATORS[leg_data["leg_type"]](
                    leg_data, self.num_interp_pnts
                )
                if return_distance:
                    leg_trajectory, leg_distance = generator.generate(
                        return_distance=True
                    )
                    missed_appr_distance += leg_distance
                else:
                    leg_trajectory = generator.generate(return_distance=False)

                missed_appr_trajectory.extend(leg_trajectory)

                # Re-assign prev_coords for the next iteration
                prev_coords = leg_trajectory[-1]

        final_trajectory = final_appr_trajectory + missed_appr_trajectory

        if return_distance:
            final_distance = final_appr_distance + missed_appr_distance
            return final_trajectory, final_distance
        else:
            return final_trajectory

    @staticmethod
    def extract_missed_appr_wpts(wpts_final):
        """
        Extract final approach and missed approach waypoints from final waypoints
        """
        final_appr_end = ("CF", "TF", "RF")
        missed_appr_initial = ("CA", "CF", "DF", "FA", "HA", "HM", "RF", "VI", "VM")

        wpts_final_appr = {}
        wpts_missed_appr = {}
        idx_ma_start = None
        for wpt_idx in range(len(wpts_final["lat"]) - 1):
            leg_type_current = wpts_final["leg_type"][wpt_idx]
            leg_type_next = wpts_final["leg_type"][wpt_idx + 1]

            if (
                leg_type_current in final_appr_end
                and leg_type_next in missed_appr_initial
            ):
                alt_top_current = wpts_final["alt_top"][wpt_idx]
                alt_top_next = wpts_final["alt_top"][wpt_idx + 1]
                alt_bottom_next = wpts_final["alt_bottom"][wpt_idx + 1]

                if alt_top_current > alt_top_next or alt_top_current > alt_bottom_next:
                    idx_ma_start = wpt_idx + 1
                    break

        for key, val in wpts_final.items():
            wpts_final_appr[key] = val[:idx_ma_start]
            wpts_missed_appr[key] = val[idx_ma_start:]

        return wpts_final_appr, wpts_missed_appr
