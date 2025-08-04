import numpy as np
from pandas import read_csv

from ..utils import (
    DATA_DIR,
    FT2M,
    G_CONST,
    KTS2MPS,
    MAPPING_NAV_TO_CODE,
    NM2M,
    atmos,
    cas_to_tas,
    # TODO: add final approach, missed approach
    # load_apptr_waypoints,
    # load_final_waypoints,
    load_rwy_coords,
    load_sid_waypoints,
    load_star_waypoints,
    load_wpt_coords,
)
from .phases import ArrivalGenerator, DepartureGenerator, EnrouteGenerator
from .routing import create_straight, select_enroute_waypoints


class LateralTrajectoryGenerator:
    def __init__(
        self,
        org_airport,
        org_rwy,
        sid,
        dest_airport,
        dest_rwy,
        star,
        # TODO: add final approach, missed approach
        # appr_type,
        num_interp_pnts=100,
    ):
        """
        Define bank dynamics. Assumptions:
            - Altitude: 5000 [ft]
            - CAS: 220 [kts]
            - Bank angle: 22 [deg]
        """
        altitude_m = 5000 * FT2M  # convert altitude from ft to m
        rho, p, _, _ = atmos(altitude_m)  # atmospheric properties at 5000 ft
        V = cas_to_tas(220, rho, p) * KTS2MPS  # convert CAS to TAS
        self.turn_radius = V**2 / (G_CONST * np.tan(np.deg2rad(22.0)))  # turn radius

        self.org_rwy = org_rwy
        self.dest_rwy = dest_rwy
        # TODO: add final approach, missed approach
        # self.nav_code = MAPPING_NAV_TO_CODE[appr_type.upper()]
        self.num_interp_pnts = num_interp_pnts

        # Load relevant flight data
        # TODO: add final approach, missed approach
        # (
        #     self.org_rwy_coords,
        #     self.dest_rwy_coords,
        #     self.wpts_dep,
        #     self.wpts_enroute,
        #     self.wpts_star,
        #     self.wpts_apptr,
        #     self.wpts_final,
        # ) = LateralTrajectoryGenerator._load_flight_data(
        #     org_airport, org_rwy, sid, dest_airport, dest_rwy, star, appr_type.upper()
        # )
        (
            self.org_rwy_coords,
            self.dest_rwy_coords,
            self.wpts_dep,
            self.wpts_enroute,
            self.wpts_star,
        ) = LateralTrajectoryGenerator._load_flight_data(
            org_airport, org_rwy, sid, dest_airport, dest_rwy, star
        )

    def generate(
        self,
        # TODO: add final approach, missed approach
        # generate_missed_appr=False,
        return_wpts=False,
        return_distance=False,
    ):
        self.complete_trajectory = {}
        if return_distance:
            travel_distance = 0

        # Phase 1: origin airport -> SID
        enroute_entry = (self.wpts_enroute["lat"][0], self.wpts_enroute["lon"][0])
        departure = DepartureGenerator(
            self.org_rwy_coords,
            self.wpts_dep,
            self.turn_radius,
            enroute_entry,
            self.num_interp_pnts,
        )
        if return_distance:
            departure_trajectory, departure_distance = departure.generate(
                return_distance=True
            )
            travel_distance += departure_distance
        else:
            departure_trajectory = departure.generate(return_distance=False)
        self.complete_trajectory["departure_phase"] = departure_trajectory

        # Phase 2: SID -> STAR (en route)
        sid_exit = departure_trajectory[-1]
        enroute = EnrouteGenerator(
            self.wpts_enroute,
            self.turn_radius,
            sid_exit,
            self.wpts_star,
            self.num_interp_pnts,
        )
        if return_distance:
            enroute_trajectory, enroute_distance = enroute.generate(
                return_distance=True
            )
            travel_distance += enroute_distance
        else:
            enroute_trajectory = enroute.generate(return_distance=False)
        self.complete_trajectory["enroute_phase"] = enroute_trajectory

        # Phase 3: STAR -> destination airport
        enroute_exit = enroute_trajectory[-1]
        arrival = ArrivalGenerator(
            self.dest_rwy_coords,
            self.wpts_star,
            # TODO: add final approach, missed approach
            # self.wpts_apptr,
            # self.wpts_final,
            # self.nav_code,
            self.turn_radius,
            enroute_exit,
            self.num_interp_pnts,
        )
        if return_distance:
            arrival_trajectory, arrival_distance = arrival.generate(
                # TODO: add final approach, missed approach
                # generate_missed_appr=generate_missed_appr,
                return_distance=True,
            )
            travel_distance += arrival_distance
        else:
            arrival_trajectory = arrival.generate(
                # TODO: add final approach, missed approach
                # generate_missed_appr=generate_missed_appr,
                return_distance=False,
            )
        self.complete_trajectory["arrival_phase"] = arrival_trajectory

        # Combine into a full trajectory
        self.complete_trajectory["complete_coords"] = (
            departure_trajectory + enroute_trajectory + arrival_trajectory
        )

        if return_wpts:
            if return_distance:
                return (
                    self.complete_trajectory,
                    self.wpts_dep,
                    self.wpts_enroute,
                    self.wpts_star,
                    travel_distance / NM2M,
                )
            else:
                return (
                    self.complete_trajectory,
                    self.wpts_dep,
                    self.wpts_enroute,
                    self.wpts_star,
                )
        else:
            if return_distance:
                return self.complete_trajectory, travel_distance / NM2M
            else:
                return self.complete_trajectory

    @staticmethod
    def _load_flight_data(
        org_airport,
        org_rwy,
        sid,
        dest_airport,
        dest_rwy,
        star,
        # TODO: add final approach, missed approach
        # appr_type,
    ):
        # Load fixes
        table_fixes = read_csv(
            DATA_DIR / "Waypoints.txt", delimiter=",", header=None, index_col=False
        )

        # Load departure information
        org_rwy_coords = load_rwy_coords(org_airport, org_rwy)

        wpts_dep = load_sid_waypoints(
            DATA_DIR / "airports" / f"{org_airport}.txt", sid, org_rwy, table_fixes
        )

        # Load destination information
        dest_rwy_coords = load_rwy_coords(dest_airport, dest_rwy)

        wpts_star = load_star_waypoints(
            DATA_DIR / "airports" / f"{dest_airport}.txt", star, dest_rwy, table_fixes
        )

        # TODO: add final approach, missed approach
        # wpts_apptr = load_apptr_waypoints(
        #     DATA_DIR / "airports" / f"{dest_airport}.txt",
        #     star,
        #     dest_rwy,
        #     appr_type,
        #     table_fixes,
        # )

        # wpts_final = load_final_waypoints(
        #     DATA_DIR / "airports" / f"{dest_airport}.txt",
        #     dest_rwy,
        #     appr_type,
        #     table_fixes,
        # )

        # Select enroute waypoint based on selected SID and STAR
        enroute_llh = create_straight(
            wpts_dep["lat"][-1],
            wpts_dep["lon"][-1],
            wpts_star["lat"][0],
            wpts_star["lon"][0],
            num_points=100,
            return_distance=False,
            exclude_start=False,
        )
        all_wpts_llh = load_wpt_coords(DATA_DIR / "Waypoints.txt")
        wpts_enroute = select_enroute_waypoints(
            enroute_llh, all_wpts_llh, number_wpts_selected=5
        )

        return (
            org_rwy_coords,
            dest_rwy_coords,
            wpts_dep,
            wpts_enroute,
            wpts_star,
            # TODO: add final approach, missed approach
            # wpts_apptr,
            # wpts_final,
        )


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Define data for test

    # org_airport = "EDDF"
    # org_rwy = "07C"
    # sid = "ANEK1X"
    # dest_airport = "EDDB"
    # dest_rwy = "24R"
    # star = "KLF24R"
    # appr_type = "RNAV"

    # org_airport = "EDDB"
    # sid = "ARSA2Q"
    # org_rwy = "06R"
    # dest_airport = "EDDF"
    # star = "DEBH1D"
    # dest_rwy = "07C"

    # org_airport = "EDDM"
    # sid = "AKIN1S"
    # org_rwy = "26L"
    # dest_airport = "EDDB"
    # star = "KLF24R"
    # dest_rwy = "24R"

    # org_airport = "EDDM"
    # sid = "AKIN1S"
    # org_rwy = "26L"
    # dest_airport = "EDDF"
    # star = "DEBH1D"
    # dest_rwy = "07C"

    # org_airport = "NZQN"
    # sid = "ANPO5B"
    # org_rwy = "23"
    # dest_airport = "EDDK"
    # star = "ERNE2N"
    # dest_rwy = "31R"

    org_airport = "LFPG"
    sid = "AGOP6D"
    org_rwy = "27R"
    dest_airport = "EDDB"
    star = "KLF24R"
    dest_rwy = "24R"
    # TODO: add final approach, missed approach
    # appr_type = "RNAV"

    table_fixes = read_csv(
        DATA_DIR / "Waypoints.txt", delimiter=",", header=None, index_col=False
    )

    # Load departure information
    org_rwy_coords = load_rwy_coords(org_airport, org_rwy)

    wpts_dep = load_sid_waypoints(
        DATA_DIR / "airports" / f"{org_airport}.txt", sid, org_rwy, table_fixes
    )

    # Load destination information
    dest_rwy_coords = load_rwy_coords(dest_airport, dest_rwy)

    wpts_star = load_star_waypoints(
        DATA_DIR / "airports" / f"{dest_airport}.txt", star, dest_rwy, table_fixes
    )

    plt.figure(tight_layout=True)

    trajectory_generator = LateralTrajectoryGenerator(
        org_airport,
        org_rwy,
        sid,
        dest_airport,
        dest_rwy,
        star,
        # TODO: add final approach, missed approach
        # appr_type,
    )
    trajectory, travel_distance = trajectory_generator.generate(
        generate_missed_appr=True, return_distance=True
    )
    print(f"travel_distance = {travel_distance} NM")

    lats, lons = zip(*trajectory["complete_coords"])

    plt.scatter(
        org_rwy_coords[1],
        org_rwy_coords[0],
        marker="1",
        s=40,
        c="y",
        label="origin airport",
        zorder=1,
    )
    plt.scatter(
        dest_rwy_coords[1],
        dest_rwy_coords[0],
        marker="1",
        s=40,
        c="y",
        label="destination airport",
        zorder=1,
    )
    for i_sid in range(len(wpts_dep["lat"])):
        if i_sid != len(wpts_dep["lat"]) - 1:
            label = None
        else:
            label = "SID"
        plt.scatter(
            wpts_dep["lon"][i_sid],
            wpts_dep["lat"][i_sid],
            marker="x",
            linewidths=1.5,
            s=20,
            c="b",
            label=label,
            zorder=1,
        )
    for i_enroute in range(len(trajectory_generator.wpts_enroute["lat"])):
        if i_enroute != len(wpts_dep["lat"]) - 1:
            label = None
        else:
            label = "En Route"
        plt.scatter(
            trajectory_generator.wpts_enroute["lon"][i_enroute],
            trajectory_generator.wpts_enroute["lat"][i_enroute],
            marker="x",
            linewidths=1.5,
            s=20,
            c="r",
            label=label,
            zorder=1,
        )
    for i_star in range(len(wpts_star["lat"])):
        if i_star != len(wpts_star["lat"]) - 1:
            label = None
        else:
            label = "STAR"
        plt.scatter(
            wpts_star["lon"][i_star],
            wpts_star["lat"][i_star],
            marker="x",
            linewidths=1.5,
            s=20,
            c="g",
            label=label,
            zorder=1,
        )
    plt.legend(loc="best")
    plt.grid(True)
    plt.xlabel("Longitude [deg]")
    plt.ylabel("Latitude [deg]")
    plt.plot(lons, lats, linewidth=1.5, color="b", label="route", zorder=1)
    plt.show()
