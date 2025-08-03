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
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(800, 600)
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
        ax.plot(lons_enroute, lats_enroute, linestyle="-", color="m", zorder=1)
        _plot_wpts(ax, self.wpts_enroute, "m", "En route")

        # STAR
        lats_star, lons_star = zip(*self.trajectory["arrival_phase"])
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
        self.trajectory = trajectory
        self.wpts_dep = wpts_dep
        self.wpts_enroute = wpts_enroute
        self.wpts_star = wpts_star
        self.fig = None

    def plot(self):
        self.fig, ax = plt.subplots()

        # SID
        lats_sid, lons_sid = zip(*self.trajectory["departure_phase"])
        ax.plot(lons_sid, lats_sid, linestyle="-", color="b", zorder=1)
        _plot_wpts(ax, self.wpts_dep, "b", "SID")

        # En route
        lats_enroute, lons_enroute = zip(*self.trajectory["enroute_phase"])
        ax.plot(lons_enroute, lats_enroute, linestyle="-", color="m", zorder=1)
        _plot_wpts(ax, self.wpts_enroute, "m", "En route")

        # STAR
        lats_star, lons_star = zip(*self.trajectory["arrival_phase"])
        ax.plot(lons_star, lats_star, linestyle="-", color="g", zorder=1)
        _plot_wpts(ax, self.wpts_star, "g", "STAR")

        ax.set_xlabel("Longitude [deg]")
        ax.set_ylabel("Latitude [deg]")
        ax.legend(loc="best")
        ax.grid(True)

    def show(self):
        if self.fig:
            plt.show()
