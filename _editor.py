import json
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QColorDialog, QMessageBox, QApplication,
    QStackedWidget, QCheckBox, QComboBox, QDialog, QLabel, QDialogButtonBox,
    QGridLayout, QGraphicsDropShadowEffect, QMenu, QLineEdit, QListWidget, 
    QListWidgetItem, QAbstractItemView, QInputDialog, QTextBrowser
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont

from datetime import datetime
from _logging import log_to_gui


class AddDriverDialog(QDialog):
    def __init__(self, parent, current_source, tag_categories, car_classes, existing_ids, save_callback):
        super().__init__(parent)
        self.current_source = current_source
        self.tag_categories = tag_categories
        self.car_classes = car_classes
        self.existing_ids = existing_ids
        self.save_callback = save_callback  # Save callback for saving the driver

        self.setWindowTitle("Add Driver")
        self.setFixedSize(400, 350)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #e0f7ff, stop: 1 #ffffff
                );
                border-radius: 10px;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 6px;
                font-size: 14px;
                color: #333333;
            }
        """)

        layout = QVBoxLayout(self)

        # iRacing ID Input
        self.id_label = QLabel("iRacing ID:")
        layout.addWidget(self.id_label)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter a 5 to 8-digit iRacing ID")
        self.id_input.textChanged.connect(self.validate_inputs)
        layout.addWidget(self.id_input)

        # Driver Name Input
        self.name_label = QLabel("Driver Name:")
        layout.addWidget(self.name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter driver name")
        self.name_input.textChanged.connect(self.validate_inputs)
        layout.addWidget(self.name_input)

        # Dynamic Fields for iOverlay or CrewChief
        if self.current_source == "iOverlay":
            self.group_label = QLabel("Group:")
            layout.addWidget(self.group_label)

            self.group_dropdown = QComboBox()
            self.group_dropdown.addItems([cat["name"] for cat in self.tag_categories])
            self.group_dropdown.currentIndexChanged.connect(self.validate_inputs)
            layout.addWidget(self.group_dropdown)

        elif self.current_source == "CrewChief":
            self.car_class_label = QLabel("Car Class (Optional):")
            layout.addWidget(self.car_class_label)

            self.car_class_dropdown = QComboBox()
            self.car_class_dropdown.addItems(["None"] + self.car_classes)
            layout.addWidget(self.car_class_dropdown)

            self.comment_label = QLabel("Comment (Optional):")
            layout.addWidget(self.comment_label)

            self.comment_input = QLineEdit()
            layout.addWidget(self.comment_input)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.save_button = button_box.button(QDialogButtonBox.Ok)
        self.save_button.setText("Save")
        self.save_button.setEnabled(False)  # Initially disabled
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_inputs(self):
        """Validate inputs in real-time and enable/disable the Save button."""
        iracing_id = self.id_input.text().strip()
        driver_name = self.name_input.text().strip()

        # Check if iRacing ID is numeric and 5-8 digits long
        is_valid_id = iracing_id.isdigit() and 5 <= len(iracing_id) <= 8
        is_unique_id = iracing_id not in self.existing_ids

        # Update the iRacing ID field's background color based on validity
        if not is_valid_id or not is_unique_id:
            self.id_input.setStyleSheet("background-color: #FFCCCC;")
        else:
            self.id_input.setStyleSheet("")

        # Enable Save button based on validity and current source
        if self.current_source == "iOverlay":
            group_selected = self.group_dropdown.currentIndex() != -1
            self.save_button.setEnabled(is_valid_id and is_unique_id and bool(driver_name) and group_selected)
        elif self.current_source == "CrewChief":
            self.save_button.setEnabled(is_valid_id and is_unique_id and bool(driver_name))

    def save_and_close(self):
        """Save the driver using the callback and close the dialog."""
        driver_data = self.get_driver()
        self.save_callback(driver_data)
        self.accept()

    def get_driver(self):
        """Retrieve driver data entered in the dialog."""
        iracing_id = self.id_input.text().strip()
        driver_name = self.name_input.text().strip()

        if self.current_source == "iOverlay":
            group = self.group_dropdown.currentText()
            return {"identifier": iracing_id, "name": driver_name, "group": group}

        elif self.current_source == "CrewChief":
            car_class = self.car_class_dropdown.currentText() if self.car_class_dropdown.currentIndex() > 0 else None
            comment = self.comment_input.text().strip() if self.comment_input.text().strip() else None
            return {"customer_id": iracing_id, "name": driver_name, "carClass": car_class, "comment": comment}

class GroupManagementDialog(QDialog):
    def __init__(self, parent, tag_categories, drivers_table, synchronizer):
        super().__init__(parent)
        self.tag_categories = tag_categories
        self.drivers_table = drivers_table
        self.synchronizer = synchronizer

        self.setWindowTitle("Manage Groups")
        self.setFixedSize(500, 450)

        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #e0f7ff, stop: 1 #ffffff
                );
                border-radius: 10px;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 6px;
                font-size: 14px;
                color: #333333;
            }
        """)

        # Initialize the selected color with a default value
        self.selected_color = "#000000"  # Default to black

        # Initialization flag
        self.initialized = False

        # Main layout
        layout = QHBoxLayout(self)

        # Left Panel: Group List
        self.group_list = QListWidget()
        self.group_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_list.customContextMenuRequested.connect(self.show_context_menu)
        self.group_list.setStyleSheet("""
            QListWidget {
                background-color: #f9f9f9;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #e6f7ff;
                border: 1px solid #007acc;
            }
            QListWidget::item:selected {
                background-color: #d0e8ff;
                border: 1px solid #4682b4;
                color: white;
            }
        """)
        self.group_list.itemClicked.connect(self.on_group_selected)
        self.refresh_group_list()
        layout.addWidget(self.group_list, 2)

        # Right Panel: Add/Delete Form
        form_layout = QVBoxLayout()

        # Add Group Section
        form_layout.addWidget(QLabel("Add Group"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter group name")
        form_layout.addWidget(self.name_input)

        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.pick_color)
        form_layout.addWidget(self.color_button)

        self.add_button = QPushButton("Add Group")
        self.add_button.clicked.connect(self.add_group)
        form_layout.addWidget(self.add_button)

        # Remove Group Section
        form_layout.addWidget(QLabel("Remove Group"))
        self.delete_dropdown = QComboBox()
        self.delete_dropdown.currentTextChanged.connect(self.refresh_reassign_dropdown)
        self.refresh_delete_dropdown()
        form_layout.addWidget(self.delete_dropdown)

        # Initialize reassign_dropdown
        self.reassign_dropdown = QComboBox()
        form_layout.addWidget(QLabel("Reassign drivers to:"))
        form_layout.addWidget(self.reassign_dropdown)

        self.delete_button = QPushButton("Delete Group")
        self.delete_button.clicked.connect(self.remove_group)
        form_layout.addWidget(self.delete_button)

        # Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        form_layout.addWidget(close_button)

        layout.addLayout(form_layout, 3)

        # Set initialized flag after all attributes are created
        self.initialized = True

        # Ensure this is called AFTER initializing reassign_dropdown
        self.refresh_reassign_dropdown()

    def refresh_group_list(self):
        """Refresh the list of groups displayed in the list widget."""
        self.group_list.clear()
        for category in self.tag_categories:
            item = QListWidgetItem(f"👥 {category['name']}")
            item.setForeground(QColor(category["color"]))
            self.group_list.addItem(item)

    def refresh_delete_dropdown(self):
        """Refresh the group dropdown for deletion."""
        self.delete_dropdown.clear()
        self.delete_dropdown.addItems([cat["name"] for cat in self.tag_categories])

    def refresh_reassign_dropdown(self):
        """Refresh the reassignment dropdown dynamically."""
        if not self.initialized:
            return  # Do not attempt to refresh if not fully initialized
        selected_group = self.delete_dropdown.currentText()
        self.reassign_dropdown.clear()
        self.reassign_dropdown.addItems(
            [cat["name"] for cat in self.tag_categories if cat["name"] != selected_group]
        )

    def show_context_menu(self, pos):
        index = self.drivers_table.indexAt(pos)
        if index.isValid():
            menu = QMenu(self)

            # Add actions
            add_driver_action = menu.addAction("Add Driver")
            add_driver_action.triggered.connect(self.add_driver_dialog)

            archive_action = menu.addAction("Archive Driver")
            archive_action.triggered.connect(lambda: self.archive_drivers([index.row()]))

            delete_action = menu.addAction("Delete Driver")
            delete_action.triggered.connect(lambda: self.delete_selected_drivers(from_context_menu=True, row_index=index.row()))

            reassign_action = menu.addAction("Reassign to Group")
            reassign_action.triggered.connect(lambda: self.mass_group_drivers(selected_rows=self.get_selected_rows()))

            menu.exec_(self.drivers_table.viewport().mapToGlobal(pos))


    def on_group_selected(self, item):
        """Update the remove group dropdown when a group is selected."""
        group_name = item.text().replace("👥 ", "").strip()
        self.delete_dropdown.setCurrentText(group_name)

    def pick_color(self):
        """Pick a color for a new group."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_button.setStyleSheet(f"background-color: {color.name()};")
            self.selected_color = color.name()

    def add_group(self):
        """Add a new group."""
        group_name = self.name_input.text().strip()
        if not group_name:
            QMessageBox.warning(self, "Error", "Group name cannot be empty.")
            return

        if any(cat["name"].lower() == group_name.lower() for cat in self.tag_categories):
            QMessageBox.warning(self, "Error", f"Group '{group_name}' already exists.")
            return

        new_group = {
            "id": max([cat["id"] for cat in self.tag_categories], default=0) + 1,
            "name": group_name,
            "color": self.selected_color
        }
        self.tag_categories.append(new_group)
        self.save_changes()
        self.refresh_group_list()
        self.refresh_delete_dropdown()
        self.refresh_reassign_dropdown()

        # Clear input fields
        self.name_input.clear()
        self.color_button.setStyleSheet("")  # Reset the color button style
        self.selected_color = "#000000"  # Reset to default black

        # Refresh editor/grid to reflect new group
        if hasattr(self.parent(), "refresh_grid"):
            self.parent().refresh_grid()

    def remove_group(self):
        """Remove a group with reassignment if necessary."""
        selected_group = self.delete_dropdown.currentText()
        reassign_to = self.reassign_dropdown.currentText()

        if not selected_group:
            QMessageBox.warning(self, "Error", "No group selected for deletion.")
            return

        # Check if this is the last group
        if len(self.tag_categories) == 1:
            # Load drivers from iOverlay settings file
            try:
                with open(self.synchronizer.ioverlay_path, "r") as file:
                    data = json.load(file)
                drivers = data.get("modules", {}).get("drivertagging", {}).get("drivertag", [])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load drivers from settings.dat: {e}")
                return

            if drivers:
                QMessageBox.warning(self, "Error", "Cannot delete the last group while there are drivers in iOverlay.")
                return

        # Reassign drivers in the selected group
        for row in range(self.drivers_table.rowCount()):
            group_widget = self.drivers_table.cellWidget(row, 3)
            if isinstance(group_widget, QComboBox) and group_widget.currentText() == selected_group:
                group_widget.setCurrentText(reassign_to)

        # Remove the group
        self.tag_categories = [cat for cat in self.tag_categories if cat["name"] != selected_group]
        self.save_changes()
        self.refresh_group_list()
        self.refresh_delete_dropdown()
        self.refresh_reassign_dropdown()

        # Refresh the grid in the editor
        if hasattr(self.parent(), "refresh_grid"):
            self.parent().refresh_grid()


    def save_changes(self):
        """Save group changes to the file."""
        try:
            with open(self.synchronizer.ioverlay_path, "r") as file:
                data = json.load(file)
            data["modules"]["drivertagging"]["tagcategory"] = self.tag_categories
            with open(self.synchronizer.ioverlay_path, "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save changes: {e}")


class QSwitchControl(QWidget):
    toggled = pyqtSignal(bool)  # Emits the state of the switch (True/False)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 25)
        self._checked = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.toggled.emit(self._checked)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background color: green for checked, blue for unchecked
        background_color = QColor("#2196F3") if self._checked else QColor("#4CAF50")  # Green and Blue
        painter.setBrush(QBrush(background_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        # Handle color
        handle_color = QColor("#ffffff")  # Always white for the handle
        handle_radius = self.height() - 4
        x_pos = self.width() - handle_radius - 2 if self._checked else 2
        painter.setBrush(QBrush(handle_color))
        painter.drawEllipse(x_pos, 2, handle_radius, handle_radius)

        painter.end()

class Editor(QWidget):
    def __init__(self, driversync):
        super().__init__()
        self.synchronizer = driversync  # Use the DriverSync instance
        self.current_source = "iOverlay"  # Default source
        self.is_crewchief = self.current_source == "CrewChief"  # Initialize based on the default source
        self.tag_categories = []  # Will be populated dynamically
        self.archived_drivers = {"iOverlay": [], "CrewChief": []}  # Separate archives for each source
        self.car_classes = []  # For CrewChief car classes dropdown
        self.init_ui()
        self.load_data()  # Load drivers and categories

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.is_first_load = True  # Track the first load state

        # Drivers Table
        self.drivers_table = QTableWidget(0, 5)
        self.update_drivers_table_headers()
        self.drivers_table.verticalHeader().setDefaultSectionSize(35)
        self.drivers_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.drivers_table.customContextMenuRequested.connect(self.show_context_menu)
   
        # Connect signals to detect grid changes
        self.drivers_table.itemChanged.connect(self.on_grid_modified)

        # Connect signals for iRacing ID validation
        self.drivers_table.cellChanged.connect(self.validate_iracing_id)

        layout.addWidget(self.drivers_table)

        # Add the blinking timer
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_save_button_blink)
        self.blink_state = False

        # Horizontal layout for refresh button and switch
        switch_layout = QHBoxLayout()

        # Refresh text button with Unicode
        refresh_label = QLabel("⟳")  # Unicode for refresh with "Refresh" text
        refresh_label.setToolTip("refresh grid")
        refresh_label.setAlignment(Qt.AlignCenter)
        refresh_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #FFFFFF;  /* White text for dark theme */
                background-color: #333333;  /* Dark gray background */
                border: 1px solid #555555;  /* Subtle border for definition */
                border-radius: 8px;
                padding: 5px 10px;  /* Padding for spacing */
            }
            QLabel:hover {
                background-color: #333333;  /* Slightly lighter background on hover */
                color: grey;
            }
        """)
        refresh_label.mousePressEvent = lambda event: self.refresh_grid()
        switch_layout.addWidget(refresh_label)

        # Add the QSwitchControl next to the refresh button
        switch_layout.addStretch()  # Push the switch to the right

        # Dynamic label for iOverlay / CrewChief with bold text
        self.source_label = QLabel("iOverlay")  # Default label text
        self.source_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Ensure vertical alignment
        self.source_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; padding-bottom: 2px;")  # Fine-tune positioning
        switch_layout.addWidget(self.source_label, alignment=Qt.AlignVCenter)  # Align with switch

        self.source_switch = QSwitchControl()
        self.source_switch.setObjectName("sourceSwitch")  # For external CSS styling
        self.source_switch.toggled.connect(self.on_switch_toggled)
        switch_layout.addWidget(self.source_switch, alignment=Qt.AlignVCenter)  # Align switch in center

        layout.addLayout(switch_layout)  # Add the switch layout below the grid

        # Filter Input
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter drivers or groups...")
        self.filter_input.textChanged.connect(self.filter_grid)  # Connect filter input to filtering function
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)

        # Action Buttons
        button_layout = QHBoxLayout()
        delete_button = self.create_action_button("❌ Delete")
        delete_button.clicked.connect(self.delete_selected_drivers)
        button_layout.addWidget(delete_button)

        archive_button = self.create_action_button("📥 Archive")
        archive_button.clicked.connect(self.archive_selected_drivers)
        button_layout.addWidget(archive_button)

        retrieve_button = self.create_action_button("🔄 Retrieve")
        retrieve_button.clicked.connect(self.retrieve_archived_drivers)
        button_layout.addWidget(retrieve_button)

        add_driver_button = self.create_action_button("➕ Add Driver")
        add_driver_button.clicked.connect(self.add_driver_dialog)  # Open Add Driver Dialog
        button_layout.addWidget(add_driver_button)


        self.mass_group_button = self.create_action_button("📂 Mass Group")
        self.mass_group_button.clicked.connect(lambda: self.mass_group_drivers())
        button_layout.addWidget(self.mass_group_button)


        self.add_group_button = self.create_action_button("👥 Manage Groups")
        self.add_group_button.clicked.connect(self.manage_groups)  # Call the unified dialog
        button_layout.addWidget(self.add_group_button)

        layout.addLayout(button_layout)

        # Save and Exit Buttons
        control_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("saveButton")  # For CSS
        self.save_button.clicked.connect(self.save_data)
        self.exit_button = QPushButton("Exit")
        self.exit_button.setObjectName("exitButton")  # For CSS
        self.exit_button.clicked.connect(self.close_editor)
        control_layout.addWidget(self.save_button)
        control_layout.addWidget(self.exit_button)
        layout.addLayout(control_layout)

        # Timer for blinking animation
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_save_button_blink)
        self.blink_timer.setInterval(2000)
        self.blink_state = False  # Track the current blink state
        self.changes_made = False  # Track whether unsaved changes exist
        self.has_unsaved_changes = False
        self.setLayout(layout)


    def on_grid_modified(self, item):
        """
        Re-enable the save button when a cell in the drivers table is modified.
        """
        if item:  # Ensure item is valid
            self.save_button.setEnabled(True)  # Re-enable save button
            self.start_save_button_blink()  # Trigger blinking as the grid has unsaved changes

    def on_data_changed(self, row, column):
        if column == 1:  # Validate iRacing ID only for column 1
            self.validate_iracing_id(row)
        self.start_save_button_blink()

        # Start save button blinking
        self.start_save_button_blink()

    def validate_iracing_id(self, row, column):
        """Validate the iRacing ID field in real-time."""
        if column == 1:  # Check only the iRacing ID column
            id_item = self.drivers_table.item(row, column)
            if not id_item:
                return

            id_text = id_item.text().strip()
            # Validate ID: Numeric and 5-8 digits long
            if not id_text.isdigit() or not (5 <= len(id_text) <= 8):
                id_item.setBackground(QColor("#FFCCCC"))  # Highlight invalid input in red
                id_item.setToolTip("iRacing ID must be numeric and 5-8 digits.")
                self.save_button.setEnabled(False)  # Disable save button if invalid
            else:
                id_item.setBackground(QColor("#FFFFFF"))  # Reset to default for valid input
                id_item.setToolTip("")
                self.check_all_ids_valid()

    def check_all_ids_valid(self):
        """
        Check if all iRacing IDs in the table are valid.
        """
        for row in range(self.drivers_table.rowCount()):
            id_item = self.drivers_table.item(row, 1)
            if not id_item or not id_item.text().isdigit() or not (5 <= len(id_item.text()) <= 8):
                self.save_button.setEnabled(False)
                return
        self.save_button.setEnabled(True)

    def on_switch_toggled(self, checked):
        """
        Handle the QSwitchControl toggled event.
        Toggles the source between iOverlay and CrewChief and updates the label, buttons, and grid styling.
        """
        # Determine the new source and log the switch
        self.current_source = "CrewChief" if checked else "iOverlay"
        self.is_crewchief = checked
        self.source_label.setText(self.current_source)
        self.synchronizer.log(f"Switched to {self.current_source}", "info", to_gui=False)

        # Update tab style based on the new source
        self.update_tab_style(self.current_source)

        # Adjust visibility of buttons based on the current source
        self.mass_group_button.setVisible(not self.is_crewchief)
        self.add_group_button.setVisible(not self.is_crewchief)

        # Debugging: Log the visibility states
        self.synchronizer.log(
            f"Mass group button visible: {not self.is_crewchief}, "
            f"Add group button visible: {not self.is_crewchief}",
            "debug"
        )

        # Refresh the grid to reflect the changes
        try:
            self.refresh_grid()
            self.synchronizer.log(f"Grid refreshed successfully for {self.current_source}", "success", to_gui=False)
        except Exception as e:
            self.synchronizer.log(f"Error refreshing grid for {self.current_source}: {e}", "error", to_gui=False)

    def set_tab_widget(self, tab_widget):
        """Set the parent tab widget and handle tab-specific logic."""
        self.tab_widget = tab_widget
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """
        Handle logic when the tab changes. Always reset to 'iOverlay' mode when the Editor tab is selected.
        """
        current_tab_text = self.tab_widget.tabText(index)

        if current_tab_text == "Editor":
            # Ensure the Editor tab always resets to 'iOverlay' mode
            if self.current_source != "iOverlay":
                self.current_source = "iOverlay"
                self.is_crewchief = False
                self.source_label.setText(self.current_source)

                # Reset the switcher to 'iOverlay'
                if self.source_switch._checked:
                    self.source_switch._checked = False
                    self.source_switch.update()

                # Refresh the grid to load 'iOverlay' data
                self.refresh_grid()

            if self.is_first_load:
                self.is_first_load = False
                self.save_button.setEnabled(False)  # Disable save button on the first load
                self.stop_save_button_blink()  # Ensure no blinking
            else:
                # Reset blinking and ensure save button reflects changes
                self.stop_save_button_blink()
        else:
            # Stop blinking and reset styles for other tabs
            self.stop_save_button_blink()

    def update_tab_style(self, mode):
        """
        Dynamically update the CSS style of the active tab based on the mode.
        """
        tab_bar = self.tab_widget.tabBar()
        for index in range(self.tab_widget.count()):
            if self.tab_widget.tabText(index) == "Editor":
                # Apply the specific style to the Editor tab based on the mode
                if mode == "iOverlay":
                    tab_bar.setTabTextColor(index, QColor("white"))
                    tab_bar.setTabText(index, "Editor")
                    tab_bar.setStyleSheet("QTabBar::tab:selected { background: green; color: white; }")
                elif mode == "CrewChief":
                    tab_bar.setTabTextColor(index, QColor("white"))
                    tab_bar.setTabText(index, "Editor")
                    tab_bar.setStyleSheet("QTabBar::tab:selected { background: blue; color: white; }")
            else:
                # Reset the style for non-Editor tabs
                tab_bar.setTabTextColor(index, QColor("black"))
                tab_bar.setTabText(index, self.tab_widget.tabText(index))
                tab_bar.setStyleSheet("")


    def create_action_button(self, text):
        """Create an action button with a gradient styling for dark theme."""
        button = QPushButton(text)
        button.setObjectName("actionButton")  # For further customization
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c2c2c,  /* Dark Gray */
                    stop:1 #3e3e3e   /* Slightly Lighter Gray */
                );
                color: #ffffff;
                border: 2px solid #5a5a5a;  /* Medium Gray Border */
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3e3e3e,  /* Lighter Gray */
                    stop:1 #555555   /* Medium Gray */
                );
                border: 2px solid #777777;  /* Lighter Gray Border */
            }
            QPushButton:pressed {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e1e1e,  /* Darker Gray */
                    stop:1 #333333   /* Slightly Darker Gray */
                );
                border: 2px solid #999999;  /* Highlighted Border */
            }
        """)
        return button

    def toggle_source(self):
        """Toggle between iOverlay and CrewChief."""
        if self.source_toggle.isChecked():
            self.current_source = "CrewChief"
            self.source_toggle.setText("CrewChief")
        else:
            self.current_source = "iOverlay"
            self.source_toggle.setText("iOverlay")
        self.refresh_grid()

    def update_drivers_table_headers(self):
        """
        Set headers for the drivers table dynamically based on the current source.
        """
        if self.current_source == "iOverlay":
            # iOverlay-specific headers
            self.drivers_table.setHorizontalHeaderLabels(["Select", "iRacing ID", "Driver Name", "Group", "Color"])
            # Set column widths
            self.drivers_table.setColumnWidth(0, 50)  # Select
            self.drivers_table.setColumnWidth(1, 100)  # iRacing ID (max 8 digits)
            self.drivers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Driver Name
            self.drivers_table.setColumnWidth(3, 150)  # Group
            self.drivers_table.setColumnWidth(4, 50)  # Color

        elif self.current_source == "CrewChief":
            # CrewChief-specific headers
            self.drivers_table.setHorizontalHeaderLabels(["Select", "iRacing ID", "Driver Name", "Car Class", "Comment"])
            # Set column widths
            self.drivers_table.setColumnWidth(0, 50)  # Select
            self.drivers_table.setColumnWidth(1, 100)  # Customer ID
            self.drivers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Driver Name
            self.drivers_table.setColumnWidth(3, 200)  # Car Class
            self.drivers_table.setColumnWidth(4, 200)  # Comment

    def load_data(self):
        """Load data into the drivers table based on the current source."""
        self.drivers_table.clearContents()
        self.drivers_table.setRowCount(0)

        try:
            if self.current_source == "iOverlay":
                # Load iOverlay data
                data = self.synchronizer.load_driver_data(self.synchronizer.ioverlay_path)
                self.tag_categories = data.get("modules", {}).get("drivertagging", {}).get("tagcategory", [])
                drivers = data.get("modules", {}).get("drivertagging", {}).get("drivertag", [])
                for driver in drivers:
                    self.add_driver_row(driver, is_ioverlay=True)

            elif self.current_source == "CrewChief":
                # Load CrewChief data
                data = self.synchronizer.load_driver_data(self.synchronizer.crewchief_path)

                # Dynamically load car classes
                try:
                    self.car_classes = self.load_car_classes()
                except Exception as e:
                    self.synchronizer.log(f"Error loading car classes: {e}", to_gui=True)
                    QMessageBox.warning(self, "Error", f"Failed to load car classes: {e}")
                    self.car_classes = []  # Default to empty list

                # Add drivers to the table
                for driver in data:
                    self.add_driver_row(driver, is_ioverlay=False)

            # Load archived drivers
            self.load_archived_drivers()

        except Exception as e:
            self.synchronizer.log(f"Error loading data: {e}", to_gui=False)
            QMessageBox.warning(self, "Error", f"Failed to load data: {e}")

    def load_archived_drivers(self):
        """Load archived drivers from _archive.json."""
        try:
            with open("_archive.json", "r") as file:
                loaded_archives = json.load(file)
                self.archived_drivers = {
                    "iOverlay": loaded_archives.get("iOverlay", []),
                    "CrewChief": loaded_archives.get("CrewChief", [])
                }
                self.synchronizer.log(f"Loaded archived drivers: {self.archived_drivers}", to_gui=False)
        except FileNotFoundError:
            self.synchronizer.log(f"No archived drivers found. Starting with an empty archive.", to_gui=False)
            self.archived_drivers = {"iOverlay": [], "CrewChief": []}

    def save_archived_drivers(self):
        """Save the archived drivers to _archive.json."""
        try:
            with open("_archive.json", "w") as file:
                json.dump(self.archived_drivers, file, indent=4)
            self.synchronizer.log(f"Archived drivers saved successfully.", to_gui=False)
        except Exception as e:
            self.synchronizer.log(f"Error saving archived drivers: {e}", to_gui=True)

    def archive_drivers(self, rows):
        """Archive specified rows of drivers based on the current source."""
        for row in reversed(rows):
            self.synchronizer.log(f"Processing row {row} for {self.current_source}...", to_gui=False)

            # Column 1: ID (iRacing ID or Customer ID)
            id_item = self.drivers_table.item(row, 1)
            if not id_item or not id_item.text():
                self.synchronizer.log(f"Row {row}: Missing ID.", to_gui=False)
                continue
            driver_id = id_item.text()

            # Column 2: Driver Name
            name_item = self.drivers_table.item(row, 2)
            if not name_item or not name_item.text():
                self.synchronizer.log(f"Row {row}: Missing Driver Name.", to_gui=False)
                continue
            driver_name = name_item.text()

            if self.current_source == "iOverlay":
                group_widget = self.drivers_table.cellWidget(row, 3)
                if not group_widget or not isinstance(group_widget, QComboBox):
                    self.synchronizer.log(f"Row {row}: Missing or invalid Group Dropdown.", to_gui=False)
                    continue
                group_dropdown = group_widget
                selected_group = group_dropdown.currentText()
                tag_id = next((cat["id"] for cat in self.tag_categories if cat["name"] == selected_group), None)

                if tag_id is None:
                    self.synchronizer.log(f"Row {row}: Invalid group '{selected_group}'.", to_gui=False)
                    continue

                self.archived_drivers["iOverlay"].append({
                    "id": int(row + 1),
                    "identifier": driver_id,
                    "name": driver_name,
                    "tagId": tag_id
                })

            elif self.current_source == "CrewChief":
                car_class_widget = self.drivers_table.cellWidget(row, 3)
                if not car_class_widget or not isinstance(car_class_widget, QComboBox):
                    self.synchronizer.log(f"Row {row}: Missing or invalid Car Class Dropdown.", to_gui=False)
                    continue
                car_class_dropdown = car_class_widget
                car_class = car_class_dropdown.currentText()

                comment_item = self.drivers_table.item(row, 4)
                comment = comment_item.text() if comment_item else ""

                self.archived_drivers["CrewChief"].append({
                    "customer_id": driver_id,
                    "name": driver_name,
                    "carClass": car_class,
                    "comment": comment
                })

            self.drivers_table.removeRow(row)

        # Save the updated archive
        with open("_archive.json", "w") as file:
            json.dump(self.archived_drivers, file, indent=4)
        self.synchronizer.log(f"Archived drivers updated: {self.archived_drivers}", to_gui=False)

    def add_driver_row(self, driver, is_ioverlay=True):
        row = self.drivers_table.rowCount()
        self.drivers_table.insertRow(row)

        # Add checkbox for selection in column 0
        checkbox = QCheckBox()
        checkbox.setStyleSheet("margin-left: 15px; margin-right:15px;")
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.drivers_table.setCellWidget(row, 0, checkbox_widget)

        # Extract iRacing ID
        id_item = QTableWidgetItem(driver.get("identifier", "Unknown") if is_ioverlay else str(driver.get("customer_id", "Unknown")))
        id_item.setTextAlignment(Qt.AlignCenter)

        # Validate iRacing ID (5-8 digits)
        if not id_item.text().isdigit() or not (5 <= len(id_item.text()) <= 8):
            id_item.setBackground(QColor("#FFCCCC"))  # Light red background for invalid ID
            id_item.setToolTip("iRacing ID must be numeric and between 5 and 8 digits.")
            self.save_button.setEnabled(False)  # Disable Save button
        else:
            id_item.setBackground(QColor("#FFFFFF"))  # Reset background for valid ID
            id_item.setToolTip("")

        self.drivers_table.setItem(row, 1, id_item)

        # Driver Name
        self.drivers_table.setItem(row, 2, QTableWidgetItem(driver.get("name", "Unknown")))

        if is_ioverlay:
            # iOverlay-specific fields
            tag_id = driver.get("tagId", None)
            group_info = next((cat for cat in self.tag_categories if cat["id"] == tag_id), {"name": "Unknown", "color": "#FFFFFF"})

            group_dropdown = QComboBox()
            group_dropdown.addItems([cat["name"] for cat in self.tag_categories])
            group_dropdown.setCurrentText(group_info["name"])
            # Connect both the save button blinking and the dropdown change handler
            group_dropdown.currentIndexChanged.connect(self.start_save_button_blink)  # For blinking save button
            group_dropdown.currentIndexChanged.connect(
                lambda index, row=row: self.group_dropdown_changed(row)  # For updating color buttons
            )

            self.drivers_table.setCellWidget(row, 3, group_dropdown)

            color_button = QPushButton()
            color_button.setFixedSize(25, 25)
            color_button.setStyleSheet(self.get_color_button_style(group_info["color"]))
            color_button.clicked.connect(lambda: self.select_color(group_info["name"], color_button))

            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.addWidget(color_button)
            button_layout.setAlignment(Qt.AlignCenter)
            button_layout.setContentsMargins(0, 0, 0, 0)
            self.drivers_table.setCellWidget(row, 4, button_container)
        else:
            # CrewChief-specific fields
            car_class_dropdown = QComboBox()
            car_class_dropdown.clear()
            car_class_dropdown.addItems(self.car_classes)
            car_class_dropdown.setCurrentText(driver.get("carClass", "Unknown"))
            car_class_dropdown.currentIndexChanged.connect(self.start_save_button_blink)  # Connect signal for blinking
            self.drivers_table.setCellWidget(row, 3, car_class_dropdown)

            comment_item = QTableWidgetItem(driver.get("comment", ""))
            comment_item.setToolTip(driver.get("comment", ""))
            self.drivers_table.setItem(row, 4, comment_item)

    def filter_grid(self):
        """
        Filter the drivers table based on the input in the filter box.
        Filters by Driver Name (Column 2) and Group/Car Class (Column 3).
        """
        filter_text = self.filter_input.text().strip().lower()

        for row in range(self.drivers_table.rowCount()):
            driver_name_match = False
            group_class_match = False

            # Check Driver Name (Column 2)
            driver_item = self.drivers_table.item(row, 2)
            if driver_item and filter_text in driver_item.text().strip().lower():
                driver_name_match = True

            # Check Group (Column 3) or Car Class
            group_class_widget = self.drivers_table.cellWidget(row, 3)
            if isinstance(group_class_widget, QComboBox):
                group_class_name = group_class_widget.currentText().strip().lower()
                if filter_text in group_class_name:
                    group_class_match = True

            # Show row if either match
            self.drivers_table.setRowHidden(row, not (driver_name_match or group_class_match))

    def select_color(self, group_name, color_button):
        """Allow the user to select a color and update the button and group colors."""
        color = QColorDialog.getColor()
        if color.isValid():
            new_color = color.name()
            color_button.setStyleSheet(self.get_color_button_style(new_color))
            self.update_color_buttons(group_name, new_color)
            self.start_save_button_blink()  # Trigger blinking after color change
            self.save_button.setEnabled(True)  # Enable the save button
            self.save_data()  # Automatically save changes after color update

    def get_color_button_style(self, color):
        """Generate a consistent style for color buttons."""
        return f"""
            QPushButton {{
                background-color: {color};
                border-radius: 12px;
                border: 1px solid #444;
                background-image: qradialgradient(
                    cx:0.5, cy:0.5, radius:1.0,
                    fx:0.5, fy:0.5,
                    stop:0 rgba(255, 255, 255, 150),
                    stop:1 {color}
                );
            }}
            QPushButton:hover {{
                border: 1px solid #222;
            }}
            QPushButton:pressed {{
                border: 1px solid #000;
            }}
        """

    def update_color_buttons(self, group_name, new_color):
        """Update the color buttons for all drivers in the specified group."""
        for row in range(self.drivers_table.rowCount()):
            group_widget = self.drivers_table.cellWidget(row, 3)
            if group_widget and isinstance(group_widget, QComboBox):
                group_dropdown = group_widget
                if group_dropdown.currentText() == group_name:
                    button_widget = self.drivers_table.cellWidget(row, 4)
                    if button_widget and button_widget.layout() and button_widget.layout().itemAt(0):
                        color_button = button_widget.layout().itemAt(0).widget()
                        color_button.setStyleSheet(self.get_color_button_style(new_color))
                        self.synchronizer.log(f"Updated color for row {row} to '{new_color}'", to_gui=False)

        for category in self.tag_categories:
            if category["name"] == group_name:
                category["color"] = new_color
                self.synchronizer.log(f"Updated color for group '{group_name}' to '{new_color}'.", to_gui=False)

        self.start_save_button_blink()  # Ensure blinking starts for any color change
        self.save_button.setEnabled(True)  # Enable the save button after changes

    def refresh_group_dropdowns(self):
        """Refresh group dropdowns and update color buttons with timing logic."""
        self.is_refreshing = True  # Flag to prevent blinking during this process
        QTimer.singleShot(0, self._refresh_group_dropdowns_internal)

    def _refresh_group_dropdowns_internal(self):
        try:
            for row in range(self.drivers_table.rowCount()):
                if self.current_source == "iOverlay":
                    # Handle iOverlay dropdowns
                    group_widget = self.drivers_table.cellWidget(row, 3)
                    if group_widget and isinstance(group_widget, QComboBox):
                        group_dropdown = group_widget
                        current_group = group_dropdown.currentText()
                        group_dropdown.blockSignals(True)  # Temporarily block signals
                        group_dropdown.clear()
                        group_dropdown.addItems([cat["name"] for cat in self.tag_categories])
                        if current_group in [cat["name"] for cat in self.tag_categories]:
                            group_dropdown.setCurrentText(current_group)
                        else:
                            group_dropdown.setCurrentIndex(0)
                        group_dropdown.blockSignals(False)  # Re-enable signals

                        # Update the color button for the group
                        button_widget = self.drivers_table.cellWidget(row, 4)
                        if button_widget and button_widget.layout() and button_widget.layout().itemAt(0):
                            color_button = button_widget.layout().itemAt(0).widget()
                            group_info = next(
                                (cat for cat in self.tag_categories if cat["name"] == current_group), 
                                {"color": "#FFFFFF"}
                            )
                            color_button.setStyleSheet(self.get_color_button_style(group_info["color"]))
                elif self.current_source == "CrewChief":
                    # Handle CrewChief dropdowns
                    car_class_widget = self.drivers_table.cellWidget(row, 3)
                    if car_class_widget and isinstance(car_class_widget, QComboBox):
                        car_class_dropdown = car_class_widget
                        current_car_class = car_class_dropdown.currentText()
                        car_class_dropdown.blockSignals(True)  # Temporarily block signals
                        car_class_dropdown.clear()
                        car_class_dropdown.addItems(self.car_classes)
                        car_class_dropdown.setCurrentText(current_car_class if current_car_class in self.car_classes else "Unknown")
                        car_class_dropdown.blockSignals(False)  # Re-enable signals
        except Exception as e:
            self.synchronizer.log(f"Error in refreshing group dropdowns: {e}", to_gui=False)
        finally:
            self.is_refreshing = False  # Reset the flag after the process

    def group_dropdown_changed(self, row):
        """Handle changes in the group dropdown and update the corresponding color button."""
        group_widget = self.drivers_table.cellWidget(row, 3)  # Column 3: Group Dropdown
        if group_widget and isinstance(group_widget, QComboBox):
            group_name = group_widget.currentText()
            group_info = next((cat for cat in self.tag_categories if cat["name"] == group_name), {"color": "#FFFFFF"})
            new_color = group_info["color"]

            button_widget = self.drivers_table.cellWidget(row, 4)  # Column 4: Color Button
            if button_widget and button_widget.layout() and button_widget.layout().itemAt(0):
                color_button = button_widget.layout().itemAt(0).widget()
                color_button.setStyleSheet(self.get_color_button_style(new_color))
                self.synchronizer.log(f"Row {row}: Updated to group '{group_name}' with color '{new_color}'.", to_gui=False)


    def delete_selected_drivers(self, from_context_menu=False, row_index=None):
        """
        Delete selected drivers from the drivers table.
        :param from_context_menu: If True, delete a specific row passed as `row_index`.
        :param row_index: The index of the row to delete, used when triggered from the context menu.
        """
        if from_context_menu and row_index is not None:
            # Delete a specific row when triggered from the context menu
            self.drivers_table.removeRow(row_index)
            self.synchronizer.log(f"Driver in row {row_index + 1} deleted from context menu.", to_gui=False)
        else:
            # Delete all selected rows based on checkboxes
            for row in reversed(range(self.drivers_table.rowCount())):
                checkbox_widget = self.drivers_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.layout().itemAt(0).widget()
                    if checkbox.isChecked():
                        self.drivers_table.removeRow(row)
                        self.synchronizer.log(f"Driver in row {row + 1} deleted.", to_gui=False)

        # Trigger blinking after deletion
        self.start_save_button_blink()

    def archive_selected_drivers(self):
        """Archive selected drivers based on the current source."""
        selected_rows = [
            row for row in range(self.drivers_table.rowCount())
            if self.drivers_table.cellWidget(row, 0).layout().itemAt(0).widget().isChecked()
        ]
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "No drivers selected for archiving.")
            return

        self.archive_drivers(selected_rows)


    def load_car_classes(self):
        """
        Load car classes from _internal/car_classes.json.
        """
        try:
            # Resolve the path to the car_classes.json file
            car_classes_path = self.get_internal_file_path("_car_classes.json")
        
            # Open and parse the JSON file
            with open(car_classes_path, "r", encoding="utf-8") as file:
                car_classes_data = json.load(file)
        
            # Parse the car classes into a structured list
            car_classes = []
            for category, classes in car_classes_data.items():
                car_classes.append(f"--- {category} ---")  # Add category as a separator
                car_classes.extend(classes)  # Add all car classes
        
            return car_classes
        except FileNotFoundError as e:
            self.synchronizer.log(f"Car classes file not found: {e}", to_gui=True)
            QMessageBox.warning(self, "Error", f"Car classes file not found: {e}")
            return []
        except json.JSONDecodeError as e:
            self.synchronizer.log(f"Error parsing car classes file: {e}", to_gui=True)
            QMessageBox.warning(self, "Error", f"Error parsing car classes file: {e}")
            return []
        except Exception as e:
            self.synchronizer.log(f"Unexpected error loading car classes: {e}", to_gui=True)
            QMessageBox.warning(self, "Error", f"Unexpected error loading car classes: {e}")
            return []

    def get_internal_file_path(self, relative_path):
        """
        Resolve the path to a file within the _internal directory.
        Works for PyInstaller bundles and during development.
        """
        try:
            # Resolve the base path for PyInstaller or regular script execution
            base_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(__file__).parent.resolve()
        
            # Construct the full path
            internal_path = base_path / relative_path
        
            # Check if the file exists
            if not internal_path.exists():
                raise FileNotFoundError(f"File not found: {internal_path}")
        
            return internal_path
        except Exception as e:
            raise FileNotFoundError(f"Error resolving path for {relative_path}: {e}")


    def retrieve_archived_drivers(self):
        """Retrieve archived drivers with enhanced UI."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Retrieve Drivers")
        dialog.resize(600, 400)

        # Main layout
        layout = QVBoxLayout(dialog)

        # Add a search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Type to filter drivers by name or ID...")
        search_bar.textChanged.connect(lambda: self.filter_driver_list(search_bar.text(), list_widget))
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_bar)
        layout.addLayout(search_layout)

        # Driver list (scrollable)
        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        for driver in self.archived_drivers[self.current_source]:
            label = f"{driver['name']} (ID: {driver.get('identifier', driver.get('customer_id'))})"
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.UserRole, driver)  # Store driver data in the item
            list_widget.addItem(list_item)
        layout.addWidget(list_widget)

        # Action buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Retrieve Selected Drivers")
        buttons.button(QDialogButtonBox.Cancel).setText("Close")
        buttons.accepted.connect(lambda: self.apply_retrieve(dialog, list_widget))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec_()

    def filter_driver_list(self, text, list_widget):
        """
        Filter the driver list based on the search input.
        """
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            driver = item.data(Qt.UserRole)
            label = f"{driver['name']} (ID: {driver.get('identifier', driver.get('customer_id'))})"
            item.setHidden(text.lower() not in label.lower())

    def apply_retrieve(self, dialog, list_widget):
        """
        Retrieve selected drivers from the archive.
        """
        dialog.accept()

        # Determine the next available unique ID
        existing_ids = [
            int(self.drivers_table.item(row, 1).text())
            for row in range(self.drivers_table.rowCount())
        ]
        next_id = max(existing_ids, default=0) + 1

        for item in list_widget.selectedItems():
            driver = item.data(Qt.UserRole)

            # Assign a new unique ID
            if self.current_source == "iOverlay":
                driver["id"] = next_id
            else:
                driver["customer_id"] = str(next_id)
            next_id += 1

            # Add the driver back to the table
            self.add_driver_row(driver, is_ioverlay=(self.current_source == "iOverlay"))

            # Remove the driver from the archive
            self.archived_drivers[self.current_source] = [
                archived_driver for archived_driver in self.archived_drivers[self.current_source]
                if archived_driver["identifier" if self.current_source == "iOverlay" else "customer_id"] !=
                   driver["identifier" if self.current_source == "iOverlay" else "customer_id"]
            ]

        # Save the updated archive
        self.save_archived_drivers()
        self.synchronizer.log(f"Retrieved selected drivers.", to_gui=False)

    def mass_group_drivers(self, selected_rows=None):
        """Apply a group to selected drivers."""
        if selected_rows is None:  # If no rows are passed, use checkboxes to determine selected rows
            selected_rows = self.get_selected_rows()

        if not selected_rows:
            QMessageBox.warning(self, "Error", "No drivers selected for grouping.")
            return

        # Show group selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Mass Group Drivers")
        dialog.setFixedSize(300, 150)
        layout = QVBoxLayout(dialog)

        label = QLabel("Select a group to assign:")
        layout.addWidget(label)

        group_dropdown = QComboBox()
        group_dropdown.addItems([cat["name"] for cat in self.tag_categories])
        layout.addWidget(group_dropdown)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.apply_mass_group(dialog, group_dropdown.currentText(), selected_rows))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.exec_()

    def apply_mass_group(self, dialog, selected_group, selected_rows):
        """Assign the selected group to specific rows."""
        for row in selected_rows:
            group_widget = self.drivers_table.cellWidget(row, 3)
            if group_widget and isinstance(group_widget, QComboBox):
                group_dropdown = group_widget
                group_dropdown.setCurrentText(selected_group)

                # Update the color button based on the new group
                group_info = next((cat for cat in self.tag_categories if cat["name"] == selected_group), None)
                if group_info:
                    button_widget = self.drivers_table.cellWidget(row, 4)
                    if button_widget and button_widget.layout() and button_widget.layout().itemAt(0):
                        color_button = button_widget.layout().itemAt(0).widget()
                        color_button.setStyleSheet(self.get_color_button_style(group_info["color"]))
                    else:
                        self.synchronizer.log(f"Row {row}: Missing Color Button.", to_gui=False)
                else:
                    self.synchronizer.log(f"Row {row}: Group '{selected_group}' not found.", to_gui=False)
            else:
                self.synchronizer.log(f"Row {row}: Missing Group Dropdown.", to_gui=False)

        dialog.accept()


    def get_selected_rows(self):
        """Retrieve rows with selected checkboxes."""
        selected_rows = []
        for row in range(self.drivers_table.rowCount()):
            checkbox_widget = self.drivers_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.layout().itemAt(0).widget()
                if checkbox.isChecked():
                    selected_rows.append(row)
        self.synchronizer.log(f"Selected rows: {selected_rows}", to_gui=False)
        return selected_rows

    def manage_groups(self):
        """Open the unified Group Management Dialog."""
        dialog = GroupManagementDialog(self, self.tag_categories, self.drivers_table, self.synchronizer)
        dialog.exec_()

    def show_context_menu(self, pos):
        index = self.drivers_table.indexAt(pos)
        if index.isValid():
            self.context_menu_selected_row = index.row()

            menu = QMenu(self)

            # Add actions
            add_driver_action = menu.addAction("Add Driver")
            add_driver_action.triggered.connect(self.add_driver_dialog)

            archive_action = menu.addAction("Archive Driver")
            archive_action.triggered.connect(lambda: self.archive_drivers([self.context_menu_selected_row]))

            delete_action = menu.addAction("Delete Driver")
            delete_action.triggered.connect(lambda: self.delete_selected_drivers(from_context_menu=True, row_index=self.context_menu_selected_row))

            reassign_action = menu.addAction("Reassign to Group")
            reassign_action.triggered.connect(lambda: self.mass_group_drivers(selected_rows=[self.context_menu_selected_row]))

            menu.exec_(self.drivers_table.viewport().mapToGlobal(pos))
        else:
            self.context_menu_selected_row = None

    def delete_driver(self, row):
        """Delete a driver from the table based on the specified row."""
        reply = QMessageBox.question(
            self,
            "Delete Driver",
            f"Are you sure you want to delete the driver in row {row + 1}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.drivers_table.removeRow(row)
            self.synchronizer.log(f"Driver at row {row + 1} deleted successfully.", to_gui=False)
            self.start_save_button_blink()  # Start blinking save button after deletion


    def get_toggle_style(self, is_checked):
        """Return the style for the toggle button based on its state."""
        if is_checked:
            return """
                QPushButton {
                    background-color: #00BFFF;  /* Light Blue for CrewChief */
                    color: white;
                    border: 2px solid #007ACC;
                    border-radius: 20px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #007ACC;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #FFA500;  /* Orange for iOverlay */
                    color: white;
                    border: 2px solid #FF8C00;
                    border-radius: 20px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #FF8C00;
                }
                """
    def save_data(self):
        """Save the drivers and categories to the correct data source."""
        try:
            # Validate IDs before proceeding
            invalid_ids = []
            for row in range(self.drivers_table.rowCount()):
                id_item = self.drivers_table.item(row, 1)
                if not id_item or not id_item.text().isdigit() or not (5 <= len(id_item.text()) <= 8):
                    invalid_ids.append(row)
                    id_item.setBackground(QColor("#FFCCCC"))  # Highlight invalid ID in red
                    id_item.setToolTip("iRacing ID must be numeric and between 5 and 8 digits.")
                else:
                    id_item.setBackground(QColor("#FFFFFF"))  # Reset valid IDs
                    id_item.setToolTip("")

            if invalid_ids:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"Invalid iRacing IDs found in rows: {', '.join(str(r + 1) for r in invalid_ids)}.\n"
                    "Please correct them before saving."
                )
                return

            # Determine file path based on current source
            file_path = self.synchronizer.ioverlay_path if self.current_source == "iOverlay" else self.synchronizer.crewchief_path

            with open(file_path, "r") as file:
                data = json.load(file)

            drivers = []
            for row in range(self.drivers_table.rowCount()):
                self.synchronizer.log(f"Processing row {row}...", to_gui=False)

                # Column 1: iRacing ID or Customer ID
                id_item = self.drivers_table.item(row, 1)
                driver_id = id_item.text()

                # Column 2: Driver Name
                name_item = self.drivers_table.item(row, 2)
                if not name_item:
                    self.synchronizer.log(f"Row {row}: Missing Driver Name.", to_gui=False)
                    raise ValueError(f"Row {row}: Missing Driver Name.")
                driver_name = name_item.data(Qt.UserRole) if name_item.data(Qt.UserRole) else name_item.text()

                if self.current_source == "iOverlay":
                    # Column 3: Group Dropdown
                    group_widget = self.drivers_table.cellWidget(row, 3)
                    if not group_widget or not isinstance(group_widget, QComboBox):
                        self.synchronizer.log(f"Row {row}: Missing or invalid Group Dropdown.", to_gui=False)
                        raise ValueError(f"Row {row}: Missing or invalid Group Dropdown.")

                    group_dropdown = group_widget
                    selected_group = group_dropdown.currentText()
                    tag_id = next((cat["id"] for cat in self.tag_categories if cat["name"] == selected_group), None)
                    if tag_id is None:
                        self.synchronizer.log(f"Row {row}: Invalid group '{selected_group}'.", to_gui=False)
                        raise ValueError(f"Row {row}: Tag ID not found for group '{selected_group}'.")

                    drivers.append({
                        "id": int(driver_id),
                        "identifier": driver_id,
                        "name": driver_name,  # Save the original name
                        "tagId": tag_id
                    })

                elif self.current_source == "CrewChief":
                    # Column 3: Car Class Dropdown
                    car_class_widget = self.drivers_table.cellWidget(row, 3)
                    if not car_class_widget or not isinstance(car_class_widget, QComboBox):
                        self.synchronizer.log(f"Row {row}: Missing or invalid Car Class Dropdown.", to_gui=False)
                        raise ValueError(f"Row {row}: Missing or invalid Car Class Dropdown.")
                    car_class_dropdown = car_class_widget
                    car_class = car_class_dropdown.currentText()

                    # Column 4: Comment
                    comment_item = self.drivers_table.item(row, 4)
                    comment = comment_item.text() if comment_item and comment_item.text() else ""

                    drivers.append({
                        "customer_id": driver_id,
                        "name": driver_name,  # Save the original name
                        "carClass": car_class,
                        "comment": comment
                    })

            # Ensure IDs are sequential for iOverlay
            if self.current_source == "iOverlay":
                drivers.sort(key=lambda x: x["id"])
                for index, driver in enumerate(drivers):
                    driver["id"] = index + 1

            # Update the file
            if self.current_source == "iOverlay":
                data["modules"]["drivertagging"]["drivertag"] = drivers
                data["modules"]["drivertagging"]["tagcategory"] = self.tag_categories
            else:
                data = drivers

            # Write back the updated data to the file
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)

            # Stop blinking and reset Save button style
            self.blink_timer.stop()
            self.save_button.setStyleSheet("")  # Reset to default style
            self.save_button.setEnabled(False)  # Disable save button after saving

            self.synchronizer.log("Data saved successfully.", to_gui=False)

        except Exception as e:
            self.synchronizer.log(f"Error saving data: {e}", to_gui=False)
            QMessageBox.warning(self, "Error", f"Failed to save data: {e}")

    def toggle_source(self):
        """Toggle between iOverlay and CrewChief."""
        if self.source_toggle.isChecked():
            self.current_source = "CrewChief"
            self.source_toggle.setText("CrewChief")
            self.source_toggle.setStyleSheet(self.get_toggle_style(True))
        else:
            self.current_source = "iOverlay"
            self.source_toggle.setText("iOverlay")
            self.source_toggle.setStyleSheet(self.get_toggle_style(False))

        self.refresh_grid()  # Reload data
        self.update_drivers_table_headers()  # Update headers dynamically

    def start_save_button_blink(self):
        """Start blinking the save button to indicate unsaved changes."""
        if self.is_first_load or getattr(self, 'is_refreshing', False):
            return  # Do not blink if it's the first load or during refresh

        # Enable the save button
        self.save_button.setEnabled(True)

        # Ensure the timer exists and is active
        if not hasattr(self, 'blink_timer'):
            return
        if not self.blink_timer.isActive():
            self.blink_timer.start(1000)



    def stop_save_button_blink(self):
        """Stop blinking the save button and reset its style."""
        if hasattr(self, 'blink_timer') and self.blink_timer.isActive():
            self.blink_timer.stop()
        self.save_button.setStyleSheet("")  # Reset the button style

    def toggle_save_button_blink(self):
        """Toggle the save button style for blinking effect."""
        if self.blink_state:
            self.save_button.setStyleSheet("")  # Reset to default style
        else:
            self.save_button.setStyleSheet("background-color: green;")  # Subtle blinking color
        self.blink_state = not self.blink_state

    def add_driver_dialog(self):
        """Open a dialog to add a new driver and refresh the grid afterward."""
        existing_ids = [
            self.drivers_table.item(row, 1).text().strip()
            for row in range(self.drivers_table.rowCount())
            if self.drivers_table.item(row, 1)
        ]

        def save_callback(driver_data):
            """Save the driver to the table and initiate a save."""
            self.add_driver_row(driver_data, is_ioverlay=(self.current_source == "iOverlay"))
            self.save_data()  # Automatically save after adding a driver
            self.refresh_grid()  # Refresh the grid to reflect new data
            self.start_save_button_blink()  # Indicate action completion visually

        # Initialize the dialog and pass the save callback
        dialog = AddDriverDialog(
            self,
            self.current_source,
            self.tag_categories,
            self.car_classes,
            existing_ids,
            save_callback  # Provide callback to handle saving logic
        )
        dialog.exec_()

    def delayed_refresh(self):
        """Delayed grid refresh."""
        self.refresh_group_dropdowns()  # Ensure dropdowns and colors are refreshed
        self.refresh_grid()  # Reload grid data to ensure consistency

    def add_driver_to_table(self, driver_data):
        """Add the new driver to the table and refresh the grid."""
        is_ioverlay = self.current_source == "iOverlay"
        self.add_driver_row(driver_data, is_ioverlay=is_ioverlay)

        # Update color buttons if in iOverlay mode
        if is_ioverlay:
            self.refresh_group_dropdowns()

    def lookup_driver(self, row_index):
        """
        Fetch and display driver details for the selected row.
        """
        id_item = self.drivers_table.item(row_index, 1)
        if not id_item or not id_item.text().strip().isdigit():
            QMessageBox.warning(self, "Error", "Invalid iRacing ID.")
            return

        iracing_id = id_item.text().strip()

        try:
            # Fetch driver data
            driver_data = fetch_driver_data(iracing_id)

            # Show the data in a dialog
            self.show_driver_data_dialog(driver_data)

        except ValueError as e:
            QMessageBox.warning(self, "Lookup Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def show_driver_data_dialog(self, driver_data):
        """
        Display driver data in a dialog.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Driver: {driver_data['name']}")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        # Name
        layout.addWidget(QLabel(f"Name: {driver_data['name']}"))

        # iRatings
        layout.addWidget(QLabel("iRatings:"))
        iratings = "\n".join(f"{category}: {rating}" for category, rating in driver_data['iratings'].items())
        layout.addWidget(QLabel(iratings))

        # Statistics
        layout.addWidget(QLabel("Statistics:"))
        stats = "\n\n".join(f"{category}:\n{details}" for category, details in driver_data['stats'].items())
        stats_browser = QTextBrowser()
        stats_browser.setPlainText(stats)
        layout.addWidget(stats_browser)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec_()

    def update_color_buttons_for_all_rows(self):
        """Ensure all color buttons in the grid reflect the correct group colors."""
        for row in range(self.drivers_table.rowCount()):
            group_widget = self.drivers_table.cellWidget(row, 3)
            if group_widget and isinstance(group_widget, QComboBox):
                group_name = group_widget.currentText()
                group_info = next((cat for cat in self.tag_categories if cat["name"] == group_name), {"color": "#FFFFFF"})
                color = group_info["color"]

                button_widget = self.drivers_table.cellWidget(row, 4)
                if button_widget and button_widget.layout() and button_widget.layout().itemAt(0):
                    color_button = button_widget.layout().itemAt(0).widget()
                    color_button.setStyleSheet(self.get_color_button_style(color))

    def refresh_grid(self):
        """Refresh the editor grid by reloading data and updating headers."""
        try:
            self.is_refreshing = True  # Flag to indicate grid refresh is in progress

            self.drivers_table.blockSignals(True)  # Temporarily block signals to avoid unintended triggers
            self.load_data()  # Reload the drivers and categories
            self.update_drivers_table_headers()  # Ensure correct headers
            self.refresh_group_dropdowns()  # Ensure dropdowns are current
            self.update_color_buttons_for_all_rows()  # Update color buttons

            self.drivers_table.viewport().update()  # Force UI repaint
            self.drivers_table.repaint()
            self.drivers_table.blockSignals(False)  # Re-enable signals after changes

            self.synchronizer.log(f"Editor grid refreshed successfully for source: {self.current_source}", to_gui=False)
        except Exception as e:
            self.drivers_table.blockSignals(False)  # Ensure signals are re-enabled in case of error
            self.synchronizer.log(f"Error refreshing the editor grid: {e}", to_gui=False)
            QMessageBox.warning(self, "Error", f"Failed to refresh the editor grid: {e}")
        finally:
            self.is_refreshing = False  # Reset the flag after refresh

    def on_grid_modified(self, item):
        """
        Re-enable the save button when a cell in the drivers table is modified.
        """
        if item and not getattr(self, "is_refreshing", False):  # Prevent blinking during grid refresh
            self.start_save_button_blink()  # Trigger blinking as the grid has unsaved changes


    def close_editor(self):
        """Close the editor."""
        QApplication.quit()