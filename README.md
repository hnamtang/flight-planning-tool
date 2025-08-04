# Flight Management and Procedure Design

## Project Part 2 - Lateral Trajectory Generation

This project focuses on generating lateral trajectories for Flight Management System (FMS), based on user-defined departure and destination airport, runways, and procedures (SID/STAR).
The primary goal is to compute a lateral flight path in conformance with the published waypoints and the associated ARINC 424 leg types.

## Current Capabilities

- **Supported leg types**: CF, DF, RF, and TF (4 of 23 ARINC 424 types).
- **Supported phases**: SID, en route, and STAR.
- **En route selection**: Waypoints are automatically chosen near the great-circle route between SID exit and STAR entry points using a K-D Tree algorithm.

Future development may include support for additional leg types, SID transition, approach transition, final approach, and missed approach procedures, and constraints on en route waypoint selection (e.g., due to airspace restrictions).

## Requirements

- Python 3.11 or higher.
- Virtual environment (recommended).

Ensure Python and all required dependencies are installed in a virtual environment:

```bash
python3 -m venv .venv
source ./.venv/bin/activate
pip install -r requirements.txt
```

To use the Google Maps plot (`gmplot`), set your API key once:

```bash
python3 main.py --save-api-key YOUR_KEY
```

## Usage

The main script is `./main.py`. Run it with a GUI or in headless mode.

### GUI Mode

Launch the GUI:

```bash
python3 main.py [options]
```

- Input parameters via the interface.
- Use command-line options to control the behavior when the "generate" button is clicked.

**Options:** The GUI mode accepts the following command-line arguments

- `--to-csv`
  - Opens the GUI.
  - Clicking "generate" button saves the trajectory coordinates to a CSV file in `./output/`.
- `--plot {matplotlib,gmplot,both}`
  - Opens the GUI.
  - Clicking "generate" button displays the trajectory plot using the specified backend (Matplotlib, gmplot, or both).

**Examples:**

Open GUI, save CSV, plot with Google Maps:

```bash
python3 main.py --to-csv --plot gmplot
```

Open GUI, no CSV, plot with Matplotlib and Google Maps:

```bash
python3 main.py --plot both
```

**Note:** The CSV and plot file are saved in `./output/` by default.

### Headless Mode

Run without GUI:

```bash
python3 main.py --no-gui [options]
```

**Options:** The headless mode accepts the following command-line arguments

- `--plot {matplotlib,gmplot,both}`: Specifies the plotting backends. `matplotlib` | `gmplot` | `both`. If omitted, the trajectory will not be plotted.
- `--to-csv`: Saves the trajectory coordinates to CSV.
- `--org-airport ICAO`: Specifies ICAO code of origin airport (e.g., EDDF).
- `--org-rwy RWY`: Specifies runway ID of origin airport (e.g., 07C).
- `--sid SID`: Specifies Standard Instrument Departure (SID) procedure (e.g., ANEK1X).
- `--dest-airport ICAO`: Specifies ICAO code of destination airport (e.g., EDDB).
- `--dest-rwy RWY`: Specifies runway ID of destination airport (e.g., 24R).
- `--star STAR`: Specifies Stanrdard Terminal Arrival Route (STAR) procedure (e.g., KLF24R).

**Examples:**

Generate trajectory from EDDF (Frankfurt Airport), runway 07C, with SID ANEK1X to EDDB (Berlin Brandenburg Airport), runway 24R, with STAR KLF24R, save CSV, no plot:

```bash
python3 main.py --no-gui --to-csv --org-airport EDDF --org-rwy 07C --sid ANEK1X --dest-airport EDDB --dest-rwy 24R --star KLF24R
```

Generate trajectory from OTBD (Doha International Airport), runway 33, with SID ALVE3N to EDDM (Munich Airport), runway 26R, with STAR ELMO1D, save CSV, plot with Matplotlib:

```bash
python3 main.py --no-gui --to-csv --plot matplotlib --org-airport OTBD --org-rwy 33 --sid ALVE3N --dest-airport EDDM --dest-rwy 26R --star ELMO1D
```

Generate trajectory from ZBAA (Beijing Capital International Airport), runway 18L, with SID BOTP6J to RJTT airport (Haneda Airport), runway 34L, with STAR AKSE1A, no CSV, plot with Google Maps:

```bash
python3 main.py --no-gui --plot gmplot --org-airport ZBAA --org-rwy 18L --sid BOTP6J --dest-airport RJTT --dest-rwy 34L --star AKSE1A
```

## Output

- **Google Maps Plot**: An `.html` file will be saved in `./output/` and automatically opened in the default browser.
  - **Blue line/markers**: Indicate the SID segment.
  - **Magenta line/markers**: Indicate the en route segment.
  - **Green line/markers**: Indicate the STAR segment.
- **Trajectory coordinates file**: A `.csv` file will be saved in `./output/`. Columns are:
  - `lat`: Latitude coordinates in degrees.
  - `lon`: Longitude coordinates in degrees.
  - `segment`: Segment of the flight route (SID, Enroute, STAR).

## Code Formatting and Linting

This project uses `ruff` for Python code formatting and linting, configured in `pyproject.toml`.

Run the following command from the project's root directory to format and fix lint issues:

```ruff
ruff format . && ruff check . --fix
```
