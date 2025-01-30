"""
----------------------------------------------------------------------------------------------------
DriverSync

Version: 0.8
Author:  Pazzie
Email:   cenodude@outlook.com
Discord: cenodude#2185

GitHub:  https://github.com/cenodude/DriverSync

Description:
    This script (DriverSync) helps synchronize driver-related data between iOverlay and CrewChief.

Disclaimer:
    Use this script at your own risk. The author (Pazzie) is not responsible for any damage, data 
    loss, or other consequences resulting from the use or misuse of this script. The user assumes 
    all risks associated with its operation. 

    Furthermore, iOverlay and CrewChief are not affiliated with or endorsed by this project in any 
    way. Any references to or integrations with iOverlay or CrewChief are solely the responsibility 
    of the user, and neither iOverlay nor CrewChief hold any liability for its use.

----------------------------------------------------------------------------------------------------
"""

# Standard library imports
import argparse
import datetime
import json
import logging
import sys
import shutil

from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from _logging import log_to_gui
from _wizard import DriverSyncWizard
from _reputations import Reputations

# PyQt library imports (all 50000 of them)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QFrame,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QGraphicsDropShadowEffect, QGraphicsScene, QGraphicsRectItem, QGraphicsView,
    QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QComboBox, QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QProgressBar,
    QMenu, QMenuBar, QSystemTrayIcon, QToolTip, QTextBrowser, 
    QFileDialog, QInputDialog, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QIcon, QColor, QFont, QBrush
from PyQt5.QtCore import Qt, QTimer, QTime, QEvent, QMetaObject, QRectF

# DriverSync specific imports
from _driversync_logics import DriverSync
from _driversync_logics import get_onedrive_documents_path
from _backup import BackupManager
from _schedular import DriverSyncScheduler
from _about import AboutDialog
from _analytics import AnalyticsOverviewDialog, record_analytics
from _editor import Editor
from _logdashboard import LogDashboard

# for pyinstaller 
def ensure_reputations_file():
    """
    Ensure _reputations.json exists in the correct directory.
    """
    try:
        # Determine the base directory: executable directory for PyInstaller or script directory during development
        if hasattr(sys, '_MEIPASS'):  # PyInstaller temp extraction directory
            base_path = Path(sys._MEIPASS)  # PyInstaller extraction directory
        else:
            base_path = Path(__file__).parent.resolve()  # Script directory during development

        reputations_file = base_path / "_reputations.json"

        # Check if the file exists
        if not reputations_file.exists():
            raise FileNotFoundError(f"_reputations.json not found in: {base_path}")

        return reputations_file
    except Exception as e:
        raise RuntimeError(f"Error in ensure_reputations_file: {str(e)}")

# Set a global fontsize and font family for the application
QToolTip.setFont(QFont("Arial", 14, QFont.Bold))  # Tooltip font

# Ensure the log directory exists
log_folder = Path("Logs")
log_folder.mkdir(parents=True, exist_ok=True)  # Create the Logs directory if it doesn't exist

log_file_path = log_folder / "DriverSync.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3),
    ]
)

def resource_path(relative_path):
    """
    Get the absolute path to the resource.
    """
    base_path = Path(getattr(sys, '_MEIPASS', Path(".").resolve()))
    return base_path / relative_path

def get_default_paths(self):
    """
    Returns default paths for iOverlay and CrewChief, localized for the system's user profile.
    Ensures folders and files exist if they are missing.
    """
    try:
        # Use the centralized OneDrive logic
        documents_folder = Path(get_onedrive_documents_path())

        # Define paths for CrewChief and iOverlay
        crewchief_folder = documents_folder / "CrewChiefV4"
        crewchief_file = crewchief_folder / "iracing_reputations.json"
        ioverlay_path = documents_folder / "iOverlay" / "settings.dat"

        # Ensure CrewChiefV4 folder exists
        crewchief_folder.mkdir(parents=True, exist_ok=True)

        # Ensure iracing_reputations.json exists
        if not crewchief_file.exists():
            with crewchief_file.open("w", encoding="utf-8") as f:
                f.write("[]")  # Write an empty JSON array

        return str(ioverlay_path), str(crewchief_file)
    except Exception as e:
        self.log(f"Error determining default paths: {e}", level="error")
        raise

def load_stylesheet(file_name):
    """
    Load and return the stylesheet content from a given file.
    """
    file_path = resource_path(file_name)
    if not file_path.exists():
        raise FileNotFoundError(f"Stylesheet not found: {file_path}")
    return file_path.read_text(encoding="utf-8")

class SettingsDialog(QDialog):
    def __init__(self, parent=None, synchronizer=None):
        super().__init__(parent)
        if synchronizer is None:
            raise ValueError("The synchronizer parameter is required.")

        self.synchronizer = synchronizer
        self.setWindowTitle("Settings")
        self.resize(600, 550)

        # Initialize category checkboxes dictionary
        self.category_checkboxes = {}

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        self.add_pathnames_section()
        self.add_general_settings_section()
        self.add_sync_behavior_section()
        self.add_categories_section()

        # Save Button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        save_button.setStyleSheet("background-color: #007BFF; color: white; font-size: 14px;")
        self.layout.addWidget(save_button)

    def add_pathnames_section(self):
        pathnames_header = QLabel("📂 Pathnames")
        pathnames_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        self.layout.addWidget(pathnames_header)

        pathnames_form = QFormLayout()

        # iOverlay Path
        self.ioverlay_input = QLineEdit(self.synchronizer.config.get("ioverlay_settings_path", ""))
        ioverlay_browse_button = QPushButton("Browse")
        ioverlay_browse_button.clicked.connect(lambda: self.browse_path("iOverlay", self.ioverlay_input, "settings.dat"))
        pathnames_form.addRow("iOverlay Path:", self.create_path_widget(self.ioverlay_input, ioverlay_browse_button))

        # CrewChief Path
        self.crewchief_input = QLineEdit(self.synchronizer.config.get("crewchief_reputations_path", ""))
        crewchief_browse_button = QPushButton("Browse")
        crewchief_browse_button.clicked.connect(lambda: self.browse_path("CrewChief", self.crewchief_input, "iracing_reputations.json"))
        pathnames_form.addRow("CrewChief Path:", self.create_path_widget(self.crewchief_input, crewchief_browse_button))

        self.layout.addLayout(pathnames_form)

    def create_path_widget(self, input_field, browse_button):
        layout = QHBoxLayout()
        layout.addWidget(input_field)
        layout.addWidget(browse_button)
        return layout

    def browse_path(self, description, input_field, required_file):
        folder_path = QFileDialog.getExistingDirectory(self, f"Select {description} Folder")
        if folder_path:
            input_field.setText(str(Path(folder_path) / required_file))

    def add_general_settings_section(self):
        general_settings_header = QLabel("⚙️ General Settings")
        general_settings_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        self.layout.addWidget(general_settings_header)

        general_form = QFormLayout()

        self.backup_checkbox = QCheckBox("Enable Backup")
        self.backup_checkbox.setChecked(self.synchronizer.config.get("backup_files", True))
        self.retention_spinbox = QSpinBox()
        self.retention_spinbox.setRange(1, 30)
        self.retention_spinbox.setValue(self.synchronizer.config.get("backup_retention_days", 5))
        general_form.addRow("Backup Enabled:", self.backup_checkbox)
        general_form.addRow("Backup Retention Days:", self.retention_spinbox)

        self.minimize_to_tray_checkbox = QCheckBox("Minimize to System Tray")
        self.minimize_to_tray_checkbox.setChecked(self.synchronizer.config.get("minimize_to_tray", False))
        general_form.addRow("Minimize to Tray:", self.minimize_to_tray_checkbox)

        self.layout.addLayout(general_form)

    def add_sync_behavior_section(self):
        sync_behavior_header = QLabel("🔄 Synchronization Behavior")
        sync_behavior_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        self.layout.addWidget(sync_behavior_header)

        sync_behavior_form = QFormLayout()

        self.sync_behavior_combo = QComboBox()
        self.sync_behavior_combo.addItems(["Additive Only", "Bidirectional"])
        self.sync_behavior_combo.setCurrentText(self.synchronizer.config.get("sync_behavior", "Additive Only"))
        sync_behavior_form.addRow("Sync Behavior:", self.sync_behavior_combo)

        self.update_existing_checkbox = QCheckBox("Update Existing Entries")
        self.update_existing_checkbox.setChecked(self.synchronizer.config.get("update_existing_entries", False))
        self.update_existing_checkbox.toggled.connect(self.on_update_existing_toggled)
        sync_behavior_form.addRow("Update Existing Entries:", self.update_existing_checkbox)

        self.layout.addLayout(sync_behavior_form)

    def add_categories_section(self):
        categories_header = QLabel("📋 Categories")
        categories_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        self.layout.addWidget(categories_header)

        self.category_layout = QVBoxLayout()
        self.create_category_checkboxes()
        self.layout.addLayout(self.category_layout)

    def create_category_checkboxes(self):
        self.category_checkboxes = {}
        categories = self.synchronizer.load_categories()
        for category in categories:
            name = category.get("name", "Unknown")
            checkbox = QCheckBox(name)
            checkbox.setChecked(self.synchronizer.enabled_categories.get(name, False))
            self.category_layout.addWidget(checkbox)
            self.category_checkboxes[name] = checkbox

    def on_update_existing_toggled(self, checked):
        self.synchronizer.config["update_existing_entries"] = checked

    def save_settings(self):
        # Ensure update_existing_entries is correctly assigned before saving
        self.synchronizer.update_existing_entries = self.update_existing_checkbox.isChecked()

        self.synchronizer.config.update({
            "ioverlay_settings_path": self.ioverlay_input.text(),
            "crewchief_reputations_path": self.crewchief_input.text(),
            "backup_files": self.backup_checkbox.isChecked(),
            "backup_retention_days": self.retention_spinbox.value(),
            "update_existing_entries": self.update_existing_checkbox.isChecked(),  # This should now work
            "sync_behavior": self.sync_behavior_combo.currentText(),
            "minimize_to_tray": self.minimize_to_tray_checkbox.isChecked()
        })
        self.synchronizer.save_config()
        self.accept()

class PreviewDialog(QDialog):
    def __init__(self, preview_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Synchronization Preview")
        self.resize(800, 400)

        # Main layout
        layout = QVBoxLayout(self)

        # Table to display preview data
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Source", "Details"])
        layout.addWidget(self.table)

        # Populate the table with preview data
        self.table.setRowCount(len(preview_data))
        for row, item in enumerate(preview_data):
            action_item = QTableWidgetItem(item["action"])
            source_item = QTableWidgetItem(item["source"])
            details_item = QTableWidgetItem(item["details"])

            # Align text to the left
            action_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            source_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            details_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            self.table.setItem(row, 0, action_item)
            self.table.setItem(row, 1, source_item)
            self.table.setItem(row, 2, details_item)

        # Adjust table column resizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        # Resize rows and columns to fit contents
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

class MarkdownHelpDialog(QDialog):
    def __init__(self, markdown_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DriverSync Help")
        self.resize(800, 600)

        # Main layout
        layout = QVBoxLayout(self)

        # Markdown viewer
        self.text_browser = QTextBrowser(self)
        try:
            with open(markdown_path, "r", encoding="utf-8") as md_file:
                self.text_browser.setMarkdown(md_file.read())
        except FileNotFoundError:
            self.text_browser.setPlainText("Help content not found.")
        layout.addWidget(self.text_browser)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        # Apply custom styles
        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Apply custom stylesheet to match the main theme."""
        self.setStyleSheet("""
            QTextBrowser {
                background-color: #f0f4f8;
                color: #334e68;
                font-size: 14px;
                padding: 10px;
                border: 1px solid #007BFF;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                font-size: 14px;
                padding: 8px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

class DriverSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DriverSync by Pazzie")
        self.setWindowIcon(QIcon(str(resource_path("sync.ico"))))
        self.resize(900, 600)
        self.reputations_file_path = self.resolve_reputations_file_path()

        self.countdown_timer = None
        self.next_run_time = None
        self.paused_remaining_time = None  # Store the remaining time when paused
        self.scheduler_paused = False     # Track whether the scheduler is paused
        self.remaining_time_paused = None  # Initialize paused time tracking
        self.is_paused = False  # Track whether the scheduler is paused

        try:
            # Initialize the synchronizer
            self.synchronizer = DriverSync(log_to_gui=self.log_to_gui, ui=self)
            self.editor = Editor(self.synchronizer)
            self.editor_tab = Editor(self.synchronizer)

            # Scheduler configuration
            interval_hours = self.synchronizer.config.get("scheduler_interval")

        except FileNotFoundError as e:
            # Handle missing critical files
            self.synchronizer = None
            self.editor = None
            self.log_to_gui(f"Critical file not found: {e}", "error")
            interval_hours = None

        except json.JSONDecodeError as e:
            # Handle malformed configuration file
            self.synchronizer = None
            self.editor = None
            self.log_to_gui("Invalid or corrupted config.json detected. Please reset the configuration.", "error")
            interval_hours = None

        except Exception as e:
            # Handle other initialization errors
            self.synchronizer = None
            self.editor = None
            self.log_to_gui(f"General initialization error: {e}", "error")
            interval_hours = None

        # Initialize the UI and system tray
        self.init_ui()
        self.init_system_tray()
        self.apply_light_theme()
        self.create_log_folder()

        # Initialize the scheduler
        self.scheduler = DriverSyncScheduler(self.synchronizer, self.log_to_gui)
        self.scheduler.running = False

        if interval_hours:
            try:
                self.scheduler.start_scheduler(interval_hours)
                self.start_countdown(interval_hours)
                self.log_to_gui(f"Scheduler started with an interval of {interval_hours} hour(s).", "info")
            except Exception as e:
                self.log_to_gui(f"Failed to start scheduler: {e}", "error")
        else:
            self.log_to_gui("Scheduler inactive: No valid interval set.", "info")

        # Initialize backup manager
        self.backup_manager = BackupManager(log_func=self.log_to_gui)

        # Update button states based on file validation
        self.update_button_state()

        # Validate files and provide feedback
        if self.synchronizer and getattr(self.synchronizer, "sync_enabled", False):
            self.log_to_gui("DriverSync initialized successfully.", "success")
        elif self.synchronizer:
            self.log_to_gui("DriverSync initialized but disabled, due to missing or invalid source files.", "error")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Menu Bar
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        # File Menu
        file_menu = menu_bar.addMenu("📂 File")
        file_menu.addAction("📊 Analytics", self.open_analytics).setToolTip("View synchronization analytics.")
        file_menu.addAction("❌ Exit", self.close).setToolTip("Exit the application.")

        # Settings Menu
        settings_menu = menu_bar.addMenu("⚙️ Settings")
        settings_menu.addAction("🔧 Configure", self.open_settings).setToolTip("Open the settings dialog.")
        settings_menu.addAction("🛠️ Setup Wizard", self.open_wizard).setToolTip("Launch the setup wizard.")

        # Scheduler Menu
        scheduler_menu = menu_bar.addMenu("⏰ Scheduler")
        scheduler_menu.addAction("🕒 Scheduler Settings", self.open_scheduler_settings).setToolTip("Set the synchronization interval.")

        # Help Menu
        help_menu = menu_bar.addMenu("❓ Help")
        help_menu.addAction("ℹ️ About", self.open_about).setToolTip("View information about DriverSync.")
        help_menu.addAction("📖 View Help", self.open_help_dialog).setToolTip("Open the DriverSync Help guide.")

        # Tabs
        self.tabs = QTabWidget()

        # Synchronization Tab
        sync_tab = QWidget()
        sync_layout = QVBoxLayout()  # Initialize sync_layout here
        sync_tab.setLayout(sync_layout)

        # Header with Unicode Icon
        sync_header = QLabel("Synchronization Dashboard")
        sync_header.setAlignment(Qt.AlignCenter)
        sync_header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #007BFF;
                margin-bottom: 15px;
            }
        """)
        sync_layout.addWidget(sync_header)

        # Log Dashboard
        self.log_dashboard = LogDashboard()
        sync_layout.addWidget(self.log_dashboard)


        # Buttons Layout
        button_layout = QHBoxLayout()

        # Sync Button
        self.sync_button = QPushButton("Sync Now")
        self.sync_button.setEnabled(False)
        self.sync_button.clicked.connect(self.sync_files)
        self.sync_button.setToolTip("Click to synchronize data between iOverlay and CrewChief.")
        button_layout.addWidget(self.sync_button)

        # Preview Button
        self.preview_button = QPushButton("Preview")
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self.open_preview)
        self.preview_button.setToolTip("Preview synchronization changes without applying them.")
        button_layout.addWidget(self.preview_button)

        # Exit Button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setToolTip("Exit the application.")
        button_layout.addWidget(self.exit_button)

        sync_layout.addLayout(button_layout)

        # Countdown Label
        self.countdown_label = QLabel("Scheduler is off")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setToolTip("Shows the remaining time until the next scheduled synchronization.")

        # Apply styling and shadow
        self.countdown_label.setStyleSheet("""
            QLabel {
                font-size: 18px;  /* Increased font size */
                font-weight: 600;  /* Slightly bolder font */
                color: #FFFFFF;
                background-color: #007BFF;  /* Bright blue background */
                border-radius: 10px;  /* Slightly larger rounded corners */
                padding: 8px 20px;  /* Increased padding for a larger label */
                text-align: center;
            }
        """)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(3)  # Reduced blur for subtle shadow
        shadow_effect.setXOffset(1)  # Minimal horizontal offset
        shadow_effect.setYOffset(1)  # Minimal vertical offset
        shadow_effect.setColor(QColor(0, 0, 0, 50))  # Lighter shadow
        self.countdown_label.setGraphicsEffect(shadow_effect)


        self.countdown_label.mousePressEvent = self.toggle_scheduler
        sync_layout.addWidget(self.countdown_label)  # Use the sync_layout initialized earlier

        main_layout.addWidget(sync_tab)  # Add the sync tab to the main layout

        # Add tabs sync
        self.tabs.addTab(sync_tab, "Sync")

        # Editor Tab
        self.editor_tab = Editor(self.synchronizer)
        self.tabs.addTab(self.editor_tab, "Editor")
        self.editor_tab.set_tab_widget(self.tabs)  # Pass the tab widget reference

        # Reputations Tab
        rep_tab = QWidget()
        rep_layout = QVBoxLayout()
        rep_tab.setLayout(rep_layout)
        self.tabs.addTab(rep_tab, "Reputations")

        # Connect tab change event
        self.tabs.currentChanged.connect(self.on_tab_change)

        # Add the tabs to the main layout
        main_layout.addWidget(self.tabs)

    def resolve_reputations_file_path(self):
        try:
            reputations_file = ensure_reputations_file()
            self.log_to_gui(f"Reputations file path resolved to: {reputations_file}", level="info")
            return reputations_file
        except Exception as e:
            self.log_to_gui(f"Failed to resolve reputations file path: {e}", level="error")
            QMessageBox.critical(self, "Error", f"Failed to locate reputations file:\n{e}")
            sys.exit(1)

    def on_tab_change(self):
        """
        Update the tab style and content dynamically based on the selected tab.
        """
        try:
            current_tab_text = self.tabs.tabText(self.tabs.currentIndex())
            self.log_to_gui(f"Tab changed to: {current_tab_text}", level="debug")

            if current_tab_text == "Editor":
                self.log_to_gui("Entering Editor tab.", level="debug")
                if hasattr(self, 'editor_tab') and hasattr(self.editor_tab, 'on_switch_toggled'):
                    self.editor_tab.on_switch_toggled(False)  # Default to iOverlay
                else:
                    self.log_to_gui("Editor tab is missing 'on_switch_toggled' method.", level="error")
            elif current_tab_text == "Reputations":
                if not hasattr(self, 'reputations_file_path') or not self.reputations_file_path:
                    self.log_to_gui("Reputations file path is not set.", level="error")
                    QMessageBox.critical(self, "Error", "Reputations file path is not configured.")
                    return

                if not hasattr(self, 'reputations_tab_initialized'):
                    self.log_to_gui("Initializing Reputations tab.", level="debug")

                    try:
                        reputations_tab = Reputations(
                            config_path=self.synchronizer.config_file,
                            crewchief_path=self.synchronizer.crewchief_path,
                            reputations_file_path=self.reputations_file_path  # Pass the resolved path
                        )
                        self.tabs.widget(self.tabs.currentIndex()).layout().addWidget(reputations_tab)
                        self.reputations_tab_initialized = True
                        # self.log_to_gui("Reputations tab initialized successfully.", level="info")
                    except Exception as e:
                        self.log_to_gui(f"Failed to initialize Reputations tab: {e}", level="error")
                        QMessageBox.critical(self, "Error", f"Failed to load Reputations tab:\n{e}")
            else:
                self.log_to_gui(f"Unhandled tab: {current_tab_text}. No specific action taken.", level="debug")
        except Exception as e:
            self.log_to_gui(f"Error in on_tab_change: {e}", level="error")
            QMessageBox.critical(self, "Error", f"An error occurred while switching tabs:\n{e}")

    def init_category_settings(self):
        """
        Initialize category-related settings.
        """
        categories_header = QLabel("iOverlay Categories Sync")
        categories_header.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px 0;")
        self.layout.addWidget(categories_header)

        self.category_layout = QVBoxLayout()
        self.create_category_checkboxes()
        self.layout.addLayout(self.category_layout)
        
    def create_category_checkboxes(self):
        self.category_checkboxes = {}
        for category in self.categories:
            name = category.get("name")
            if name:
                checkbox = QCheckBox(name)
                checkbox.setChecked(self.enabled_categories.get(name, False))
                checkbox.toggled.connect(lambda state, name=name: self.toggle_category(name, state))
                self.category_layout.addWidget(checkbox)
                self.category_checkboxes[name] = checkbox
                
    def toggle_category(self, name, state):
        self.synchronizer.enabled_categories[name] = state
        
    def apply_light_theme(self):
        try:
            stylesheet = load_stylesheet("light_theme.css")
            self.setStyleSheet(stylesheet)
        except FileNotFoundError as e:
            self.log_to_gui(f"Error loading stylesheet: {e}", "error")
     

    def init_system_tray(self):
        """
        Initializes the system tray icon and menu.
        """
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(str(resource_path("sync.ico"))))

        # Create the system tray menu
        tray_menu = QMenu(self)

        # Add countdown action to tray menu
        self.countdown_action = tray_menu.addAction("Next run: None")
        self.countdown_action.setEnabled(True)  # Make it interactive
        self.countdown_action.triggered.connect(self.toggle_tray_scheduler)

        # Add Open and Exit actions
        open_action = tray_menu.addAction("Open")
        open_action.triggered.connect(self.showNormal)

        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_application)

        # Set the tray menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # Show the tray icon
        self.tray_icon.show()


    def update_system_tray_next_run(self, next_run_time=None):
        """
        Updates the countdown text in the system tray menu.
        """
        if next_run_time:
            countdown_text = f"Next run: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            countdown_text = "Next run: None"

    def on_tray_icon_activated(self, reason):
        """
        Restore the application when the tray icon is activated.
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()

    def exit_application(self):
        """
        Exit the application gracefully.
        """
        self.tray_icon.hide()
        self.close()
        
    def set_scheduler_interval(self):
        current_interval = self.synchronizer.config.get("scheduler_interval") or 1
        interval, ok = QInputDialog.getInt(
            self,
            "Scheduler Interval",
            "Enter interval in hours (or cancel to stop):",
            value=current_interval,
            min=1,
            max=24
        )

        if ok:
            # User confirmed the new interval
            self.synchronizer.config["scheduler_interval"] = interval
            self.synchronizer.save_config()
            self.scheduler.start_scheduler(interval)
            self.start_countdown(interval)
            self.log_to_gui(f"Scheduler interval set to {interval} hour(s).", "success", to_gui=False)
            self.tray_icon.showMessage(
                "Scheduler Updated",
                f"Interval set to {interval} hour(s).",
                QSystemTrayIcon.Information,
                3000
            )
        else:
            # User canceled, reset interval to null
            self.synchronizer.config["scheduler_interval"] = None
            self.synchronizer.save_config()
            self.scheduler.stop_scheduler()
            self.stop_countdown()
            self.log_to_gui("Scheduler stopped and disabled.", "info", to_gui=False)
        
    def start_background_mode(self):
        print("Starting background mode...")
        self.hide()  # Hide the main application window
        try:
            self.tray_icon.show()  # Explicitly show the tray icon
            print("Tray icon displayed.")
        except Exception as e:
            print(f"Error displaying tray icon: {e}")

        # Start the scheduler
        interval_hours = self.scheduler.interval_hours or 1  # Default interval
        self.scheduler.start_scheduler(interval_hours)
            
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() == Qt.WindowMinimized:
                minimize_to_tray = self.synchronizer.config.get("minimize_to_tray", False)
                if minimize_to_tray:
                    print("Minimizing to system tray...")
                    self.hide()  # Hide the application from the taskbar
                    self.tray_icon.showMessage(
                        "DriverSync",
                        "DriverSync is running in the background.",
                        QSystemTrayIcon.Information,
                        3000  # Duration in milliseconds
                    )
                    event.accept()

    def open_help_dialog(self):
        """Open the Help dialog to display the DriverSync_README.md."""
        help_path = resource_path("DriverSync_README.md")
        dialog = MarkdownHelpDialog(markdown_path=help_path, parent=self)
        dialog.exec_()

    def open_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def open_reputations_settings(self):
        """Open the Reputations Settings dialog."""
        if not self.synchronizer.config.get("crewchief_reputations_path"):
            QMessageBox.critical(self, "Error", "CrewChief path is not configured.")
            return

        reputations_dialog = ReputationsSettings(self.synchronizer.config["crewchief_reputations_path"], self)
        reputations_dialog.exec_()

    def start_countdown(self, interval_hours=None):
        """
        Starts the countdown timer for the next run.
        If interval_hours is None, resumes from the remaining time.
        """
        if self.scheduler_paused:
            self.log_to_gui("Countdown is paused. Cannot start.", "warning")
            return

        if interval_hours:
            self.remaining_seconds = interval_hours * 3600

        self.next_run_time = datetime.now() + timedelta(seconds=self.remaining_seconds)

        if self.countdown_timer:
            self.countdown_timer.stop()

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.timeout.connect(self.update_tray_countdown)
        self.countdown_timer.start(1000)
        self.update_countdown()
        self.update_tray_countdown()


    def update_tray_countdown(self):
        """Update the tray menu's countdown status."""
        if self.scheduler_paused:
            countdown_text = "Scheduler is paused"
        elif not self.next_run_time:
            countdown_text = "Next run in: Not scheduled"
        else:
            remaining_time = (self.next_run_time - datetime.now()).total_seconds()
            if remaining_time > 0:
                hours, remainder = divmod(remaining_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                countdown_text = f"Next run in: {int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            else:
                countdown_text = "Next run in: Running now..."

        self.countdown_action.setText(countdown_text)  # Update the tray menu text


    def update_countdown(self):
        """
        Update the countdown label.
        """
        if self.scheduler_paused:
            return  # Don't update if the scheduler is paused

        if not self.next_run_time:
            self.countdown_label.setText("Scheduler is off")
            return

        remaining_time = max(0, (self.next_run_time - datetime.now()).total_seconds())

        if remaining_time <= 0:
            self.countdown_label.setText("Synchronization in progress...")
            self.countdown_timer.stop()

            # Perform synchronization
            try:
                self.sync_files()
            except Exception as e:
                self.log_to_gui(f"Error during synchronization: {e}", "error")

            # Restart the countdown for the next interval
            self.start_countdown(self.synchronizer.config.get("scheduler_interval", 1))
        else:
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.countdown_label.setText(f"Next run in: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")

        # Calculate remaining time
        remaining_time = (self.next_run_time - datetime.now()).total_seconds()

        if remaining_time <= 0:
            self.countdown_label.setText("Synchronization in progress...")
            self.countdown_timer.stop()

            # Use sync_files for synchronization
            try:
                self.sync_files()
            except Exception as e:
                self.log_to_gui(f"Error during synchronization: {e}", "error")

            # Restart countdown for the next interval
            self.start_countdown(self.interval_hours)
        else:
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.countdown_label.setText(f"Next run in: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")

    def create_log_folder(self):
        log_folder = Path("Logs")
        log_folder.mkdir(parents=True, exist_ok=True)  # Create the Logs directory if it doesn't exist

    def update_button_state(self, sync_enabled=None):
        """
        Updates the state of buttons and tabs based on path validation.
        """
        if sync_enabled is None:
            sync_enabled = getattr(self.synchronizer, "sync_enabled", False)

        # Update Sync and Preview buttons
        self.sync_button.setEnabled(sync_enabled)
        self.preview_button.setEnabled(sync_enabled)

        # Log the state for Sync and Preview
        if not sync_enabled:
            self.log_to_gui("DriverSync is disabled! Ensure iOverlay settings.dat is available.", "error")

        # Enable or disable the Editor and Reputations tabs
        editor_index = self.tabs.indexOf(self.editor_tab)
        reputations_index = self.tabs.indexOf(self.tabs.widget(self.tabs.count() - 1))  # Assuming the last tab is Reputations

        self.tabs.setTabEnabled(editor_index, sync_enabled)
        self.tabs.setTabEnabled(reputations_index, sync_enabled)

        # Log changes to the tabs' state
        if not sync_enabled:
            pass

    def log_to_gui(self, message, level="info", bold=False, include_timestamp=False, html=False, to_file=True):

        # Generate the log message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if include_timestamp else ""
        full_message = f"{timestamp} {message}".strip()

        colors = {
            "info": "black",
            "error": "red",
            "success": "green",
            "warning": "orange",
            "debug": "gray",
        }
        color = colors.get(level.lower(), "black")

        # Format the message for the GUI
        if html:
            formatted_message = message  # Assume message is already formatted in HTML
        else:
            style = f"color:{color};"
            if bold:
                style += " font-weight:bold;"
            formatted_message = f'<div><span style="{style}">{full_message}</span></div>'

        # Update the GUI dashboard if available
        if hasattr(self, "log_dashboard") and self.log_dashboard is not None:
            QTimer.singleShot(0, lambda: self.log_dashboard.add_log(level.capitalize(), full_message))

        # Write to the log file if enabled
        if to_file:
            try:
                self._log_to_file(full_message, level)
            except Exception as e:
                # Log the error only to the file if writing fails
                self._log_to_file(f"[ERROR] Failed to write to log file: {e}", "error")

        # Handle specific cases for log messages
        if "settings.dat file not found" in message.lower() and level.lower() == "info":
            self.update_button_state(sync_enabled=False)

    def _log_to_file(self, message, level):
        """
        Appends a log entry to the log file with a timestamp and level.
        Ensures the log file is stored in a Logs directory.
        """

        # Ensure the Logs directory exists
        log_dir = Path("Logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Define the log file path
        log_file = log_dir / "DriverSync.log"

        # Prepare the log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"

        # Write to the log file
        with log_file.open("a", encoding="utf-8") as file:
            file.write(log_entry + "\n")

    def sync_files(self):
        """
        Synchronize files between iOverlay and CrewChief with error handling, logging, and overview updates.
        """
        sync_mode = self.synchronizer.config.get("sync_behavior", "Additive Only")
        self.log_to_gui(f"Starting synchronization in '{sync_mode}' mode...", bold=True, include_timestamp=False)

        try:
            # Perform backups if enabled
            if self.synchronizer.config.get("backup_files", False):
                self.log_to_gui("Creating backup zip before synchronization...", "info")
                try:
                    files_to_backup = [
                        self.synchronizer.ioverlay_path,
                        self.synchronizer.crewchief_path
                    ]
                    backup_manager = BackupManager()
                    backup_manager.create_backup_zip(files_to_backup, "Backup")
                    self.log_to_gui("Backup zip created successfully.", "success")
                except Exception as e:
                    self.log_to_gui(f"Error creating backup zip: {e}", "error")

            # Perform synchronization
            success, details, preview_data = self.synchronizer.synchronize_files(dry_run=False)

            if success:
                self.log_to_gui("Synchronization completed successfully!", "success")

                # Update driver overview
                QTimer.singleShot(0, lambda: self.update_driver_overview(
                    added_to_ioverlay=details.get("added_to_ioverlay", 0),
                    added_to_crewchief=details.get("added_to_crewchief", 0),
                    deleted_from_ioverlay=details.get("deleted_from_ioverlay", 0),
                    deleted_from_crewchief=details.get("deleted_from_crewchief", 0),
                    total_ioverlay_drivers=details.get("total_ioverlay", 0),
                    total_crewchief_drivers=details.get("total_crewchief", 0),
                ))
            else:
                self.log_to_gui("Synchronization failed.", "error")
        except Exception as e:
            self.log_to_gui(f"Error during synchronization: {e}", "error")

    def open_settings(self):
        try:
            # Create and open the settings dialog
            dialog = SettingsDialog(self, self.synchronizer)

            # Populate input fields with the current configuration paths
            dialog.ioverlay_input.setText(self.synchronizer.config.get("ioverlay_settings_path", ""))
            dialog.crewchief_input.setText(self.synchronizer.config.get("crewchief_reputations_path", ""))

            # Execute the dialog and apply changes if accepted
            if dialog.exec_() == QDialog.Accepted:
                self.log_to_gui("Settings updated successfully.", "success")
                # Revalidate button states after updating settings
                self.revalidate_buttons()
            else:
                self.log_to_gui("Settings update was canceled by the user.", "info")

        except Exception as e:
            # Log and handle errors gracefully
            self.log_to_gui(f"Error opening settings dialog: {e}", "error")

    def update_driver_overview(
        self,
        added_to_ioverlay=0,
        added_to_crewchief=0,
        deleted_from_ioverlay=0,
        deleted_from_crewchief=0,
        total_ioverlay_drivers=0,
        total_crewchief_drivers=0,
    ):
        # Define a fixed-width format for alignment
        log_format = "{:<10} {:<20} {:<20}"

        # Log overview details
        self.log_dashboard.add_log("Info", log_format.format("✅ Added:  ", f"iOverlay: {added_to_ioverlay}", f"CrewChief: {added_to_crewchief}"))
        self.log_dashboard.add_log("Info", log_format.format("❌ Deleted:", f"iOverlay: {deleted_from_ioverlay}", f"CrewChief: {deleted_from_crewchief}"))

    def revalidate_buttons(self):
        # Validate configuration files using the synchronizer
        valid_config = self.synchronizer.validate_config_files()

        # Ensure valid_config is a boolean
        if isinstance(valid_config, bool):
            self.sync_button.setEnabled(valid_config)
            self.preview_button.setEnabled(valid_config)
        else:
            # Disable buttons and log an error if validation result is unexpected
            self.sync_button.setEnabled(False)
            self.preview_button.setEnabled(False)
            self.log_to_gui("Unexpected validation result. Disabling buttons.", "error")

        # Log debug or warning messages based on validation result
        if valid_config:
            self._log_to_file("Sync and Preview are enabled.", level="debug")
        else:
            self._log_to_file("Sync and Preview are disabled due to invalid configuration.", "warning")


    def open_preview(self):
        self.log_to_gui("Generating preview...", "info")
        try:
            _, _, preview_data = self.synchronizer.synchronize_files(dry_run=True)
            dialog = PreviewDialog(preview_data, self)
            dialog.exec()
        except Exception as e:
            self.log_to_gui(f"Error generating preview: {e}", "error")


    def open_scheduler_settings(self):
        """
        Opens the Scheduler Settings dialog with improved structure and styling.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("🕒 Scheduler Settings")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_label = QLabel("🕒 Scheduler Settings")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        layout.addWidget(header_label)

        # Explanation Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        explanation_label = QLabel(
            "The scheduler automates synchronization at regular intervals. "
            "Specify the interval (in hours) to ensure your data stays updated."
        )
        explanation_label.setStyleSheet("font-size: 12px; color: #555555;")
        explanation_label.setWordWrap(True)
        layout.addWidget(explanation_label)

        # Scheduler Interval Input
        interval_layout = QFormLayout()
        interval_layout.setSpacing(10)

        interval_spinbox = QSpinBox()
        interval_spinbox.setRange(1, 24)
        interval_spinbox.setValue(self.synchronizer.config.get("scheduler_interval") or 1)  # Default to 1 if None
        interval_layout.addRow("Synchronization Interval (hours):", interval_spinbox)
        layout.addLayout(interval_layout)

        # Buttons Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Save Button
        save_button = QPushButton("Save")
        save_button.setStyleSheet("background-color: #007BFF; color: white; font-size: 14px;")
        save_button.clicked.connect(lambda: self.save_scheduler_settings(dialog, interval_spinbox))
        button_layout.addWidget(save_button)

        # Cancel Scheduler Button
        cancel_button = QPushButton("Cancel Scheduler")
        cancel_button.setStyleSheet("background-color: #dc3545; color: white; font-size: 14px;")
        cancel_button.clicked.connect(lambda: self.cancel_scheduler(dialog))
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # Open the dialog
        dialog.exec_()

    def save_scheduler_settings(self, dialog, interval_spinbox):
        """
        Saves the scheduler settings using the existing logic.
        """
        interval = interval_spinbox.value()

        # Update the configuration
        self.synchronizer.config["scheduler_interval"] = interval
        self.synchronizer.save_config()

        # Start the scheduler with the new interval
        self.scheduler.start_scheduler(interval)
        self.start_countdown(interval)

        self.log_to_gui(f"Scheduler interval set to {interval} hour(s).", "success")
        self.tray_icon.showMessage(
            "Scheduler Updated",
            f"Interval set to {interval} hour(s).",
            QSystemTrayIcon.Information,
            3000,
        )

        dialog.accept()

    def cancel_scheduler(self, dialog):
        """
        Stops the scheduler and clears the interval.
        """
        self.scheduler.stop_scheduler()
        self.stop_countdown()
        self.synchronizer.config["scheduler_interval"] = None
        self.synchronizer.save_config()

        self.log_to_gui("Scheduler stopped and disabled.", "warning")
        self.tray_icon.showMessage(
            "Scheduler Stopped",
            "The scheduler has been disabled.",
            QSystemTrayIcon.Warning,
            3000,
        )

        dialog.accept()


    def stop_countdown(self):
        """
        Stops the countdown timer and updates the countdown label.
        """
        if hasattr(self, "countdown_timer") and self.countdown_timer:
            self.countdown_timer.stop()  # Stop the countdown timer if it exists
        if hasattr(self, "countdown_label") and self.countdown_label:
            self.countdown_label.setText("Scheduler is off")  # Update the label to indicate the scheduler is off

    def toggle_scheduler(self, event=None):
        """
        Handles toggling the scheduler state (pause, resume, or open settings).
        """
        if not self.scheduler.running:
            # If the scheduler is not active, open the settings dialog
            self.log_to_gui("Scheduler inactive. Opening settings...", "info")
            self.open_scheduler_settings()
            return

        if self.scheduler_paused:
            # Resume the scheduler from the paused state
            self.scheduler_paused = False
            self.start_countdown(self.remaining_seconds / 3600)  # Convert seconds to hours
            self.log_to_gui("Scheduler resumed from paused state.", "info")
        else:
            # Pause the scheduler and save the remaining time
            self.scheduler_paused = True
            self.remaining_seconds = (self.next_run_time - datetime.now()).total_seconds()
            self.stop_countdown()
            self.log_to_gui("Scheduler paused.", "warning")

    def toggle_tray_scheduler(self, _):
        if self.scheduler and not self.scheduler.running:
            self.open_scheduler_settings()
            return

        if self.is_paused:
            # Resume the scheduler
            if self.remaining_time_paused:
                self.next_run_time = datetime.now() + timedelta(seconds=self.remaining_time_paused)
                self.start_countdown(self.remaining_time_paused / 3600)  # Convert seconds to hours
                self.remaining_time_paused = None
            self.is_paused = False
            self.log_to_gui("Scheduler resumed.", "info")
        else:
            # Pause the scheduler
            if self.next_run_time:
                self.remaining_time_paused = (self.next_run_time - datetime.now()).total_seconds()
            self.is_paused = True
            self.stop_countdown()  # Stops the countdown timer
            self.log_to_gui("Scheduler paused.", "warning")

    def closeEvent(self, event):
        """
        Handle window close event.
        Minimize to the system tray or stop the scheduler.
        """
        if self.synchronizer.config.get("minimize_to_tray", False):
            self.hide()
            self.tray_icon.showMessage(
                "DriverSync",
                "The application is minimized to the system tray.",
                QSystemTrayIcon.Information,
                3000
            )
            event.ignore()
        else:
            self.scheduler.stop_scheduler()
            self.stop_countdown()
            super().closeEvent(event)

    def open_analytics(self):
        dialog = AnalyticsOverviewDialog(self)
        dialog.exec()

    def open_wizard(self):
        """
        Open the setup wizard manually from the settings.
        If the user exits, no changes are saved, and they return to DriverSync.
        """
        try:
            wizard = DriverSyncWizard(auto_mode=False, parent=self)  # Pass the parent window
            wizard.exec_()  # Launch the wizard as a modal dialog
        except Exception as e:
            self.log_to_gui(f"Error launching setup wizard: {e}", "error")

if __name__ == "__main__":
    print("Launching DriverSync with GUI...")

    # Create the application
    app = QApplication(sys.argv)

    # Ensure _reputations.json is available
    try:
        reputations_file_path = ensure_reputations_file()
        # print(f"_reputations.json available at: {reputations_file_path}")
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

    # Check if config.json exists
    config_path = Path("config.json")
    if not config_path.exists():
        log_to_gui("Configuration file not found. Launching setup wizard...", "info")
        
        # Launch the wizard in auto mode
        wizard = DriverSyncWizard(auto_mode=True)
        wizard.exec_()  # Launch wizard as a modal dialog

        # Re-check if config.json is created after the wizard
        if not config_path.exists():
            log_to_gui("Setup incomplete. Exiting...", "error")
            sys.exit(1)  # Exit if setup is incomplete

    # Apply the light theme
    try:
        stylesheet = load_stylesheet("light_theme.css")
        app.setStyleSheet(stylesheet)
    except FileNotFoundError as e:
        log_to_gui(f"Error loading stylesheet: {e}", "error")

    # Initialize the main window
    window = DriverSyncApp()
    window.show()

    # Start the GUI event loop
    sys.exit(app.exec_())