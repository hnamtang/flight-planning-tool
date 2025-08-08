import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure


def _plot_wpts(axis, wpts, color, label):
    """
    Plot waypoints on specified pyplot axis.
    """
    axis.scatter(
        wpts["lon"][0], wpts["lat"][0], marker="x", c=color, s=15, label=label, zorder=2
    )

    if len(wpts["lat"]) > 1:
        axis.scatter(
            wpts["lon"][1:], wpts["lat"][1:], marker="x", c=color, s=15, zorder=2
        )

    for lon, lat, name in zip(wpts["lon"], wpts["lat"], wpts["name"]):
        axis.text(lon, lat, name, fontsize=9, zorder=3)


class QtMatplotlibPlot(QtWidgets.QMainWindow):
    def __init__(self, trajectory, title, wpts_dep, wpts_enroute, wpts_star):
        """
        Plot trajectory with Matplotlib for GUI application.

        Parameters
        ----------
        trajectory : dict
            A dictionary contains latitude and longitude [deg] of interpolated points
            of the flight route. The dictionary contains the following keys:

                * `complete_coords` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the complete flight route
                * `departure_phase` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the departure phase (SID)
                * `enroute_phase` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the en route phase
                * `arrival_phase` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the arrival phase (STAR)

        title : str
            Title of GUI window

        wpts_dep, wpts_enroute, wpts_star : dict
            Dictionaries contain data of departure, en route and arrival waypoints used
            for SID procedure. 2 relevant keys for this class are:

                * `lat` : list
                    A list contains latitudes of all corresponding waypoints [deg]
                * `lon` : list
                    A list contains longitudes of all corresponding waypoints [deg]
        """
        super().__init__()
        self.setWindowTitle(title)
        # self.setFixedSize(800, 600)
        self.resize(800, 600)
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        self.layout = QtWidgets.QVBoxLayout(self._main)
        self.canvas = FigureCanvas(Figure(figsize=(4, 3)))
        self.layout.addWidget(NavigationToolbar(self.canvas, self))

        self.layout.addWidget(self.canvas)

        # Store data
        self.trajectory = trajectory
        self.wpts_dep = wpts_dep
        self.wpts_enroute = wpts_enroute
        self.wpts_star = wpts_star

    def plot(self):
        ax = self.canvas.figure.subplots()

        # SID
        lats_sid, lons_sid = zip(*self.trajectory["departure_phase"])
        ax.plot(lons_sid, lats_sid, linestyle="-", color="b", zorder=1)
        _plot_wpts(ax, self.wpts_dep, "b", "SID")

        # Enroute
        lats_enroute, lons_enroute = zip(*self.trajectory["enroute_phase"])
        ax.plot(
            [lons_sid[-1], lons_enroute[0]],
            [lats_sid[-1], lats_enroute[0]],
            linestyle="-",
            color="m",
            zorder=1,
        )
        ax.plot(lons_enroute, lats_enroute, linestyle="-", color="m", zorder=1)
        _plot_wpts(ax, self.wpts_enroute, "m", "En route")

        # STAR
        lats_star, lons_star = zip(*self.trajectory["arrival_phase"])
        ax.plot(
            [lons_enroute[-1], lons_star[0]],
            [lats_enroute[-1], lats_star[0]],
            linestyle="-",
            color="g",
            zorder=1,
        )
        ax.plot(lons_star, lats_star, linestyle="-", color="g", zorder=1)
        _plot_wpts(ax, self.wpts_star, "g", "STAR")

        ax.set_xlabel("Longitude [deg]")
        ax.set_ylabel("Latitude [deg]")
        ax.legend(loc="best")
        ax.grid(True)

        self.canvas.draw()

    def closeEvent(self, event):
        """
        Clean up plot window resources
        """
        plt.close(self.canvas.figure)
        event.accept()
        super().closeEvent(event)


class StandardMatplotlibPlot:
    def __init__(self, trajectory, wpts_dep, wpts_enroute, wpts_star):
        """
        Plot trajectory with Matplotlib.

        Parameters
        ----------
        trajectory : dict
            A dictionary contains latitude and longitude [deg] of interpolated points
            of the flight route. The dictionary contains the following keys:

                * `complete_coords` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the complete flight route
                * `departure_phase` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the departure phase (SID)
                * `enroute_phase` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the en route phase
                * `arrival_phase` : list
                    A list contains latitudes and longitudes [deg] in form of (lat, lon)
                    for the arrival phase (STAR)

        wpts_dep, wpts_enroute, wpts_star : dict
            Dictionaries contain data of departure, en route and arrival waypoints used
            for SID procedure. 2 relevant keys for this class are:

                * `lat` : list
                    A list contains latitudes of all corresponding waypoints [deg]
                * `lon` : list
                    A list contains longitudes of all corresponding waypoints [deg]
        """
        self.trajectory = trajectory
        self.wpts_dep = wpts_dep
        self.wpts_enroute = wpts_enroute
        self.wpts_star = wpts_star
        self.fig = None

    def plot(self, is_latex=False):
        if is_latex:
            # Update rcParams for LaTeX
            plt.rcParams.update(
                {
                    "text.usetex": True,
                    "font.family": "serif",
                    "font.serif": ["Computer Modern"],
                    "font.size": 8,
                    "lines.linewidth": 1,
                    "grid.alpha": 0.3,
                }
            )
            fig_size = (3.5, 2.16)  # IEEE single column
        else:
            fig_size = (6.4, 4.8)

        self.fig, ax = plt.subplots(figsize=fig_size)

        # SID
        lats_sid, lons_sid = zip(*self.trajectory["departure_phase"])
        if not is_latex:
            ax.plot(lons_sid, lats_sid, linestyle="-", color="b", zorder=1)
            _plot_wpts(ax, self.wpts_dep, "b", "SID")
        else:
            ax.plot(lons_sid, lats_sid, linestyle="-", color="b", label="SID", zorder=1)

        # En route
        lats_enroute, lons_enroute = zip(*self.trajectory["enroute_phase"])
        ax.plot(
            [lons_sid[-1], lons_enroute[0]],
            [lats_sid[-1], lats_enroute[0]],
            linestyle="-",
            color="m",
            zorder=1,
        )
        if not is_latex:
            ax.plot(lons_enroute, lats_enroute, linestyle="-", color="m", zorder=1)
            _plot_wpts(ax, self.wpts_enroute, "m", "En route")
        else:
            ax.plot(
                lons_enroute,
                lats_enroute,
                linestyle="-",
                color="m",
                label="En route",
                zorder=1,
            )

        # STAR
        lats_star, lons_star = zip(*self.trajectory["arrival_phase"])
        ax.plot(
            [lons_enroute[-1], lons_star[0]],
            [lats_enroute[-1], lats_star[0]],
            linestyle="-",
            color="g",
            zorder=1,
        )
        if not is_latex:
            ax.plot(lons_star, lats_star, linestyle="-", color="g", zorder=1)
            _plot_wpts(ax, self.wpts_star, "g", "STAR")
        else:
            ax.plot(
                lons_star,
                lats_star,
                linestyle="-",
                color="g",
                label="STAR",
                zorder=1,
            )

        ax.set_xlabel("Longitude [deg]")
        ax.set_ylabel("Latitude [deg]")
        ax.legend(loc="best")
        ax.grid(True)

    def show(self):
        if self.fig:
            plt.show()

    def save(self, fig_name, img_type):
        if self.fig:
            if not fig_name:
                raise ValueError("fig_name is missing.")

            from ..utils import PROJECT_ROOT

            if img_type.upper() == "PDF":
                self.fig.savefig(
                    PROJECT_ROOT / "output" / f"{fig_name}.pdf",
                    format="pdf",
                    dpi=1200,
                    bbox_inches="tight",
                )
            elif img_type.upper() == "EPS":
                self.fig.savefig(
                    PROJECT_ROOT / "output" / f"{fig_name}.eps",
                    format="eps",
                    dpi=1200,
                    bbox_inches="tight",
                )
            elif img_type.upper() == "PNG":
                self.fig.savefig(
                    PROJECT_ROOT / "output" / f"{fig_name}.png",
                    format="png",
                    dpi=1200,
                    bbox_inches="tight",
                )
            else:
                raise ValueError("img_type is missing.")
