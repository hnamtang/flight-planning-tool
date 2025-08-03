import argparse
import os


def parse_arguments():
    """
    Parse command-line arguments.
    """
    prog_description = (
        "Flight planning tool for generating lateral flight trajectories based on "
        " user-defined departure and arrival procedures. Supports configuration of "
        "origin/destination airports, runways, SIDs, STARs. Can be used with a GUI or "
        "in headless mode for automated processing and visualization.\nCurrently only "
        "supports generation of CF, DF, RF, and TF legs and visualization using "
        "matplotlib and gmplot."
    )
    prog_epilog = (
        "Example usage:\n"
        "  Launch GUI:\n"
        "    python3 main.py\n"
        "\n"
        "  Run in headless mode:\n"
        "    python3 main.py --no-gui \\\n"
        "                    --plot both \\\n"
        "                    --to-csv \\\n"
        "                    --org-airport EDDF \\\n"
        "                    --org-rwy 07C \\\n"
        "                    --sid ANEK1X \\\n"
        "                    --dest-airport EDDB \\\n"
        "                    --dest-rwy 24R \\\n"
        "                    --star KLF24R\n"
        "\n"
        "Note: Only CF, DF, RF, and TF legs are currently supported.\n"
    )
    parser = argparse.ArgumentParser(
        prog="Flight Planning Tool",
        description=prog_description,
        epilog=prog_epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # Save API key first
    parser.add_argument(
        "--save-api-key",
        type=str,
        metavar="KEY",
        help="Save Google Maps API key for 'gmplot'.",
    )

    # GUI or headless
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in headless mode without launching the GUI. After clicking 'generate', the program will automatically save trajectory coordinates as CSV file, the gmap plot as HTML file in ./output/ and shows the plots.",
    )

    parser.add_argument(
        "--plot",
        type=str,
        choices=["matplotlib", "gmplot", "both"],
        help="Select plotting backend. Options: 'matplotlib', 'gmplot' or 'both'.",
    )
    parser.add_argument(
        "--to-csv",
        action="store_true",
        help="Save trajectory coordinates to ./output/. Directory will be created if it does not exist.",
    )
    parser.add_argument(
        "--org-airport",
        type=str,
        default="EDDF",
        metavar="ICAO",
        help="ICAO code of origin airport (e.g., EDDF).",
    )
    parser.add_argument(
        "--org-rwy",
        type=str,
        default="07C",
        metavar="RWY",
        help="Runway ID of origin airport (e.g., 07C).",
    )
    parser.add_argument(
        "--sid",
        type=str,
        default="ANEK1X",
        metavar="SID",
        help="Standard Instrument Departure (SID) procedure name (e.g., ANEK1X).",
    )
    parser.add_argument(
        "--dest-airport",
        type=str,
        default="EDDB",
        metavar="ICAO",
        help="ICAO code of destination airport (e.g., EDDB).",
    )
    parser.add_argument(
        "--dest-rwy",
        type=str,
        default="24R",
        metavar="RWY",
        help="Runway ID of destination airport (e.g., 24R).",
    )
    parser.add_argument(
        "--star",
        type=str,
        default="KLF24R",
        metavar="STAR",
        help="Standard Terminal Arrival Route (STAR) procedure name (e.g., KLF24R).",
    )

    return parser.parse_args()
