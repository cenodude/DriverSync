import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QSlider,
    QFormLayout, QHBoxLayout, QMessageBox, QGridLayout, QTextEdit, QInputDialog, QWidget, QSizePolicy, QLineEdit, QFrame, QStackedLayout
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QBrush
from _logging import log_to_gui

# Utility Functions
def load_json_file(file_path):
    """
    Load a JSON file and return its contents.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        log_to_gui(f"File not found: {file_path}", "error")
        raise
    except json.JSONDecodeError as e:
        log_to_gui(f"JSON parsing error in {file_path}: {e}", "error")
        raise
    except Exception as e:
        log_to_gui(f"Error loading JSON file {file_path}: {e}", "error")
        raise


def save_json_file(file_path, data):
    """
    Save a dictionary to a JSON file.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        log_to_gui(f"Saved JSON file: {file_path}", "info")
    except Exception as e:
        log_to_gui(f"Error saving JSON file {file_path}: {e}", "error")
        raise


def load_default_settings(path):
    """
    Load and parse the default settings file.
    """
    settings = {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                if ":" in line and not line.strip().startswith("#"):
                    try:
                        key, value = line.split(":", 1)
                        key = key.strip().strip('"')
                        value = json.loads(value.strip().rstrip(","))
                        settings[key] = value
                    except json.JSONDecodeError:
                        continue
        return settings
    except FileNotFoundError:
        log_to_gui(f"Settings file not found: {path}", "error")
        raise
    except Exception as e:
        log_to_gui(f"Error loading default settings: {e}", "error")
        raise

def save_default_settings(path, data, user_settings):
    """
    Update specific keys in defaultSettings.json while preserving its original formatting,
    including comments, indentation, and alignment.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        updated_lines = []
        for line in lines:
            stripped_line = line.strip()

            if ":" in stripped_line and not stripped_line.startswith("#"):
                # Extract the key and determine if it needs to be updated
                key = stripped_line.split(":", 1)[0].strip().strip('"')
                if key in data:
                    # Preserve indentation and trailing characters (e.g., comma)
                    indent = line[:len(line) - len(line.lstrip())]
                    trailing_comma = "," if stripped_line.endswith(",") else ""
                    new_value = json.dumps(data[key])  # Serialize the new value
                    updated_lines.append(f'{indent}"{key}": {new_value}{trailing_comma}\n')
                else:
                    updated_lines.append(line)
            else:
                # Keep comments and unrelated lines as-is
                updated_lines.append(line)

        # Write back the updated content
        with open(path, "w", encoding="utf-8") as file:
            file.writelines(updated_lines)

    except Exception as e:
        log_to_gui(f"Error saving default settings: {e}", "error")
        raise


    except Exception as e:
        log_to_gui(f"Error saving default settings: {e}", "error")
        raise

class QSwitchControl(QWidget):
    toggled = pyqtSignal(bool)  # Emits the state of the switch (True/False)

    def __init__(self, parent=None, initial_state=False, label=None):
        """
        Initialize the switch with an optional external label for displaying "Off" and "On".
        """
        super().__init__(parent)
        self.setFixedSize(50, 25)
        self._checked = initial_state  # Initialize with the given state
        self.label = label  # QLabel instance for displaying "Off"/"On"

        self.update_label()  # Set the initial label text
        self.update()  # Ensure the switch reflects the initial state

    def setChecked(self, state):
        """
        Set the switch to the given state (checked or unchecked).
        """
        self._checked = state
        self.toggled.emit(self._checked)  # Emit signal when state is set programmatically
        self.update_label()  # Update the label
        self.update()  # Redraw the switch

    def isChecked(self):
        """
        Get the current state of the switch.
        """
        return self._checked

    def mousePressEvent(self, event):
        """
        Handle mouse click events to toggle the switch.
        """
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked  # Toggle the state
            self.toggled.emit(self._checked)  # Emit the new state
            self.update_label()  # Update the label
            self.update()  # Redraw the switch

    def paintEvent(self, event):
        """
        Paint the switch with its current state (checked or unchecked).
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background color: green for on, red for off
        background_color = QColor("#4CAF50") if self._checked else QColor("#F44336")
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

    def update_label(self):
        """
        Update the external label text if it exists.
        """
        if self.label:
            self.label.setText("On" if self._checked else "Off")

class ClubReputationsPopup(QDialog):
    def __init__(self, settings_path, reputations_file_path, parent=None):
        super().__init__(parent)
        self.settings_path = settings_path
        self.reputations_file = reputations_file_path  # Use the provided path
        self.reputations_data = self.load_reputations_file()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI for the popup with a light blueish gradient effect."""
        self.setWindowTitle("Manage and Edit Club Reputations")
        self.resize(900, 600)

        # Apply the light theme with a gradient effect
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

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("🏁 Manage and Edit Club Reputations")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #007BFF;
            }
        """)
        self.main_layout.addWidget(header_label)

        # Explanation
        explanation_label = QLabel(
            "Select clubs for each category below to mark them as 'Sketchy.' You can specify this per race category "
            "(e.g., Road, Oval, Dirt Road, etc.).\n\n"
            "Switch to 'Edit' mode to modify the categories or clubs."
        )

        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("font-size: 14px; color: #666666;")
        self.main_layout.addWidget(explanation_label)

        self.stacked_layout = QStackedLayout()
        self.main_section = QWidget()
        self.edit_section = QWidget()

        # Set up sections
        self.setup_main_section()
        self.setup_edit_section()

        # Add sections to the stacked layout
        self.stacked_layout.addWidget(self.main_section)
        self.stacked_layout.addWidget(self.edit_section)
        self.main_layout.addLayout(self.stacked_layout)

        # Populate the main section on initialization
        self.refresh_clubs_data()

        # Initially show the main section
        self.stacked_layout.setCurrentWidget(self.main_section)

    def get_reputations_file_path(self):
        """
        Dynamically resolve the path to _reputations.json.
        """
        try:
            if hasattr(sys, '_MEIPASS'):  # PyInstaller temp extraction directory
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(__file__).parent.resolve()

            reputations_file = base_path / "_reputations.json"

            # Check if the file exists
            if not reputations_file.exists():
                raise FileNotFoundError(f"Reputations file not found at: {reputations_file}")

            return reputations_file
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to locate _reputations.json: {e}")
            raise

    def load_reputations_file(self):
        """
        Load the reputations data from _reputations.json.
        """
        try:
            with open(self.reputations_file, "r", encoding="utf-8") as file:
                content = json.load(file)
                if "clubs" not in content or not isinstance(content["clubs"], dict):
                    raise ValueError("The file does not contain a valid 'clubs' key.")
                return content
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error loading _reputations.json: {e}")
            return {"clubs": {}}  # Return default structure


    def load_reputations_file(self):
        """Load the reputations data from _reputations.json."""
        try:
            # Open and load the file
            with open(self.reputations_file, "r", encoding="utf-8") as file:
                content = json.load(file)

                # Validate the file structure
                if "clubs" not in content or not isinstance(content["clubs"], dict):
                    raise ValueError("The file does not contain a valid 'clubs' key.")

                return content

        except FileNotFoundError:
            # File not found: Warn and create a default structure
            QMessageBox.warning(
                self,
                "File Not Found",
                "The reputations file was not found. A new file will be created."
            )
            return {"clubs": {}}  # Default structure

        except json.JSONDecodeError as e:
            # JSON decoding error: Show the error and use a default structure
            QMessageBox.critical(
                self,
                "Error",
                f"JSON decoding error:\n{e.msg}\nLine {e.lineno}, Column {e.colno}"
            )
            return {"clubs": {}}  # Default structure

        except Exception as e:
            # General error: Show the error and use a default structure
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load reputations file: {e}"
            )
            return {"clubs": {}}  # Default structure


    def save_reputations_file(self):
        """Save the updated reputations data to _reputations.json."""
        try:
            with open(self.reputations_file, "w", encoding="utf-8") as file:
                json.dump(self.reputations_data, file, indent=4)
            QMessageBox.information(self, "Success", "Reputations saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save reputations file: {e}")

    def show_edit_section(self):
        """
        Show the edit section and populate categories and clubs for editing.
        """
        # Populate the categories list
        self.load_categories()

        # Clear the clubs list as no category is initially selected
        self.clubs_list.clear()

        # Switch to the edit section in the stacked layout
        self.stacked_layout.setCurrentWidget(self.edit_section)


    def setup_main_section(self):
        """Setup the main section for viewing clubs."""
        layout = QVBoxLayout(self.main_section)

        # Category Listboxes
        self.category_widgets = {}
        grid_layout = QGridLayout()
        categories = ["Road", "Oval", "Dirt Road", "Dirt Oval"]

        for col, category in enumerate(categories):
            # Add category headers
            category_header = QLabel(category)
            category_header.setAlignment(Qt.AlignCenter)
            category_header.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #007BFF;
                }
            """)
            grid_layout.addWidget(category_header, 0, col)

            # Create and style category list widgets
            list_widget = QListWidget()
            list_widget.setSelectionMode(QListWidget.MultiSelection)

            # Add emoji-compatible font and styling
            list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    font-size: 14px;  /* Ensure font is large enough for emojis */
                    font-family: "Segoe UI Emoji";  /* A font known to support emojis */
                    color: #333333;
                }
            """)
        
            self.category_widgets[category] = list_widget
            grid_layout.addWidget(list_widget, 1, col)

        layout.addLayout(grid_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        edit_button = QPushButton("✏️ Edit Mode")
        edit_button.clicked.connect(self.show_edit_section)
        buttons_layout.addWidget(edit_button)

        save_button = QPushButton("💾 Save")
        save_button.clicked.connect(self.save_clubs)
        buttons_layout.addWidget(save_button)

        close_button = QPushButton("❌ Close")
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)

    def setup_edit_section(self):
        """Setup the edit section for modifying categories and clubs."""
        layout = QVBoxLayout(self.edit_section)

        # Categories and Clubs Layout
        editor_layout = QHBoxLayout()

        # Main Categories List
        self.categories_list = QListWidget()
        self.categories_list.itemClicked.connect(self.load_clubs_for_category)
        editor_layout.addWidget(self.categories_list)

        # Clubs List
        self.clubs_list = QListWidget()
        editor_layout.addWidget(self.clubs_list)

        layout.addLayout(editor_layout)

        # Action Buttons
        action_buttons_layout = QHBoxLayout()
        buttons = [
            ("➕ Add Category", self.add_category),
            ("➖ Delete Category", self.delete_category),
            ("✏️ Edit Category", self.edit_category),
            ("➕ Add Club", self.add_club),
            ("➖ Delete Club", self.delete_club),
            ("✏️ Edit Club", self.edit_club)
        ]
        for text, callback in buttons:
            button = QPushButton(text)
            button.clicked.connect(callback)
            action_buttons_layout.addWidget(button)

        layout.addLayout(action_buttons_layout)

        # Back Button
        back_button = QPushButton("🔙 Back to View Mode")
        back_button.clicked.connect(self.show_main_section)
        layout.addWidget(back_button)

    def setup_main_section(self):
        """Setup the main section for viewing clubs with a single inline search box."""
        layout = QVBoxLayout(self.main_section)

        # Category Listboxes
        self.category_widgets = {}
        grid_layout = QGridLayout()
        categories = ["Road", "Oval", "Dirt Road", "Dirt Oval"]

        for col, category in enumerate(categories):
            # Add category headers
            category_header = QLabel(category)
            category_header.setAlignment(Qt.AlignCenter)
            category_header.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #007BFF;
                }
            """)
            grid_layout.addWidget(category_header, 0, col)

            # Add category list widgets
            list_widget = QListWidget()
            list_widget.setSelectionMode(QListWidget.MultiSelection)
            self.category_widgets[category] = list_widget
            grid_layout.addWidget(list_widget, 1, col)

        layout.addLayout(grid_layout)

        # Add a single inline search box below the grid
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search across all categories...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
        """)
        self.search_box.textChanged.connect(self.filter_all_categories)
        layout.addWidget(self.search_box)

        # Buttons
        buttons_layout = QHBoxLayout()
        edit_button = QPushButton("✏️ Edit Mode")
        edit_button.clicked.connect(self.show_edit_section)
        buttons_layout.addWidget(edit_button)

        save_button = QPushButton("💾 Save")
        save_button.clicked.connect(self.save_clubs)
        buttons_layout.addWidget(save_button)

        close_button = QPushButton("❌ Close")
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)


    def show_main_section(self):
        """
        Switch back to the main section and refresh the list widgets with the updated data.
        """
        # Refresh the category widgets in the main section
        self.refresh_clubs_data()

        # Switch to the main section in the stacked layout
        self.stacked_layout.setCurrentWidget(self.main_section)


    def filter_all_categories(self, text):
        """
        Filter the clubs displayed in all category widgets based on the search box input.
        """
        # Normalize the search text for case-insensitive comparison
        text = text.lower()

        # Iterate over all category widgets and filter items
        for category, list_widget in self.category_widgets.items():
            list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # Allow horizontal growth but limit vertical
            list_widget.setMaximumHeight(200)  # Restrict excessive height usage


    def refresh_clubs_data(self):
        """
        Reload the reputations data and populate the clubs in all category widgets.
        Preselect clubs based on iracing_reputations_clubs from defaultSettings.json.
        """
        try:
            # Combine all clubs from _reputations.json into a single list
            all_clubs = []
            for group, clubs in self.reputations_data["clubs"].items():
                all_clubs.extend(clubs)

            # Load preselected clubs from defaultSettings.json
            preselected_clubs = self.load_existing_reputations()

            # Populate each category box with the same list of clubs
            for category, list_widget in self.category_widgets.items():
                list_widget.clear()  # Clear the current items in the list
                for club in sorted(set(all_clubs)):  # Avoid duplicates and sort the clubs
                    item = QListWidgetItem(club)
                    list_widget.addItem(item)

                    # Preselect the club if it's in the preselected list for the category
                    if club in preselected_clubs.get(category, []):
                        item.setSelected(True)

        except Exception as e:
            log_to_gui(f"Error refreshing clubs data: {e}", "error")
            QMessageBox.critical(self, "Error", f"Failed to refresh clubs data: {e}")

    def load_existing_reputations(self):
        """
        Load preselected reputations from defaultSettings.json.
        """
        preselected = {}
        try:
            settings = load_default_settings(self.settings_path)
            reputations_string = settings.get("iracing_reputations_clubs", "")
            if reputations_string:
                categories = reputations_string.split(";")
                for idx, category in enumerate(["Road", "Oval", "Dirt Road", "Dirt Oval"]):
                    if idx < len(categories) and categories[idx]:
                        preselected[category] = categories[idx].split(",")
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error loading existing reputations: {e}")
        return preselected


    def save_clubs(self):
        """
        Save the selected clubs for each category back to defaultSettings.json
        and close the Manage Club Reputations window.
        """
        try:
            # Collect selected clubs for each category
            selections = []
            for category, list_widget in self.category_widgets.items():
                selected_items = [item.text() for item in list_widget.selectedItems()]
                selections.append(",".join(selected_items))  # Combine selected clubs for this category

            # Format the clubs into a semicolon-separated string
            final_clubs_string = ";".join(selections)

            # Load the current settings from defaultSettings.json
            current_settings = load_default_settings(self.settings_path)

            # Update the settings with the new value
            updated_data = {"iracing_reputations_clubs": final_clubs_string}
            save_default_settings(self.settings_path, updated_data, current_settings)

            # Log the success
            log_to_gui(f"Updated iracing_reputations_clubs: {final_clubs_string}", "info")

            # Close the Manage Club Reputations window
            self.close()

        except Exception as e:
            log_to_gui(f"Error saving clubs: {e}", "error")
            QMessageBox.critical(self, "Error", f"Failed to save selected clubs: {e}")


    def load_categories(self):
        """Load the categories into the categories list."""
        self.categories_list.clear()
        for category in self.reputations_data["clubs"]:
            self.categories_list.addItem(category)

    def load_clubs_for_category(self, item):
        """Load the clubs for the selected category."""
        category = item.text()
        self.clubs_list.clear()
        for club in self.reputations_data["clubs"].get(category, []):
            self.clubs_list.addItem(club)

    def add_category(self):
        """
        Add a new category to the reputations data.
        """
        category, ok = QInputDialog.getText(self, "Add Category", "Enter a new category name:")
        if ok and category:
            # Ensure the category doesn't already exist
            if category in self.reputations_data["clubs"]:
                QMessageBox.warning(self, "Warning", "Category already exists!")
            else:
                # Add the new category to the reputations data
                self.reputations_data["clubs"][category] = []
                self.load_categories()  # Refresh the categories list
                QMessageBox.information(self, "Success", f"Category '{category}' added successfully!")

    def delete_category(self):
        """
        Delete the selected category from the reputations data.
        """
        item = self.categories_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a category to delete!")
            return

        category = item.text()

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Delete Category",
            f"Are you sure you want to delete the category '{category}'? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Remove the category from the reputations data
            del self.reputations_data["clubs"][category]
            self.load_categories()  # Refresh the categories list
            self.clubs_list.clear()  # Clear the clubs list as the category is deleted
            QMessageBox.information(self, "Success", f"Category '{category}' deleted successfully!")

    def edit_category(self):
        """
        Edit the name of the selected category in the reputations data.
        """
        item = self.categories_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a category to edit!")
            return

        old_category = item.text()
        new_category, ok = QInputDialog.getText(
            self, "Edit Category", "Enter the new category name:", text=old_category
        )
        if ok and new_category:
            if new_category in self.reputations_data["clubs"]:
                QMessageBox.warning(self, "Warning", "Category already exists!")
            else:
                # Update the category name
                self.reputations_data["clubs"][new_category] = self.reputations_data["clubs"].pop(old_category)
                self.load_categories()  # Refresh categories
                QMessageBox.information(self, "Success", f"Category '{old_category}' renamed to '{new_category}'!")

    def add_club(self):
        """
        Add a new club to the selected category.
        """
        category_item = self.categories_list.currentItem()
        if not category_item:
            QMessageBox.warning(self, "Warning", "Please select a category first!")
            return

        category = category_item.text()
        club, ok = QInputDialog.getText(self, "Add Club", "Enter a new club name:")
        if ok and club:
            if club in self.reputations_data["clubs"][category]:
                QMessageBox.warning(self, "Warning", "Club already exists in this category!")
            else:
                # Add the club to the selected category
                self.reputations_data["clubs"][category].append(club)
                self.load_clubs_for_category(category_item)
                QMessageBox.information(self, "Success", f"Club '{club}' added to category '{category}'!")

    def delete_club(self):
        """
        Delete the selected club from the selected category.
        """
        category_item = self.categories_list.currentItem()
        club_item = self.clubs_list.currentItem()
        if not category_item or not club_item:
            QMessageBox.warning(self, "Warning", "Please select a club to delete!")
            return

        category = category_item.text()
        club = club_item.text()

        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Delete Club",
            f"Are you sure you want to delete the club '{club}' from category '{category}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Remove the club from the category
            self.reputations_data["clubs"][category].remove(club)
            self.load_clubs_for_category(category_item)  # Refresh the clubs list
            QMessageBox.information(self, "Success", f"Club '{club}' deleted from category '{category}'!")

    def edit_club(self):
        """
        Edit the name of the selected club in the selected category.
        """
        category_item = self.categories_list.currentItem()
        club_item = self.clubs_list.currentItem()
        if not category_item or not club_item:
            QMessageBox.warning(self, "Warning", "Please select a club to edit!")
            return

        category = category_item.text()
        old_club = club_item.text()
        new_club, ok = QInputDialog.getText(
            self, "Edit Club", "Enter the new club name:", text=old_club
        )
        if ok and new_club:
            if new_club in self.reputations_data["clubs"][category]:
                QMessageBox.warning(self, "Warning", "Club already exists in this category!")
            else:
                # Update the club name
                clubs = self.reputations_data["clubs"][category]
                clubs[clubs.index(old_club)] = new_club
                self.load_clubs_for_category(category_item)  # Refresh the clubs list
                QMessageBox.information(self, "Success", f"Club '{old_club}' renamed to '{new_club}'!")

class Reputations(QDialog):
    def __init__(self, config_path, crewchief_path, reputations_file_path, parent=None):
        super().__init__(parent)
        self.config_path = Path(config_path)
        self.crewchief_path = Path(crewchief_path).parent / "Profiles" / "defaultSettings.json"
        self.default_settings_path = self.crewchief_path
        self.reputations_file = reputations_file_path  # Use the passed path

        # Ensure the file exists or handle errors here if needed
        if not self.reputations_file.exists():
            raise FileNotFoundError(f"Reputations file not found at: {self.reputations_file}")

        self.init_ui()

    def init_ui(self):
        """Initialize the UI elements."""
        # Check if the settings file exists
        if not self.default_settings_path.exists():
            self.display_file_missing_message()
            return

        layout = QVBoxLayout(self)

        # Header Layout
        header_layout = QHBoxLayout()

        # Spacer on the left to balance the alignment
        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(left_spacer)

        # Header Label
        header_label = QLabel("Reputations Settings")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #007BFF;
            }
        """)
        header_layout.addWidget(header_label, alignment=Qt.AlignCenter)

        # Spacer between the label and the switch
        middle_spacer = QWidget()
        middle_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(middle_spacer)

        # **Add Dynamic QLabel Next to the Switch**
        self.switch_label = QLabel("Off")  # Default label is "Off"
        self.switch_label.setAlignment(Qt.AlignRight)
        self.switch_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
        header_layout.addWidget(self.switch_label)

        # Add the switch control with label support
        self.switch = QSwitchControl(label=self.switch_label)  # Pass label to switch
        self.switch.setToolTip(
            "Enable or disable CrewChief Reputations.\n"
            "When disabled, none of the reputation settings will work.\n"
            "Basically, it should always be Enabled!"
        )
        self.switch.toggled.connect(self.on_switch_toggled)
        header_layout.addWidget(self.switch, alignment=Qt.AlignRight)

        layout.addLayout(header_layout)

        # Load the initial state of the switch
        self.load_switch_state()

        # Add the Safety Slider
        section_layout = QVBoxLayout()
        section_header = QLabel("📈 iRacing Reputations Safety")
        section_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        section_layout.addWidget(section_header)

        explanation_label = QLabel(
            "Use the slider below to set your preferred iRacing Safety Rating range (0.00 to 4.99).\n\n"
            "For example, to tag all drivers with a Safety Rating below 1.00 as 'Sketchy,' set the slider to 1.00.\n\n"
            "Setting the slider to 0.0 disables this feature entirely."
        )

        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("font-size: 12px;color: #666666;")
        section_layout.addWidget(explanation_label)

        slider_layout = QFormLayout()
        self.safety_slider = QSlider(Qt.Horizontal)
        self.safety_slider.setRange(0, 499)  # Maps to 0.00 - 4.99
        self.safety_slider.valueChanged.connect(self.update_slider_label)

        # Initialize the safety label first
        self.safety_label = QLabel("Disabled")  # Start with "Disabled" for value 0.0
        self.safety_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.safety_label.setStyleSheet("color: red;")  # Initial color cue for disabled state

        # Load and set the initial value for the safety slider
        safety_value = self.load_safety_value()  # Load saved value
        self.safety_slider.setValue(int(safety_value * 100))  # Convert to slider scale
        self.update_slider_label(self.safety_slider.value())  # Update the label with the current value

        slider_layout.addRow("Safety Rating:", self.safety_slider)
        slider_layout.addRow("Current Value:", self.safety_label)

        section_layout.addLayout(slider_layout)
        layout.addLayout(section_layout)

        # Initialize the category widgets dictionary
        self.category_widgets = {}

        # Example categories (Road, Oval, Dirt Road, Dirt Oval)
        categories = ["Road", "Oval", "Dirt Road", "Dirt Oval"]

        # Create list widgets for each category
        for category in categories:
            list_widget = QListWidget()
            list_widget.setSelectionMode(QListWidget.MultiSelection)
            list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #ffffff;
                    border: 1px solid #dddddd;
                    border-radius: 5px;
                    font-size: 14px;
                    color: #333333;
                }
                QListWidget::item {
                    padding: 4px;
                }
                QListWidget::item:selected {
                    background-color: #e8f0fe;
                    color: #007BFF;
                }
            """)
            self.category_widgets[category] = list_widget

        # Add the club reputation section
        self.add_club_reputations_section(layout)

        # Add Buttons Layout
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_button)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_application)
        buttons_layout.addWidget(exit_button)

        layout.addLayout(buttons_layout)

        # Ensure the default settings file exists
        self.check_default_settings_file()


    def display_file_missing_message(self):
        """
        Display an error message and disable the tab if the settings file is missing.
        """
        layout = QVBoxLayout(self)

        # Error message
        error_message = QLabel(
            "⚠️ The default profile of CrewChief (file 'defaultSettings.json') is missing or inaccessible.\n"
            "This tab has been disabled."
        )
        error_message.setAlignment(Qt.AlignCenter)
        error_message.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: red;
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(error_message)

        # Buttons Layout
        buttons_layout = QHBoxLayout()

        # Exit Button
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_application)
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #3e3e3e;
                border-radius: 12px; /* Adjusted radius for rounded buttons */
                padding: 12px 25px; /* Larger padding for bigger buttons */
                font-size: 16px; /* Slightly increased font size */
                font-weight: bold; /* Make text bold */
            } QPushButton:hover {
                    background-color: #333333;
                    color: white;
                } QPushButton:pressed {
                    background-color: #555555;
                    color: white;
                } QPushButton:disabled {
                    background-color: #3e3e3e;
                    color: #808080;
                }
        """)

        buttons_layout.addWidget(exit_button)

        # Add button layout to the main layout
        layout.addLayout(buttons_layout)

    def get_reputations_file_path(self):
        """
        Dynamically resolve the path to _reputations.json.
        """
        if hasattr(sys, '_MEIPASS'):  # PyInstaller temp extraction directory
            base_path = Path(sys.executable).parent  # Directory of the .exe
        else:
            base_path = Path(__file__).parent.resolve()  # Script's directory during development

        reputations_file = base_path / "_reputations.json"

        # Check if the file exists
        if not reputations_file.exists():
            raise FileNotFoundError(f"Reputations file not found at: {reputations_file}")

        return reputations_file

    def load_reputations_file(self):
        """
        Load the reputations data from _reputations.json.
        """
        try:
            with open(self.reputations_file, "r", encoding="utf-8") as file:
                content = json.load(file)
                if "clubs" not in content or not isinstance(content["clubs"], dict):
                    raise ValueError("The file does not contain a valid 'clubs' key.")
                return content
        except Exception as e:
            raise RuntimeError(f"Failed to load reputations file: {e}")

    def load_switch_state(self):
        """Load the state of the iracing_reputations switch from defaultSettings.json."""
        try:
            # Use the robust loader from _reputations.py
            settings = load_default_settings(self.default_settings_path)
            self.switch.setChecked(settings.get("iracing_reputations", False))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load switch state:\n{e}")
            log_to_gui(f"Failed to load iracing_reputations switch state: {e}", "error")

    def on_switch_toggled(self, state):
        """Handle toggling of the switch and update the settings file silently."""
        try:
            # Load the settings using the robust loader
            settings = load_default_settings(self.default_settings_path)

            # Update the iracing_reputations value
            settings["iracing_reputations"] = state

            # Save the updated settings using the robust saver
            save_default_settings(self.default_settings_path, {"iracing_reputations": state}, settings)

            # Log the change (optional)
            log_to_gui(f"iracing_reputations updated to {state}", "info")
        except Exception as e:
            # Log the error and show a warning if needed
            log_to_gui(f"Failed to update iracing_reputations switch state: {e}", "error")

    def add_safety_slider(self, parent_layout):
        """
        Add the iRacing Reputations Safety slider section and initialize its value
        from defaultSettings.json.
        """
        section_layout = QVBoxLayout()

        # Section Header
        section_header = QLabel("📈 iRacing Reputations Safety")
        section_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        section_layout.addWidget(section_header)

        # Explanation Label
        explanation_label = QLabel(
            "Use the slider below to adjust your iRacing Safety Rating preference (0.00 to 4.99). "
            "Setting the slider to 0.0 disables this feature."
        )
        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("font-size: 12px;color: #666666;")
        section_layout.addWidget(explanation_label)

        # Slider Layout
        slider_layout = QFormLayout()
        self.safety_slider = QSlider(Qt.Horizontal)
        self.safety_slider.setRange(0, 499)  # Maps to 0.00 - 4.99
        self.safety_slider.valueChanged.connect(self.update_slider_label)

        # Initialize the slider value
        safety_value = self.load_safety_value()  # Fetch the saved safety rating
        self.safety_slider.setValue(int(safety_value * 100))  # Convert float to slider scale

        # Safety Label
        self.safety_label = QLabel(f"{safety_value:.2f}" if safety_value > 0 else "Disabled")
        self.safety_label.setStyleSheet("color: red;" if safety_value == 0 else "color: black;")
        slider_layout.addRow("Safety Rating:", self.safety_slider)
        slider_layout.addRow("Current Value:", self.safety_label)

        section_layout.addLayout(slider_layout)

        # Add section to parent layout
        parent_layout.addLayout(section_layout)

    def load_safety_value(self):
        """
        Load the saved iRacing Safety Rating from defaultSettings.json.
        Returns 0.0 if the value is not found or invalid.
        """
        try:
            settings = load_default_settings(self.default_settings_path)
            value = float(settings.get("iracing_reputations_safety", 0.0))
            log_to_gui(f"Loaded safety value from JSON: {value}", "info")  # Debug log
            return value
        except FileNotFoundError:
            log_to_gui(f"File not found: {self.default_settings_path}", "error")
            QMessageBox.critical(self, "Error", "Unable to find defaultSettings.json.")
            return 0.0
        except Exception as e:
            log_to_gui(f"Error loading safety value: {e}", "error")
            return 0.0


    def update_slider_label(self, value):
        """
        Update the label based on the slider value with color cues.
        - Red for "Disabled" when the value is 0.
        - Default color for active values.
        """
        if value == 0:
            self.safety_label.setText("Disabled")
            self.safety_label.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")
        else:
            self.safety_label.setText(f"{value / 100:.2f}")
            self.safety_label.setStyleSheet("color: #555555; font-size: 20px; font-weight: bold;")


    def load_safety_rating(self):
        """
        Load the safety rating value from defaultSettings.json and set it on the slider.
        """
        try:
            settings = load_default_settings(self.default_settings_path)
            safety_value = settings.get("iracing_reputations_safety", 0)

            if isinstance(safety_value, (int, float)):
                self.safety_slider.setValue(int(safety_value * 100))  # Convert to slider range (0-499)
            else:
                log_to_gui("Invalid safety rating value in defaultSettings.json.", "error")
                QMessageBox.warning(
                    self, "Warning", "Safety rating value in defaultSettings.json is invalid. Using default value."
                )
                self.safety_slider.setValue(0)

        except FileNotFoundError:
            log_to_gui("defaultSettings.json not found!", "error")
            QMessageBox.critical(self, "Error", "Unable to find defaultSettings.json.")
        except Exception as e:
            log_to_gui(f"Error loading safety rating: {e}", "error")
            QMessageBox.critical(self, "Error", f"Unexpected error occurred: {e}")

    def add_club_reputations_section(self, parent_layout):
        """Add the Club Reputations section with button aligned next to the list widgets."""
        section_layout = QVBoxLayout()  # Main container layout

        # Section Header
        section_header = QLabel("🏁 Club Reputations")
        section_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        section_layout.addWidget(section_header)

        explanation_label = QLabel(
            "Below are the currently selected clubs. Click 'Manage Clubs' to modify your selections.\n\n"
            "This feature allows you to tag all drivers from a specific club as 'Sketchy.'\n\n"
            "For example, if all drivers from Club X have poor connections, you can tag them as 'Sketchy' to reflect this."
        )
        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("font-size: 12px; color: #666666;")
        section_layout.addWidget(explanation_label)

        # Create a Horizontal Layout for List and Button
        club_layout = QHBoxLayout()
        club_layout.setContentsMargins(0, 0, 0, 0)  # Minimize margins
        club_layout.setSpacing(10)  # Reduce spacing between list and button

        # Compact Display of Selected Clubs
        self.clubs_display = QTextEdit()
        self.clubs_display.setReadOnly(True)
        self.clubs_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clubs_display.setMaximumHeight(60)  # Adjusted height
        self.update_clubs_display()

        club_layout.addWidget(self.clubs_display, stretch=2)  # Reduced stretch factor

        # Manage Clubs Button
        manage_button = QPushButton("⚙️ Manage")
        manage_button.clicked.connect(self.open_club_reputations_popup)
        manage_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        manage_button.setMaximumWidth(150)  # Adjusted width
        club_layout.addWidget(manage_button)

        # Add the row to the main section layout
        section_layout.addLayout(club_layout)

        # Adjust spacing between section elements
        section_layout.setSpacing(5)  # Reduce vertical spacing between elements

        # Add the section to the parent layout
        parent_layout.addLayout(section_layout)

    def update_clubs_display(self):
        """
        Updates the clubs display in the main interface.
        Fetches the latest clubs from `iracing_reputations_clubs` in the settings file and groups them by category.
        """
        try:
            # Load the settings
            settings = load_default_settings(self.default_settings_path)
            clubs_string = settings.get("iracing_reputations_clubs", "")
            clubs_by_category = clubs_string.split(";") if clubs_string else []

            # Define categories (corresponding to indices in the clubs_by_category)
            categories = ["Road", "Oval", "Dirt Road", "Dirt Oval"]

            # Build the display string
            display_text = ""
            for i, category in enumerate(categories):
                if i < len(clubs_by_category) and clubs_by_category[i]:  # Check for valid data
                    clubs = clubs_by_category[i].split(",")  # Split club names
                    display_text += f"{category}: {', '.join(clubs)}\n"

            # Set the updated text in the QTextEdit
            self.clubs_display.setPlainText(display_text if display_text else "No clubs selected.")

            # Apply consistent styling to match the explanation labels
            self.clubs_display.setStyleSheet(
                """
                QTextEdit {
                    font-size: 12px;
                    color: #666666;
                    background-color: #ffffff;
                    border: none;
                }
                """
            )
        except Exception as e:
            log_to_gui(f"Error updating clubs display: {e}", "error")
            self.clubs_display.set


    def open_club_reputations_popup(self):
        """Opens a popup window for managing club reputations."""
        self.manage_clubs_popup = ClubReputationsPopup(
            settings_path=self.default_settings_path,
            reputations_file_path=self.reputations_file,
            parent=self
        )

        # Show the popup and wait for it to close
        self.manage_clubs_popup.exec_()  # Use exec_ for modal behavior

        # Update the clubs display after the popup is closed
        self.update_clubs_display()


    def add_configuration_validation_section(self, parent_layout):
        """
        Add the Configuration Validation section.

        - Placeholder for future configuration validation logic.
        - This section will validate settings and provide feedback.
        """
        section_layout = QVBoxLayout()
        section_header = QLabel("🛠️ Configuration Validation")
        section_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        section_layout.addWidget(section_header)

        explanation_label = QLabel(
            "This section will validate your configuration settings to ensure everything is set up correctly."
            " Future updates will provide automated checks and detailed feedback."
        )
        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("font-size: 12px; color: #666666;")
        section_layout.addWidget(explanation_label)

        # Placeholder label for future validation messages
        placeholder_label = QLabel("Validation logic is under construction.")
        placeholder_label.setStyleSheet("color: #999999; font-style: italic;")
        section_layout.addWidget(placeholder_label)

        parent_layout.addLayout(section_layout)

    def save_settings(self):
        """
        Save the selected clubs and safety rating to defaultSettings.json.

        - Collects data from the safety slider and the clubs display box.
        - Updates `iracing_reputations_safety` and `iracing_reputations_clubs` in the settings.
        - Saves changes back to the settings file, preserving original formatting.
        """
        try:
            # Collect data to save
            settings = load_default_settings(self.default_settings_path)

            # Get safety rating value from the slider
            safety_value = self.safety_slider.value() / 100  # Convert slider value to float

            # Collect clubs from the display text box
            clubs_display_text = self.clubs_display.toPlainText()
            clubs_list = clubs_display_text.split("\n") if clubs_display_text.strip() else []
            clubs_string = ",".join(clubs_list)  # Combine clubs into a single string

            # Prepare updated settings
            updated_data = {
                "iracing_reputations_safety": safety_value,
                "iracing_reputations_clubs": clubs_string,
            }

            # Save to file
            save_default_settings(self.default_settings_path, updated_data, settings)
            log_to_gui(f"Settings saved: safety={safety_value:.2f}, clubs={clubs_string}", "info")
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            log_to_gui(f"Error saving settings: {e}", "error")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def check_default_settings_file(self):
        """
        Check if the defaultSettings.json file exists.
        - Disables the entire tab and displays a message if the file is missing.
        """
        if not self.default_settings_path.exists():
            log_to_gui("Error: defaultSettings.json not found!", "error")

            # Clear existing layout
            self.setLayout(QVBoxLayout())

            # Display error message
            error_message = QLabel("⚠️ The file 'defaultSettings.json' is missing or inaccessible. "
                                   "This tab has been disabled.")
            error_message.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: red;
                    font-weight: bold;
                    text-align: center;
                }
            """)
            error_message.setAlignment(Qt.AlignCenter)

            # Add Exit Button
            exit_button = QPushButton("Exit")
            exit_button.clicked.connect(self.exit_application)
            exit_button.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)

            # Add message and button to the layout
            layout = self.layout()
            layout.addWidget(error_message)
            layout.addWidget(exit_button)

            # Disable interaction with the window
            self.setEnabled(False)


    def exit_application(self):
        """Exit the application."""
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().quit()
