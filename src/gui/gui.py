from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..plotting import GoogleMapPlot, QtMatplotlibPlot
from ..trajectory.generator import LateralTrajectoryGenerator
from ..utils import (
    DATA_DIR,
    MAPPING_CODE_TO_NAV,
    load_airport_codes,
    save_trajectory_to_csv,
)
from ..utils import navdata_proc as nd


class SelectAllComboBox(QComboBox):
    def focusInEvent(self, event):
        super().focusInEvent(event)

        # selectAll only when the user focuses the field
        if self.isEditable():
            self.lineEdit().selectAll()


class TrajectoryGeneratorGUI(QWidget):
    def __init__(
        self, api_key, plot_matplotlib=False, plot_gmplot=False, save_trajectory=False
    ):
        super().__init__()

        self._api_key = api_key
        self._plot_matplotlib = plot_matplotlib
        self._plot_gmplot = plot_gmplot
        self._save_trajectory = save_trajectory

        # Ensure proper cleanup
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._plot_windows = []

        # Set GUI window title
        self.setWindowTitle("Flight Route Generator")

        # Get all airports
        self._all_airports = load_airport_codes(DATA_DIR / "airports")

        # Initialize
        self._org_rwy_list = []
        self._sid_list = []
        self._dest_rwy_list = []
        self._appr_type_list = []
        self._star_list = []

        self._is_org_valid = True
        self._is_org_rwy_valid = True
        self._is_sid_valid = True
        self._is_dest_valid = True
        self._is_dest_rwy_valid = True
        self._is_star_valid = True

        # Set GUI layouts
        self._set_gui_layout()

        # Load default data for default airports
        self._load_default_data()

        # Handle user input and react to Enter or Tab or 4 characters
        self._handle_user_input()

        # Set initial state of the Generate button to Enable
        self._update_button_state()

    def showEvent(self, event):
        """
        Override showEvent to set focus and select all text after window is shown
        """
        super().showEvent(event)

        # Use QTimer.singleShot to ensure the GUI is fully rendered
        QTimer.singleShot(0, self._set_initial_focus_and_select)

    def _set_initial_focus_and_select(self):
        """
        Set focus to origin combo and select all text
        """
        self._org_combo.setFocus()
        if self._org_combo.lineEdit():
            self._org_combo.lineEdit().selectAll()

    def closeEvent(self, event):
        """
        Handle window close events with proper cleanup
        """
        # Close any open plot windows
        for plot_window in self._plot_windows:
            if plot_window.isVisible():
                plot_window.close()

        # Accept the close event
        event.accept()

        # Clean exit
        super().closeEvent(event)

    def _set_gui_layout(self):
        self._widget_height = 30  # standard height for all widgets

        # Set fixed dimensions (width, height)
        self.setFixedWidth(640)

        # Layouts
        self._grid_layout = QGridLayout()

        # Set column spacing for better separation
        self._grid_layout.setVerticalSpacing(10)  # space between rows
        min_col_width = (200, 10, 100, 50, 500, 10, 100)
        for col, min_width in zip(range(7), min_col_width):
            self._grid_layout.setColumnMinimumWidth(col, min_width)

        # Show column labels: Departure, Arrival
        bold_font = QFont()
        bold_font.setBold(True)

        departure_label = QLabel("Departure")
        departure_label.setAlignment(Qt.AlignCenter)
        departure_label.setFont(bold_font)
        departure_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        departure_label.setFixedHeight(self._widget_height)

        arrival_label = QLabel("Arrival")
        arrival_label.setAlignment(Qt.AlignCenter)
        arrival_label.setFont(bold_font)
        arrival_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        arrival_label.setFixedHeight(self._widget_height)

        transition_label = QLabel("Transition")
        transition_label.setAlignment(Qt.AlignCenter)
        transition_label.setFont(bold_font)
        transition_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        transition_label.setFixedHeight(self._widget_height)

        # Show status of the GUI fields
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._status_label.setMinimumWidth(600)
        self._status_label.setFixedHeight(self._widget_height + 10)

        # Origin airport
        self._org_combo = SelectAllComboBox()
        self._org_combo.setFixedHeight(self._widget_height)
        self._org_combo.setEditable(True)
        self._org_combo.setInsertPolicy(QComboBox.NoInsert)
        self._org_combo.addItems(self._all_airports)

        # Departure runway
        self._org_rwy_combo = SelectAllComboBox()
        self._org_rwy_combo.setFixedHeight(self._widget_height)
        self._org_rwy_combo.setEditable(True)
        self._org_rwy_combo.setInsertPolicy(QComboBox.NoInsert)

        # SID
        self._sid_combo = SelectAllComboBox()
        self._sid_combo.setFixedHeight(self._widget_height)
        self._sid_combo.setEditable(True)
        self._sid_combo.setInsertPolicy(QComboBox.NoInsert)

        # Destination airport
        self._dest_combo = SelectAllComboBox()
        self._dest_combo.setFixedHeight(self._widget_height)
        self._dest_combo.setEditable(True)
        self._dest_combo.setInsertPolicy(QComboBox.NoInsert)

        # Arrival runway
        self._dest_rwy_combo = SelectAllComboBox()
        self._dest_rwy_combo.setFixedHeight(self._widget_height)
        self._dest_rwy_combo.setEditable(True)
        self._dest_rwy_combo.setInsertPolicy(QComboBox.NoInsert)

        # STAR
        self._star_combo = SelectAllComboBox()
        self._star_combo.setFixedHeight(self._widget_height)
        self._star_combo.setEditable(True)
        self._star_combo.setInsertPolicy(QComboBox.NoInsert)

        # Approach type
        self._appr_type_combo = SelectAllComboBox()
        self._appr_type_combo.setFixedHeight(self._widget_height)
        self._appr_type_combo.setEditable(True)
        self._appr_type_combo.setInsertPolicy(QComboBox.NoInsert)

        # Add widgets to grid layout in 2 columns
        # Add column labels
        self._grid_layout.addWidget(departure_label, 0, 0, 1, 3)
        self._grid_layout.addWidget(arrival_label, 0, 4, 1, 3)

        # Column 1-3: Origin airport, departure runway and SID
        label_org = QLabel("Origin Airport:")
        label_org.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_org.setFixedHeight(self._widget_height)
        self._grid_layout.addWidget(label_org, 1, 0)
        self._grid_layout.addWidget(self._org_combo, 1, 2)

        label_org_rwy = QLabel("Runway:")
        label_org_rwy.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_org_rwy.setFixedHeight(self._widget_height)
        self._grid_layout.addWidget(label_org_rwy, 2, 0)
        self._grid_layout.addWidget(self._org_rwy_combo, 2, 2)

        label_sid = QLabel("SID:")
        label_sid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_sid.setFixedHeight(self._widget_height)
        self._grid_layout.addWidget(label_sid, 3, 0)
        self._grid_layout.addWidget(self._sid_combo, 3, 2)

        # Column 5-7: Destination and STAR
        label_dest = QLabel("Destination Airport:")
        label_dest.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_dest.setFixedHeight(self._widget_height)
        self._grid_layout.addWidget(label_dest, 1, 4)
        self._grid_layout.addWidget(self._dest_combo, 1, 6)

        label_dest_rwy = QLabel("Runway:")
        label_dest_rwy.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_dest_rwy.setFixedHeight(self._widget_height)
        self._grid_layout.addWidget(label_dest_rwy, 2, 4)
        self._grid_layout.addWidget(self._dest_rwy_combo, 2, 6)

        label_star = QLabel("STAR:")
        label_star.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_star.setFixedHeight(self._widget_height)
        self._grid_layout.addWidget(label_star, 3, 4)
        self._grid_layout.addWidget(self._star_combo, 3, 6)

        label_appr_type = QLabel("Approach type:")
        label_appr_type.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_appr_type.setFixedHeight(self._widget_height)
        self._grid_layout.addWidget(label_appr_type, 4, 4)
        self._grid_layout.addWidget(self._appr_type_combo, 4, 6)

        # Add horizontal spacer for wider gap between columns
        h_spacer2 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self._grid_layout.addItem(h_spacer2, 1, 1, 4, 1)  # span 3 rows
        h_spacer6 = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self._grid_layout.addItem(h_spacer6, 1, 5, 4, 1)  # span 3 rows
        h_spacer4 = QSpacerItem(50, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self._grid_layout.addItem(h_spacer4, 1, 3, 4, 1)  # span 3 rows

        # Add status label spanning all columns
        self._grid_layout.addWidget(self._status_label, 9, 0, 1, 6)

        # Ensure both input columns use the same stretch factor
        self._grid_layout.setColumnStretch(2, 1)
        self._grid_layout.setColumnStretch(6, 1)

        # Create buttons
        self._create_buttons()

        # Create container widget for centering
        form_container = QWidget()
        form_container.setLayout(self._grid_layout)

        # Create main layout that centers the form container
        main_layout = QVBoxLayout()
        # main_layout.addWidget(form_container, alignment=Qt.AlignCenter)
        main_layout.addWidget(form_container)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Set the main layout
        self.setLayout(main_layout)
        self.adjustSize()
        self.setFixedHeight(self.height())

        # Set Tab order
        if self._appr_type_combo.isEditable():
            self.setTabOrder(self._org_combo, self._org_rwy_combo)
            self.setTabOrder(self._org_rwy_combo, self._sid_combo)
            self.setTabOrder(self._sid_combo, self._dest_combo)
            self.setTabOrder(self._dest_combo, self._dest_rwy_combo)
            self.setTabOrder(self._dest_rwy_combo, self._star_combo)
            self.setTabOrder(self._star_combo, self._appr_type_combo)
            self.setTabOrder(self._appr_type_combo, self._btn_generate)
            self.setTabOrder(self._btn_generate, self._btn_cancel)
            self.setTabOrder(self._btn_cancel, self._org_combo)
        else:
            self.setTabOrder(self._org_combo, self._org_rwy_combo)
            self.setTabOrder(self._org_rwy_combo, self._sid_combo)
            self.setTabOrder(self._sid_combo, self._dest_combo)
            self.setTabOrder(self._dest_combo, self._dest_rwy_combo)
            self.setTabOrder(self._dest_rwy_combo, self._star_combo)
            self.setTabOrder(self._star_combo, self._btn_generate)
            self.setTabOrder(self._btn_generate, self._btn_cancel)
            self.setTabOrder(self._btn_cancel, self._org_combo)

    def _create_buttons(self):
        """
        Create cancel and generate buttons
        """
        # Cancel button
        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.clicked.connect(self.close)

        # Generate button
        self._btn_generate = QPushButton("Generate")
        self._btn_generate.clicked.connect(self._generate_route)

        # Set button layout
        self._button_layout = QHBoxLayout()

        # Spacer to shift buttons to the right; adjust width for perfect alignment
        left_spacer = QSpacerItem(396, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self._button_layout.addItem(left_spacer)
        self._button_layout.addWidget(self._btn_cancel)
        self._button_layout.addSpacing(10)
        self._button_layout.addWidget(self._btn_generate)
        self._button_layout.addStretch()
        self._grid_layout.addLayout(self._button_layout, 5, 0, 1, 7)

    def _update_button_state(self):
        if self._status_label.text() == "":
            self._btn_generate.setEnabled(True)
        else:
            self._btn_generate.setEnabled(False)

    def _update_status_label_for_focused_widget(self):
        """
        Update status label based only on the currently focused widget. The status label
        shows the highest priority error based on tab order.
        """
        # Priority order matching the tab sequence
        priority_checks = [
            (
                self._is_org_valid,
                "Origin airport not found. Enter valid origin airport.",
            ),
            (
                self._is_org_rwy_valid,
                "Depature runway not found. Enter valid departure runway.",
            ),
            (self._is_sid_valid, "SID not found. Enter valid SID."),
            (
                self._is_dest_valid,
                "Destination airport not found. Enter valid destination airport.",
            ),
            (
                self._is_dest_rwy_valid,
                "Arrival runway not found. Enter valid arrival runway.",
            ),
            (self._is_star_valid, "STAR not found. Enter valid STAR."),
        ]

        # Find the first invalid field in priority order
        for is_valid, error_message in priority_checks:
            if not is_valid:
                self._status_label.setText(error_message)
                return

        # If all fields are valid, clear the status label
        self._status_label.clear()

    def _load_default_data(self):
        """
        Load default runway, SID, and STAR data for default airports
        """
        # Load data for default origin airport (EDDF)
        org_default = "EDDF"
        org_rwy_default = "07C"
        if org_default in self._all_airports:
            self._org_combo.setCurrentText(org_default)
            self._change_org(org_default, default_rwy=org_rwy_default)

        # Load data for default destination airport (EDDB)
        dest_default = "EDDB"
        dest_rwy_default = "24R"
        if dest_default in self._all_airports:
            self._dest_combo.setCurrentText(dest_default)
            self._change_dest(dest_default, default_rwy=dest_rwy_default)

        # Set default SID and STAR
        sid_default = "ANEK1X"
        self._change_org_rwy(org_rwy_default, default_sid=sid_default)

        star_default = "KLF24R"
        self._change_dest_rwy(dest_rwy_default, default_star=star_default)

        # Set default approach type
        appr_type_default = "I"
        self._change_appr_type(dest_rwy_default, default_appr_type=appr_type_default)

    def _handle_user_input(self):
        """
        Handle user input
        """
        # Access QLineEdit inside the combo box and react to Enter or Tab or 4 characters
        # Origin airport
        org_line_edit = self._org_combo.lineEdit()
        org_line_edit.editingFinished.connect(
            lambda: self._handle_airport_editing_finished("origin")
        )
        org_line_edit.textChanged.connect(
            lambda text: self._handle_airport_text_changed(text, "origin")
        )

        # Destination airport
        dest_line_edit = self._dest_combo.lineEdit()
        dest_line_edit.editingFinished.connect(
            lambda: self._handle_airport_editing_finished("destination")
        )
        dest_line_edit.textChanged.connect(
            lambda text: self._handle_airport_text_changed(text, "destination")
        )

        if self._status_label.text() not in [
            "Origin airport not found. Enter valid origin airport.",
            "Destination airport not found. Enter valid destination airport.",
        ]:
            # Origin runway
            org_rwy_line_edit = self._org_rwy_combo.lineEdit()
            org_rwy_line_edit.editingFinished.connect(
                lambda: self._handle_rwys_editing_finished("origin")
            )
            org_rwy_line_edit.textChanged.connect(
                lambda text: self._handle_rwys_text_changed(text, "origin")
            )

            # Destination runway
            dest_rwy_line_edit = self._dest_rwy_combo.lineEdit()
            dest_rwy_line_edit.editingFinished.connect(
                lambda: self._handle_rwys_editing_finished("destination")
            )
            dest_rwy_line_edit.textChanged.connect(
                lambda text: self._handle_rwys_text_changed(text, "destination")
            )

        if self._status_label.text() not in [
            "Origin airport not found. Enter valid origin airport.",
            "Destination airport not found. Enter valid destination airport.",
            "Departure runway not found. Enter valid RWY.",
            "Arrival runway not found. Enter valid RWY.",
        ]:
            # SID
            sid_line_edit = self._sid_combo.lineEdit()
            sid_line_edit.editingFinished.connect(
                lambda: self._handle_ats_route_editing_finished("sid")
            )
            sid_line_edit.textChanged.connect(
                lambda text: self._handle_ats_route_text_changed(text, "sid")
            )

            # STAR
            star_line_edit = self._star_combo.lineEdit()
            star_line_edit.editingFinished.connect(
                lambda: self._handle_ats_route_editing_finished("star")
            )
            star_line_edit.textChanged.connect(
                lambda text: self._handle_ats_route_text_changed(text, "star")
            )

    def _handle_airport_editing_finished(self, field):
        if field == "origin":
            text = self._org_combo.currentText().strip().upper()
            self._org_combo.blockSignals(True)

            self._is_org_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._all_airports, "airport"
            )
            if self._is_org_valid:
                self._org_combo.setCurrentText(text)
                self._change_org(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            else:
                self._org_rwy_combo.clear()
                self._sid_combo.clear()
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._org_combo.blockSignals(False)
        elif field == "destination":
            text = self._dest_combo.currentText().strip().upper()
            self._dest_combo.blockSignals(True)

            self._is_dest_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._all_airports, "airport"
            )
            if self._is_dest_valid:
                self._dest_combo.setCurrentText(text)
                self._change_dest(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            else:
                self._dest_rwy_combo.clear()
                self._star_combo.clear()
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._dest_combo.blockSignals(False)

    def _handle_airport_text_changed(self, text, field):
        text = text.strip().upper()
        if field == "origin":
            self._org_combo.blockSignals(True)
            self._org_combo.setCurrentText(text)

            self._is_org_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._all_airports, "airport"
            )
            if self._is_org_valid:
                self._org_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            elif len(text) == 4:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._org_combo.blockSignals(False)
        elif field == "destination":
            self._dest_combo.blockSignals(True)
            self._dest_combo.setCurrentText(text)

            self._is_dest_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._all_airports, "airport"
            )
            if self._is_dest_valid:
                self._dest_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            elif len(text) == 4:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._dest_combo.blockSignals(False)

    def _handle_rwys_editing_finished(self, field):
        if field == "origin":
            text = self._org_rwy_combo.currentText().strip().upper()
            self._org_rwy_combo.blockSignals(True)

            self._is_org_rwy_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._org_rwy_list, "runway"
            )
            if self._is_org_valid and self._is_org_rwy_valid:
                self._org_rwy_combo.setCurrentText(text)
                self._change_org_rwy(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            else:
                self._sid_combo.clear()
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._org_rwy_combo.blockSignals(False)
        elif field == "destination":
            text = self._dest_rwy_combo.currentText().strip().upper()
            self._dest_rwy_combo.blockSignals(True)

            self._is_dest_rwy_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._dest_rwy_list, "runway"
            )
            if self._is_dest_valid and self._is_dest_rwy_valid:
                self._dest_rwy_combo.setCurrentText(text)
                self._change_dest_rwy(text)
                self._change_appr_type(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            else:
                self._star_combo.clear()
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._dest_rwy_combo.blockSignals(False)

    def _handle_rwys_text_changed(self, text, field):
        text = text.strip().upper()
        if field == "origin":
            self._org_rwy_combo.blockSignals(True)
            self._org_rwy_combo.setCurrentText(text)

            self._is_org_rwy_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._org_rwy_list, "runway"
            )
            if self._is_org_valid and self._is_org_rwy_valid:
                self._org_rwy_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            elif len(text) >= 2:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._org_rwy_combo.blockSignals(False)
        elif field == "destination":
            self._dest_rwy_combo.blockSignals(True)
            self._dest_rwy_combo.setCurrentText(text)

            self._is_dest_rwy_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._dest_rwy_list, "runway"
            )
            if self._is_dest_valid and self._is_dest_rwy_valid:
                self._dest_rwy_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            elif len(text) >= 2:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._dest_rwy_combo.blockSignals(False)

    def _handle_ats_route_editing_finished(self, field):
        if field == "sid":
            text = self._sid_combo.currentText().strip().upper()
            self._sid_combo.blockSignals(True)

            self._is_sid_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._sid_list, "sid"
            )
            if self._is_sid_valid:
                self._sid_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            else:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._sid_combo.blockSignals(False)
        elif field == "star":
            text = self._star_combo.currentText().strip().upper()
            self._star_combo.blockSignals(True)

            self._is_star_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._star_list, "star"
            )
            if self._is_star_valid:
                self._star_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            else:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._star_combo.blockSignals(False)

    def _handle_ats_route_text_changed(self, text, field):
        text = text.strip().upper()
        if field == "sid":
            self._sid_combo.blockSignals(True)
            self._sid_combo.setCurrentText(text)

            self._is_sid_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._sid_list, "sid"
            )
            if self._is_sid_valid:
                self._sid_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            elif len(text) == 6:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._sid_combo.blockSignals(False)
        elif field == "star":
            self._star_combo.blockSignals(True)
            self._star_combo.setCurrentText(text)

            self._is_star_valid = TrajectoryGeneratorGUI._validate_user_input(
                text, self._star_list, "star"
            )
            if self._is_star_valid:
                self._star_combo.setCurrentText(text)
                self._update_status_label_for_focused_widget()
                self._update_button_state()
            elif len(text) == 6:
                self._update_status_label_for_focused_widget()
                self._update_button_state()

            self._star_combo.blockSignals(False)

    def _change_org(self, origin, default_rwy=None):
        """
        Extract departure information based on selected origin airport
        """
        # Retrieve the selected origin airport
        org_airport_file = DATA_DIR / "airports" / f"{origin}.txt"

        # Show runways based on selected origin airport
        self._org_rwy_list, _, _ = TrajectoryGeneratorGUI._load_airport_data(
            org_airport_file, category="origin"
        )
        self._org_rwy_combo.blockSignals(True)
        org_rwy_prev = self._org_rwy_combo.currentText()
        self._org_rwy_combo.clear()
        if self._org_rwy_list:
            # Set default runway at start of the GUI
            if default_rwy and default_rwy in self._org_rwy_list:
                self._org_rwy_combo.setCurrentText(default_rwy)
            else:
                self._org_rwy_combo.addItems(self._org_rwy_list)
                if org_rwy_prev in self._org_rwy_list:
                    self._org_rwy_combo.setCurrentText(org_rwy_prev)
        self._org_rwy_combo.blockSignals(False)

        # Exclude the origin airport for the destination airport list
        dest_airport = self._dest_combo.currentText()
        if dest_airport in self._all_airports:
            TrajectoryGeneratorGUI._filter_combo(
                self._dest_combo, dest_airport, self._all_airports, origin
            )

    def _change_org_rwy(self, runway, default_sid=False):
        """
        Extract SID based on selected origin runway
        """
        # Retrieve the selected airport
        org_airport = self._org_combo.currentText()

        # Show SIDs based on selected runway
        _, sids_rwys, sids = TrajectoryGeneratorGUI._load_airport_data(
            DATA_DIR / "airports" / f"{org_airport}.txt", category="origin"
        )
        sid_list = [
            sid for sid, rwy in zip(sids, sids_rwys) if rwy == runway or rwy == "ALL"
        ]
        self._sid_list = sorted(set(sid_list))
        self._sid_combo.blockSignals(True)
        sid_prev = self._sid_combo.currentText()
        self._sid_combo.clear()
        if self._sid_list:
            # Set default SID at start of the GUI
            if default_sid and default_sid in self._sid_list:
                self._sid_combo.setCurrentText(default_sid)
            else:
                self._sid_combo.addItems(self._sid_list)
                if sid_prev in self._sid_list:
                    self._sid_combo.setCurrentText(sid_prev)
            self._sid_combo.setEnabled(True)
            self._sid_combo.setEditable(True)
        else:  # disable if no valid SID
            self._sid_combo.clear()
            self._sid_combo.setEnabled(False)
        self._sid_combo.blockSignals(False)

    def _change_dest(self, destination, default_rwy=None, default_appr_type=None):
        """
        Extract arrival information based on selected destination airport
        """
        # Retrieve the selected destination airport
        dest_airport_file = DATA_DIR / "airports" / f"{destination}.txt"

        # Show runways based on selected destination airport
        approaches, _ = TrajectoryGeneratorGUI._load_airport_data(
            dest_airport_file, category="destination"
        )
        filtered_rwys = [rwy for rwy in approaches["rwys"] if rwy != "ALL"]
        self._dest_rwy_list = sorted(set(filtered_rwys))
        self._dest_rwy_combo.blockSignals(True)
        dest_rwy_prev = self._dest_rwy_combo.currentText()
        self._dest_rwy_combo.clear()
        if self._dest_rwy_list:
            # Set default runway at start of the GUI
            if default_rwy and default_rwy in self._dest_rwy_list:
                self._dest_rwy_combo.setCurrentText(default_rwy)
            else:
                self._dest_rwy_combo.addItems(self._dest_rwy_list)
                if dest_rwy_prev in self._dest_rwy_list:
                    self._dest_rwy_combo.setCurrentText(dest_rwy_prev)
        self._dest_rwy_combo.blockSignals(False)

        # Exclude the origin airport for the destination airport list
        org_airport = self._org_combo.currentText()
        if org_airport in self._all_airports:
            TrajectoryGeneratorGUI._filter_combo(
                self._org_combo, org_airport, self._all_airports, destination
            )

    def _change_dest_rwy(self, runway, default_star=None):
        """
        Extract STAR based on selected arrival runway
        """
        # Retrieve the selected airport
        dest_airport = self._dest_combo.currentText()

        # Show STARs based on selected runway
        _, stars = TrajectoryGeneratorGUI._load_airport_data(
            DATA_DIR / "airports" / f"{dest_airport}.txt", category="destination"
        )
        star_list = [
            star
            for star, rwy in zip(stars[1], stars[0])
            if rwy == runway or rwy == "ALL"
        ]
        self._star_list = sorted(set(star_list))
        self._star_combo.blockSignals(True)
        star_prev = self._star_combo.currentText()
        self._star_combo.clear()
        if self._star_list:
            # Set default STAR at start of the GUI
            if default_star and default_star in self._star_list:
                self._star_combo.setCurrentText(default_star)
            else:
                self._star_combo.addItems(self._star_list)
                if star_prev in self._star_list:
                    self._star_combo.setCurrentText(star_prev)
            self._star_combo.setEnabled(True)
            self._star_combo.setEditable(True)
        else:  # disable if no valid STAR
            self._star_combo.clear()
            self._star_combo.setEnabled(False)
        self._star_combo.blockSignals(False)

    def _change_appr_type(self, rwy, default_appr_type=None):
        """
        Extract approach type based on selected airport and runway
        """
        # Retrieve the selected airport
        dest_airport = self._dest_combo.currentText().strip().upper()

        # Retrieve the selected runway
        dest_rwy = rwy

        # Retrieved selected STAR
        selected_star = self._star_combo.currentText().strip().upper()

        # Get approach type
        transitions = TrajectoryGeneratorGUI._load_airport_data(
            DATA_DIR / "airports" / f"{dest_airport}.txt", category="transition"
        )
        filtered_appr_types = []
        for i, (name, runway) in enumerate(
            zip(transitions["name"], transitions["rwys"])
        ):
            if i == 0:
                continue

            if (
                name == selected_star
                or name == selected_star[:3]
                or name[:3] == selected_star[:3]
                and runway == dest_rwy
            ):
                filtered_appr_types.append(transitions["types"][i])
        appr_type_list = [MAPPING_CODE_TO_NAV[appr[0]] for appr in filtered_appr_types]
        self._appr_type_list = sorted(set(appr_type_list))
        self._appr_type_combo.blockSignals(True)
        appr_type_prev = self._appr_type_combo.currentText()
        self._appr_type_combo.clear()
        if self._appr_type_list:
            # Set default approach type at start of the GUI
            if default_appr_type:
                appr_type_default = MAPPING_CODE_TO_NAV[default_appr_type]
                if appr_type_default in self._appr_type_list:
                    self._appr_type_combo.setCurrentText(appr_type_default)
            else:
                self._appr_type_combo.addItems(self._appr_type_list)
                if appr_type_prev in self._appr_type_list:
                    self._appr_type_combo.setCurrentText(appr_type_prev)
            self._appr_type_combo.setEnabled(True)
            self._appr_type_combo.setEditable(True)
        else:  # disable if no valid approach types
            self._appr_type_combo.clear()
            self._appr_type_combo.setEnabled(False)
        self._appr_type_combo.blockSignals(False)

    def _generate_route(self):
        """
        Generate route based on user selections
        """
        org = self._org_combo.currentText()
        org_rwy = self._org_rwy_combo.currentText()
        sid = self._sid_combo.currentText()
        dest = self._dest_combo.currentText()
        dest_rwy = self._dest_rwy_combo.currentText()
        star = self._star_combo.currentText()
        # TODO: used for final approach, missed approach
        # appr_type = self._appr_type_combo.currentText()

        try:
            generator = LateralTrajectoryGenerator(
                org,
                org_rwy,
                sid,
                dest,
                dest_rwy,
                star,
                # TODO: used for final approach, missed approach
                # appr_type,
            )
            (
                trajectory,
                wpts_dep,
                wpts_enroute,
                wpts_star,
            ) = generator.generate(return_wpts=True)

            # Save trajectory coordinates to CSV
            if self._save_trajectory:
                save_trajectory_to_csv(trajectory, org, dest)

            if self._plot_matplotlib:
                self._generate_plot_matplotlib(
                    trajectory, wpts_dep, wpts_enroute, wpts_star
                )
            if self._plot_gmplot:
                self._generate_plot_gmplot(
                    trajectory, wpts_dep, wpts_enroute, wpts_star
                )
        except Exception as e:
            print(f"[ERROR] Error in calculating route: {e}")

    def _generate_plot_matplotlib(self, trajectory, wpts_dep, wpts_enroute, wpts_star):
        """
        Plot the flight route.
        """
        # Close all existing plot windows if exist
        for plot_window in self._plot_windows:
            try:
                if plot_window.isVisible():
                    plot_window.close()
            except RuntimeError:
                continue  # already deleted
        self._plot_windows.clear()

        # Window shows the complete route
        self._qt_plotter = QtMatplotlibPlot(
            trajectory=trajectory,
            title="Complete Route",
            wpts_dep=wpts_dep,
            wpts_enroute=wpts_enroute,
            wpts_star=wpts_star,
        )
        self._qt_plotter.plot()
        self._qt_plotter.show()
        self._plot_windows.append(self._qt_plotter)

    def _generate_plot_gmplot(self, trajectory, wpts_dep, wpts_enroute, wpts_star):
        org = self._org_combo.currentText()
        dest = self._dest_combo.currentText()

        # Gmap plot
        self._map_plotter = GoogleMapPlot(
            trajectory,
            wpts_dep,
            wpts_enroute,
            wpts_star,
            org,
            dest,
        )
        self._map_plotter.plot(self._api_key)
        self._map_plotter.show()

    @staticmethod
    def _load_airport_data(airport_file, category):
        if category == "origin":
            dep_rwys, sids_rwys, sids, _ = nd.load_departures(airport_file)
            return dep_rwys, sids_rwys, sids
        elif category == "destination":
            approaches, _, stars = nd.load_arrivals(airport_file)
            return approaches, stars
        elif category == "transition":
            _, transitions, _ = nd.load_arrivals(airport_file)
            return transitions

    @staticmethod
    def _validate_user_input(code, entry_list, field):
        if field == "airport":
            valid = len(code) == 4 and code in entry_list
        elif field == "runway":
            valid = len(code) >= 2 and code in entry_list
        elif field == "sid" or field == "star":
            valid = code in entry_list or entry_list == []

        return valid

    @staticmethod
    def _filter_combo(combo, item_name, item_list, exclusions):
        """Update the combo box with items not in exclusions"""
        filtered = [it for it in item_list if it not in exclusions]
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(filtered)
        if item_name in filtered:
            combo.setCurrentText(item_name)
        combo.blockSignals(False)
