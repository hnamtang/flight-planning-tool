import webbrowser
from datetime import datetime

from gmplot import gmplot

from ..utils import PROJECT_ROOT


class GoogleMapPlot:
    def __init__(
        self,
        trajectory,
        wpts_dep,
        wpts_enroute,
        wpts_star,
        org_airport,
        dest_airport,
    ):
        self.trajectory = trajectory
        self.wpts_dep = wpts_dep
        self.wpts_enroute = wpts_enroute
        self.wpts_star = wpts_star
        self.org_airport = org_airport
        self.dest_airport = dest_airport
        self._output_html_path = None

    def plot(self, api_key):
        idx_center = len(self.trajectory["complete_coords"]) // 2
        center_lat = self.trajectory["complete_coords"][idx_center][0]
        center_lon = self.trajectory["complete_coords"][idx_center][1]

        self._gmap = gmplot.GoogleMapPlotter(center_lat, center_lon, 10, apikey=api_key)

        # SID
        lats_sid, lons_sid = zip(*self.trajectory["departure_phase"])
        self._gmap.scatter(
            self.wpts_dep["lat"],
            self.wpts_dep["lon"],
            color="b",
            edge_width=2,
            size=300,
            marker=False,
            label="SID",
            symbol="x",
        )
        self._gmap.plot(lats_sid, lons_sid, color="b", edge_width=3, markersize=10)

        # En route
        lats_enroute, lons_enroute = zip(*self.trajectory["enroute_phase"])
        self._gmap.scatter(
            self.wpts_enroute["lat"],
            self.wpts_enroute["lon"],
            color="m",
            edge_width=2,
            size=300,
            marker=False,
            label="En route",
            symbol="x",
        )
        self._gmap.plot(
            lats_enroute, lons_enroute, color="m", edge_width=3, markersize=10
        )

        # STAR
        lats_star, lons_star = zip(*self.trajectory["arrival_phase"])
        self._gmap.scatter(
            self.wpts_star["lat"],
            self.wpts_star["lon"],
            color="g",
            edge_width=2,
            size=300,
            marker=False,
            label="STAR",
            symbol="x",
        )
        self._gmap.plot(lats_star, lons_star, color="g", edge_width=3, markersize=10)

        # Save plot to HTML file
        output_dir = PROJECT_ROOT / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        time_formatted = now.strftime("%Y-%m-%d_%H-%M")
        output_filename = f"{self.org_airport}-{self.dest_airport}_{time_formatted}"
        self._output_html_path = output_dir / f"{output_filename}.html"

        self._gmap.draw(self._output_html_path)
        print(f"Google Maps plot HTML file saved to: {self._output_html_path}")

    def show(self):
        if self._output_html_path:
            webbrowser.open(self._output_html_path.as_uri(), new=2)
