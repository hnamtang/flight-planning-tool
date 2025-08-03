import sys

from src.utils import save_trajectory_to_csv
from src.utils.args import parse_arguments
from src.utils.config import load_api_key, save_api_key


def run_gui(args):
    from PyQt5.QtWidgets import QApplication

    from src.gui.gui import TrajectoryGeneratorGUI

    # Load API key for Google Maps
    api_key = load_api_key()
    if not api_key:
        print("Google Maps API key not found.")
        print("Please run: python3 main.py --save-api-key YOUR_KEY")
        sys.exit(1)

    app = QApplication(sys.argv)

    # Save to CSV if requested
    if args.to_csv:
        save_trajectory = True
    else:
        save_trajectory = False

    # Plot if requested
    if args.plot == "matplotlib":
        plot_matplotlib = True
        plot_gmplot = False
    elif args.plot == "gmplot":
        plot_matplotlib = False
        plot_gmplot = True
    elif args.plot == "both":
        plot_matplotlib = True
        plot_gmplot = True
    else:
        plot_matplotlib = False
        plot_gmplot = False

    gui = TrajectoryGeneratorGUI(
        api_key,
        plot_matplotlib=plot_matplotlib,
        plot_gmplot=plot_gmplot,
        save_trajectory=save_trajectory,
    )
    gui.show()
    sys.exit(app.exec_())


def run_cli(args):
    from src.plotting import GoogleMapPlot, StandardMatplotlibPlot
    from src.trajectory import LateralTrajectoryGenerator

    # Load API key for Google Maps
    api_key = load_api_key()
    if args.plot in ("gmplot", "both") and not api_key:
        print("Google Maps API key not found.")
        print("Please run: python3 main.py --save-api-key YOUR_KEY")
        sys.exit(1)

    # Generate trajectory based on user input
    trajectory_generator = LateralTrajectoryGenerator(
        args.org_airport,
        args.org_rwy,
        args.sid,
        args.dest_airport,
        args.dest_rwy,
        args.star,
    )
    trajectory, wpts_dep, wpts_enroute, wpts_star = trajectory_generator.generate(
        return_wpts=True
    )

    # Save to CSV if requested
    if args.to_csv:
        save_trajectory_to_csv(
            trajectory,
            args.org_airport,
            args.dest_airport,
        )

    # Plot
    if args.plot == "matplotlib":
        plotter = StandardMatplotlibPlot(trajectory, wpts_dep, wpts_enroute, wpts_star)
        plotter.plot()
        plotter.show()
    elif args.plot == "gmplot":
        plotter = GoogleMapPlot(
            trajectory,
            wpts_dep,
            wpts_enroute,
            wpts_star,
            args.org_airport,
            args.dest_airport,
        )
        plotter.plot(api_key)
        plotter.show()
    elif args.plot == "both":
        plotter_mpl = StandardMatplotlibPlot(
            trajectory, wpts_dep, wpts_enroute, wpts_star
        )
        plotter_mpl.plot()
        plotter_mpl.show()
        plotter_gm = GoogleMapPlot(
            trajectory,
            wpts_dep,
            wpts_enroute,
            wpts_star,
            args.org_airport,
            args.dest_airport,
        )
        plotter_gm.plot(api_key)
        plotter_gm.show()


def main():
    args = parse_arguments()

    # Handle API key
    if args.save_api_key:
        action = save_api_key(args.save_api_key)
        print(f"Google Maps API key {action} successfully.")
        return

    if args.no_gui:
        run_cli(args)
    else:
        run_gui(args)


if __name__ == "__main__":
    main()
