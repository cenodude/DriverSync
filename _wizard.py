import sys
import json

from PyQt5.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QComboBox, QSpinBox, QListWidget, QListWidgetItem, QTextEdit,
    QFileDialog, QMessageBox, QApplication, QFormLayout, QHBoxLayout, QFrame,
    QDialog, QTextBrowser, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices, QIcon, QColor

from pathlib import Path
from _driversync_logics import DriverSync
from _driversync_logics import get_onedrive_documents_path

# Wizard doesnt use the cental logging function, enable to print log to console
ENABLE_CONSOLE_LOGGING = False

# Needed for PyInstaller...i think
def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller bundles."""
    from pathlib import Path
    base_path = getattr(sys, '_MEIPASS', Path(__file__).parent)
    return Path(base_path) / relative_path

def default_log_to_gui(message, level="info"):
    """Default logging function if log_to_gui is not set in DriverSync."""
    if ENABLE_CONSOLE_LOGGING:
        print(f"[{level.upper()}] {message}")

class MarkdownHelpDialog(QDialog):
    def __init__(self, markdown_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help - DriverSync")
        self.resize(850, 600)

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

class CategoryListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)

    def dropEvent(self, event):
        """Handle the drop event."""
        if event.source() != self:
            # Transfer the item to the target list
            item = event.source().takeItem(event.source().currentRow())
            self.addItem(item)
            event.accept()
        else:
            super().dropEvent(event)

class DriverSyncWizard(QWizard):
    def __init__(self, auto_mode=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DriverSync Setup Wizard")
        self.setWindowIcon(QIcon(str(resource_path("sync.ico"))))
        self.resize(850, 575)

        # Auto mode flag
        self.auto_mode = auto_mode

        # Help connection
        self.button(QWizard.HelpButton).clicked.connect(self.open_help_dialog)

        # Load theme
        self.load_stylesheet(resource_path("light_theme.css"))

        # Initialize DriverSync
        self.synchronizer = DriverSync(log_to_gui=default_log_to_gui)

        # Initialize attributes
        self.ioverlay_input = QLineEdit()
        self.crewchief_input = QLineEdit()
        self.ioverlay_status = QLabel()
        self.crewchief_status = QLabel()
        self.backup_checkbox = QCheckBox("Enable Backup")
        self.retention_spinbox = QSpinBox()
        self.sync_behavior_combo = QComboBox()
        self.summary_text = QTextEdit()
        self.excluded_list = CategoryListWidget()
        self.included_list = CategoryListWidget()

        # Add pages
        self.addPage(self.create_intro_page())
        self.addPage(self.create_pathnames_page())
        self.addPage(self.create_settings_page())
        self.addPage(self.create_categories_page())
        self.addPage(self.create_summary_page())

        # Configure button layout and behavior
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        self.setButtonLayout([
            QWizard.HelpButton,
            QWizard.BackButton,
            QWizard.CancelButton,
            QWizard.NextButton,
            QWizard.FinishButton,
        ])
        self.button(QWizard.FinishButton).setText("Finish")
        self.button(QWizard.FinishButton).clicked.connect(self.complete_setup)

        # Set behavior for Cancel/Exit button
        self.button(QWizard.CancelButton).clicked.connect(self.handle_exit)

        # Set default paths and validate
        self.search_default_paths()

    def handle_exit(self):
        """
        Handle the exit action based on whether the wizard is in auto_mode or manual mode.
        """
        if self.auto_mode:
            # If invoked automatically, exit without saving and terminate the application
            QMessageBox.information(
                self, "Exit", "You’re exiting the wizard before completing it. To start again, please open it from the settings menu."
            )
            sys.exit(0)  # Terminate the application
        else:
            # If invoked manually, exit without saving and return to DriverSync
            QMessageBox.information(self, "Exit", "Exiting without saving changes.")
            self.close()

    def complete_setup(self):
        """
        Complete the setup process, save the configuration, and exit the wizard.
        """
        try:
            # Save the configuration and close the wizard
            self.synchronizer.save_config()
            QMessageBox.information(self, "Setup Complete", "Configuration saved successfully!")
            self.accept()  # Close the wizard
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")


    def load_stylesheet(self, stylesheet_path):
        """Load and apply a stylesheet to the wizard."""
        try:
            with open(stylesheet_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        except FileNotFoundError:
            default_log_to_gui(f"Stylesheet {stylesheet_path} not found. Using default theme.", "warning")

    def search_default_paths(self):
        """Retrieve default paths for iOverlay and CrewChief, handling OneDrive localization and folder existence."""
        try:
            defaults = self.synchronizer.get_default_paths()

            # iOverlay Path
            if defaults[0] and Path(defaults[0]).exists():
                self.ioverlay_input.setText(str(defaults[0]))
                self.ioverlay_status.setText('<span style="color:green; font-weight:bold;">✔ Successfully retrieved</span>')
                self.populate_categories()  # Load categories from the default settings.dat

            # CrewChief Path
            if defaults[1] and Path(defaults[1]).exists():
                self.crewchief_input.setText(str(defaults[1]))
                self.crewchief_status.setText('<span style="color:green; font-weight:bold;">✔ Successfully retrieved</span>')
            else:
                # Attempt to create the CrewChief path if it doesn't exist
                crewchief_path = Path(defaults[1])
                crewchief_path.parent.mkdir(parents=True, exist_ok=True)
                if not crewchief_path.exists():
                    with open(crewchief_path, "w", encoding="utf-8") as f:
                        json.dump([], f)
                self.crewchief_input.setText(str(defaults[1]))
                self.crewchief_status.setText('<span style="color:orange; font-weight:bold;">✘ Created iracing_reputations.json</span>')

            # Validate paths to set button state
            self.validate_paths()

        except Exception as e:
            # Handle unexpected errors
            default_log_to_gui(f"Error retrieving default paths: {e}", "error")

    def open_help_dialog(self):
        """Open the help dialog."""
        help_path = resource_path("DriverSync_README.md")
        dialog = MarkdownHelpDialog(markdown_path=help_path, parent=self)
        dialog.exec_()

    def create_intro_page(self):
        """Step 1: Introduction"""
        page = QWizardPage()
        page.setTitle("Welcome to DriverSync Setup")
        page.setSubTitle("Seamlessly synchronize and manage your driver data.")

        # Main Layout
        layout = QVBoxLayout()

        # Title Section
        title_label = QLabel("Welcome to DriverSync")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #007BFF;
            }
        """)
        layout.addWidget(title_label)

        # Animated Subtitle
        subtitle_label = QLabel("The ultimate synchronization tool for iOverlay and CrewChief.")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #555555;
            }
        """)
        layout.addWidget(subtitle_label)

        # Key Features
        features_label = QLabel("""
            <div style='text-align:left; font-size: 16px; color: #333333;'>
                <strong>Key Features:</strong>
                <ul style='margin: 10px 0; padding-left: 20px; list-style-type: none;'>
                    <li>✔ Different Sync Behaviors - Additive or Bidirectional</li>
                    <li>✔ Driver Editor for Custom Profiles</li>
                    <li>✔ Backup Support - Ensures data safety by retaining previous configurations</li>
                    <li>✔ Delta Reporting and Preview Mode</li>
                    <br>
                </ul>
            </div>
        """)
        features_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(features_label)

        # Add Spacer
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # GitHub Section
        github_section = QHBoxLayout()
        github_label = QLabel("Love DriverSync?")
        github_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #555555;
            }
        """)
        github_section.addWidget(github_label)

        github_button = QPushButton("⭐ Star us on GitHub!")
        github_button.setStyleSheet("""
            QPushButton {
                background-color: #0366D6;
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        github_button.setCursor(Qt.PointingHandCursor)
        github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/cenodude/DriverSync")))
        github_section.addWidget(github_button)
        github_section.addStretch()
        layout.addLayout(github_section)


        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        # Disclaimer Section
        disclaimer_label = QLabel("""
            <div style="font-size: 14px; color: #555555; margin-top: 10px;">
                <strong>Disclaimer</strong><br>
                DriverSync is an independent, third-party tool not affiliated with or supported by iOverlay, 
                CrewChief, or their respective owners. Use it at your own risk. No warranty is provided, and the 
                author assumes no responsibility for any damages or issues arising from its use.<br><br>
                <em>Note:</em> The Windows executable was created using PyInstaller, which may cause antivirus 
                programs to flag it as a threat. This is a false positive. Please whitelist the executable or 
                consider using the Python version.
            </div>
        """)
        disclaimer_label.setTextFormat(Qt.RichText)
        disclaimer_label.setWordWrap(True)
        layout.addWidget(disclaimer_label)

        page.setLayout(layout)
        return page

    def create_pathnames_page(self):
        """Step 2: File Path Selection with Explanations."""
        class PathnamesPage(QWizardPage):
            def __init__(self, parent):
                super().__init__(parent)
                self.wizard = parent

                self.setTitle("Set Up File Paths")
                self.setSubTitle("Specify the paths for iOverlay and CrewChief files.")

                layout = QVBoxLayout()
                layout.setSpacing(15)
                layout.setContentsMargins(20, 20, 20, 20)

                # iOverlay Section
                ioverlay_label = QLabel("📂 iOverlay Configuration")
                ioverlay_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
                layout.addWidget(ioverlay_label)

                ioverlay_selector = QFormLayout()
                ioverlay_selector.setVerticalSpacing(8)
                ioverlay_selector.addRow(
                    "iOverlay Path:",
                    self.wizard.create_path_selector(
                        self.wizard.ioverlay_input,
                        self.wizard.browse_ioverlay,
                        self.wizard.ioverlay_status
                    ),
                )
                layout.addLayout(ioverlay_selector)

                ioverlay_explanation = QLabel(
                    "DriverSync requires the <code>settings.dat</code> file in the iOverlay folder for synchronization. "
                    "Please select the folder containing this file."
                )
                ioverlay_explanation.setStyleSheet("font-size: 12px; color: #555555;")
                ioverlay_explanation.setWordWrap(True)
                layout.addWidget(ioverlay_explanation)

                # CrewChief Section
                crewchief_label = QLabel("📂 CrewChief Configuration")
                crewchief_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF; margin-top: 10px;")
                layout.addWidget(crewchief_label)

                crewchief_selector = QFormLayout()
                crewchief_selector.setVerticalSpacing(8)
                crewchief_selector.addRow(
                    "CrewChief Path:",
                    self.wizard.create_path_selector(
                        self.wizard.crewchief_input,
                        self.wizard.browse_crewchief,
                        self.wizard.crewchief_status
                    ),
                )
                layout.addLayout(crewchief_selector)

                crewchief_explanation = QLabel(
                    "DriverSync looks for the <code>iracing_reputations.json</code> file in the CrewChief folder. "
                    "If not found, DriverSync will create it automatically."
                )
                crewchief_explanation.setStyleSheet("font-size: 12px; color: #555555;")
                crewchief_explanation.setWordWrap(True)
                layout.addWidget(crewchief_explanation)

                layout.addStretch()  # Add stretch at the bottom for spacing
                self.setLayout(layout)

                # Connect validation signals
                self.wizard.ioverlay_input.textChanged.connect(self.on_paths_changed)
                self.wizard.crewchief_input.textChanged.connect(self.on_paths_changed)

            def isComplete(self):
                """Control the Next button state."""
                return self.wizard.validate_paths()

            def on_paths_changed(self):
                """Emit signal to update the Next button state."""
                self.completeChanged.emit()

        return PathnamesPage(self)


    def validate_paths_for_next(self):
        """
        Validate paths when transitioning from Step 2 to Step 3.
        Ensures both paths are valid; otherwise, prevents the transition.
        """
        valid = self.validate_paths()  # Call the validation method

        if not valid:
            return False  # Explicitly return False if validation fails

        return True  # Explicitly return True if validation passes

    def create_path_selector(self, input_field, browse_function, status_label):
        """Create a path selector with a line edit, browse button, and status."""
        container = QVBoxLayout()
        input_container = QHBoxLayout()

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(browse_function)
        input_container.addWidget(input_field)
        input_container.addWidget(browse_button)

        container.addLayout(input_container)
        container.addWidget(status_label)
        return container

    def browse_ioverlay(self):
        """Browse for the iOverlay folder, ensuring the settings.dat file is selected."""
        current_path = self.ioverlay_input.text().strip()
        start_path = Path(current_path).parent if current_path else Path(get_onedrive_documents_path())
        folder = QFileDialog.getExistingDirectory(self, "Select iOverlay Folder", str(start_path))
        if folder:
            file_path = Path(folder) / "settings.dat"
            self.ioverlay_input.setText(str(file_path))
            if file_path.exists():
                self.ioverlay_status.setText('<span style="color:green; font-weight:bold;">✔ settings.dat found</span>')
                try:
                    self.populate_categories()  # Reload categories when a valid file is selected
                except Exception as e:
                    self.ioverlay_status.setText('<span style="color:red; font-weight:bold;">✘ Error loading categories</span>')
                    print(f"Error loading categories: {e}")
            else:
                self.ioverlay_status.setText('<span style="color:orange; font-weight:bold;">✘ settings.dat not found</span>')

        # Validate paths and emit completeChanged signal
        self.validate_paths()
        self.page(self.currentId()).completeChanged.emit()


    def browse_crewchief(self):
        """Browse for the CrewChief folder, ensuring iracing_reputations.json is valid or created."""
        folder = QFileDialog.getExistingDirectory(self, "Select CrewChief Folder", str(Path.home()))
        if folder:
            file_path = Path(folder) / "iracing_reputations.json"
            self.crewchief_input.setText(str(file_path))

            if not file_path.exists():
                # Create the file with an empty array
                file_path.parent.mkdir(parents=True, exist_ok=True)
                if self.write_json_file(file_path, []):
                    self.crewchief_status.setText('<span style="color:green; font-weight:bold;">iracing_reputations.json created.</span>')
            else:
                # Validate the existing file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        json.load(f)  # Ensure valid JSON
                    self.crewchief_status.setText('<span style="color:green; font-weight:bold;">iracing_reputations.json validated</span>')
                except json.JSONDecodeError:
                    if self.write_json_file(file_path, []):
                        self.crewchief_status.setText('<span style="color:red; font-weight:bold;">Invalid JSON repaired with []</span>')

    def get_default_paths(self):
        """Retrieve default paths for iOverlay and CrewChief."""
        profile = os.environ.get("USERPROFILE", "")
        ioverlay = os.path.join(profile, "AppData", "Roaming", "iOverlay", "settings.dat")
        crewchief = os.path.join(profile, "Documents", "CrewChiefV4", "iracing_reputations.json")
        return ioverlay, crewchief


    def validate_paths(self):
        """Validate the paths selected or retrieved for iOverlay and CrewChief."""
        ioverlay_path = Path(self.ioverlay_input.text().strip())
        crewchief_path = Path(self.crewchief_input.text().strip())

        valid = True

        # Validate iOverlay Path
        if not ioverlay_path.exists() or ioverlay_path.name != "settings.dat":
            self.ioverlay_status.setText('<span style="color:red; font-weight:bold;">✘ Invalid iOverlay path</span>')
            valid = False
        else:
            self.ioverlay_status.setText('<span style="color:green; font-weight:bold;">✔ iOverlay path is valid</span>')

        # Validate CrewChief Path
        crewchief_folder = crewchief_path.parent
        if not crewchief_folder.exists() or crewchief_path.name != "iracing_reputations.json":
            self.crewchief_status.setText('<span style="color:red; font-weight:bold;">✘ Invalid CrewChief path</span>')
            valid = False
        else:
            self.crewchief_status.setText('<span style="color:green; font-weight:bold;">✔ CrewChief path is valid</span>')

        return valid

    def validate_paths_for_next(self):
        """
        Validate paths before enabling the Next button.
        """
        return self.validate_paths()

    def create_settings_page(self):
        """Step 3: General Settings"""
        page = QWizardPage()
        page.setTitle("General Settings")
        page.setSubTitle("Configure backup, synchronization, and application behavior.")

        layout = QVBoxLayout()

        # General Settings Section
        general_settings_label = QLabel("🔧 General Settings")
        general_settings_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        layout.addWidget(general_settings_label)

        self.minimize_to_tray_checkbox = QCheckBox("Minimize to System Tray")
        self.minimize_to_tray_checkbox.setChecked(False)  # Default to disabled
        minimize_to_tray_explanation = QLabel(
            "When enabled, DriverSync will minimize to the system tray instead of closing. "
            "You can restore it by double-clicking the tray icon."
        )
        minimize_to_tray_explanation.setStyleSheet("font-size: 12px; color: #555555;")
        minimize_to_tray_explanation.setWordWrap(True)

        layout.addWidget(self.minimize_to_tray_checkbox)
        layout.addWidget(minimize_to_tray_explanation)

        # Add spacer after General Settings
        layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Backup Section
        backup_label = QLabel("📦 Backup Settings")
        backup_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        layout.addWidget(backup_label)

        backup_section = QFormLayout()
        self.backup_checkbox = QCheckBox("Enable Backup")
        self.backup_checkbox.setChecked(True)
        self.retention_spinbox = QSpinBox()
        self.retention_spinbox.setRange(1, 30)
        self.retention_spinbox.setValue(5)
        backup_section.addRow("Enable Backup:", self.backup_checkbox)
        backup_section.addRow("Backup Retention Days:", self.retention_spinbox)
        layout.addLayout(backup_section)

        backup_explanation = QLabel(
            "Backups create a copy of your configuration and driver data before synchronization, "
            "allowing you to restore in case of issues."
        )
        backup_explanation.setStyleSheet("font-size: 12px; color: #555555;")
        backup_explanation.setWordWrap(True)
        layout.addWidget(backup_explanation)

        # Add spacer after Backup Section
        layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Sync Behavior Section
        sync_label = QLabel("🔄 Synchronization Settings")
        sync_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        layout.addWidget(sync_label)

        sync_behavior_section = QFormLayout()
        self.sync_behavior_combo = QComboBox()
        self.sync_behavior_combo.addItems(["Additive Only (Recommended)", "Bidirectional"])
        sync_behavior_section.addRow("Sync Behavior:", self.sync_behavior_combo)

        self.update_existing_checkbox = QCheckBox("Update Existing Entries")
        self.update_existing_checkbox.setChecked(False)
        update_existing_explanation = QLabel(
            "Enable this option to update details of existing entries during synchronization."
        )
        update_existing_explanation.setStyleSheet("font-size: 12px; color: #555555;")
        update_existing_explanation.setWordWrap(True)

        layout.addLayout(sync_behavior_section)
        layout.addWidget(self.update_existing_checkbox)
        layout.addWidget(update_existing_explanation)

        # Add spacer at the bottom
        layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))

        page.setLayout(layout)
        return page

    def create_categories_page(self):
        """Step 4: Select Categories with two-box approach and proper alignment."""
        page = QWizardPage()
        page.setTitle("Select Categories")
        page.setSubTitle("Manage and categorize drivers for synchronization.")

        layout = QVBoxLayout()

        # iOverlay Section
        ioverlay_label = QLabel("📂 iOverlay Categories")
        ioverlay_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        layout.addWidget(ioverlay_label)

        ioverlay_explanation = QLabel(
            "Select the categories from iOverlay to synchronize with CrewChief. "
        )
        ioverlay_explanation.setStyleSheet("font-size: 12px; color: #555555;")
        ioverlay_explanation.setWordWrap(True)
        layout.addWidget(ioverlay_explanation)

        # Add a spacer to create additional space between the label and the boxes
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        ioverlay_boxes_layout = QHBoxLayout()

        # Left box (Not Synced)
        ioverlay_left_box_layout = QVBoxLayout()
        ioverlay_left_label = QLabel("Not Synced")
        ioverlay_left_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #102a43;")
        self.not_synced_list = CategoryListWidget()
        ioverlay_left_box_layout.addWidget(ioverlay_left_label)
        ioverlay_left_box_layout.addWidget(self.not_synced_list)
        ioverlay_boxes_layout.addLayout(ioverlay_left_box_layout)

        # Arrow buttons layout
        ioverlay_arrow_layout = QVBoxLayout()
        self.move_right_button = QPushButton("→")
        self.move_right_button.clicked.connect(lambda: self.move_category(self.not_synced_list, self.synced_list))
        self.move_left_button = QPushButton("←")
        self.move_left_button.clicked.connect(lambda: self.move_category(self.synced_list, self.not_synced_list))
        ioverlay_arrow_layout.addStretch()
        ioverlay_arrow_layout.addWidget(self.move_right_button)
        ioverlay_arrow_layout.addWidget(self.move_left_button)
        ioverlay_arrow_layout.addStretch()
        ioverlay_boxes_layout.addLayout(ioverlay_arrow_layout)

        # Right box (Synced)
        ioverlay_right_box_layout = QVBoxLayout()
        ioverlay_right_label = QLabel("Synced")
        ioverlay_right_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #102a43;")
        self.synced_list = CategoryListWidget()
        ioverlay_right_box_layout.addWidget(ioverlay_right_label)
        ioverlay_right_box_layout.addWidget(self.synced_list)
        ioverlay_boxes_layout.addLayout(ioverlay_right_box_layout)

        layout.addLayout(ioverlay_boxes_layout)

        # Add a spacer between sections
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # CrewChief Section
        crewchief_label = QLabel("🎧 CrewChief")
        crewchief_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007BFF;")
        layout.addWidget(crewchief_label)

        crewchief_explanation = QLabel(
            "CrewChief synchronization ensures that the drivers marked in CrewChief align with iOverlay."
        )
        crewchief_explanation.setStyleSheet("font-size: 12px; color: #555555;")
        crewchief_explanation.setWordWrap(True)
        layout.addWidget(crewchief_explanation)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        # Explanation below the divider
        final_explanation_label = QLabel(
            "<i>Use the arrows to organize your driver categories. "
            "Categories in the 'Not Synced' list won't be synced.</i>"
        )
        final_explanation_label.setWordWrap(True)
        final_explanation_label.setStyleSheet("color: #334e68; font-size: 14px;")
        layout.addWidget(final_explanation_label)

        # Add a final spacer to align content at the top
        layout.addStretch()

        # Populate categories (initial load)
        self.populate_categories()

        page.setLayout(layout)
        return page


    def populate_categories(self):
        """Load and display categories based on the current iOverlay settings.dat."""
        self.not_synced_list.clear()
        self.synced_list.clear()
        try:
            settings_path = Path(self.ioverlay_input.text().strip())
            if settings_path.exists():
                categories = self.synchronizer.load_categories()  # Load categories from settings.dat
                for category in categories:
                    item = QListWidgetItem(category.get("name", "Unknown Category"))
                    if category.get("name") == "CrewChief":  # Pre-select CrewChief category
                        self.synced_list.addItem(item)
                    else:
                        self.not_synced_list.addItem(item)
            else:
                print("settings.dat file not found. Categories cannot be loaded.")
        except Exception as e:
            print(f"Error populating categories: {e}")


    def update_categories_ui(self, categories):
        """Update the categories UI with the given categories."""
        self.not_synced_list.clear()
        self.synced_list.clear()
        for category in categories:
            item = QListWidgetItem(category.get("name", "Unknown Category"))
            if category.get("name") == "CrewChief":  # Pre-select CrewChief category
                self.synced_list.addItem(item)
            else:
                self.not_synced_list.addItem(item)

    def move_category(self, source_list, target_list):
        """Move selected items from source list to target list."""
        selected_items = source_list.selectedItems()
        for item in selected_items:
            target_list.addItem(source_list.takeItem(source_list.row(item)))

    def create_summary_page(self):
        """Step 5: Summary with dynamic collapsible panels."""
        page = QWizardPage()
        page.setTitle("Summary")
        page.setSubTitle("Review your settings before completing the setup.")

        # Mark this as the final page
        page.setFinalPage(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create collapsible panels for different sections
        panels = [
            self.create_collapsible_panel("⚙️ General Settings", [
                f"Minimize to Tray: {'Enabled' if self.minimize_to_tray_checkbox.isChecked() else 'Disabled'}",
                f"Backup Enabled: {'Yes' if self.backup_checkbox.isChecked() else 'No'}",
                f"Backup Retention: {self.retention_spinbox.value()} days",
            ], expanded=True),
            self.create_collapsible_panel("🔄 Synchronization Settings", [
                f"Sync Behavior: {self.sync_behavior_combo.currentText()}",
                f"Update Existing Entries: {'Yes' if self.update_existing_checkbox.isChecked() else 'No'}",
            ], expanded=True),
            self.create_collapsible_panel("📂 Categories", [
                f"Synced Categories: {', '.join([self.synced_list.item(i).text() for i in range(self.synced_list.count())]) or 'None'}",
                f"Not Synced Categories: {', '.join([self.not_synced_list.item(i).text() for i in range(self.not_synced_list.count())]) or 'None'}",
            ], expanded=True),
        ]

        # Add panels to the layout
        for panel in panels:
            layout.addWidget(panel)

        # Add a stretch to align content at the top
        layout.addStretch()
        page.setLayout(layout)

        # Populate summary on entering this page
        page.initializePage = self.populate_summary
        return page

    def create_collapsible_panel(self, title, content, expanded=False):
        """Create a collapsible panel for the summary."""
        panel_frame = QFrame()
        panel_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #ddd;")
        panel_layout = QVBoxLayout()
        panel_layout.setSpacing(5)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QPushButton(title)
        header.setCheckable(True)
        header.setChecked(expanded)
        header.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
                background-color: #007BFF;
                border: none;
                padding: 10px;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #0056b3;
            }
            """
        )

        # Content Area
        content_area = QFrame()
        content_area.setStyleSheet("background-color: #f8f9fa;")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Add content as QLabel widgets
        for line in content:
            label = QLabel(line)
            label.setStyleSheet("font-size: 14px; color: #555555;")
            label.setWordWrap(True)
            content_layout.addWidget(label)

        content_area.setLayout(content_layout)
        content_area.setVisible(expanded)

        # Toggle Visibility
        header.toggled.connect(content_area.setVisible)

        # Add to Panel
        panel_layout.addWidget(header)
        panel_layout.addWidget(content_area)
        panel_frame.setLayout(panel_layout)

        return panel_frame

    def write_json_file(self, path, data):
        """Write JSON data to a file."""
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data if data is not None else [], file, indent=4)
            return True
        except Exception as e:
            print(f"Failed to write JSON file at {path}: {e}")
            return False


    def generate_section_content(self, details):
        """Generate a QLabel with section details."""
        content = QLabel(
            "<ul style='font-size: 14px; color: #555555; padding: 5px 10px; margin: 0;'>"
            + "".join(f"<li><b>{key}:</b> {value}</li>" for key, value in details.items())
            + "</ul>"
        )
        content.setWordWrap(True)
        return content


    def populate_summary(self):
        """Populate the summary with selected settings."""
        synced_categories = [self.synced_list.item(i).text() for i in range(self.synced_list.count())]
        settings = {
            "iOverlay Path": self.ioverlay_input.text(),
            "CrewChief Path": self.crewchief_input.text(),
            "Backup Enabled": "Yes" if self.backup_checkbox.isChecked() else "No",
            "Backup Retention Days": self.retention_spinbox.value(),
            "Minimize to Tray": "Yes" if self.minimize_to_tray_checkbox.isChecked() else "No",
            "Sync Behavior": self.sync_behavior_combo.currentText(),
            "Update Existing Entries": "Yes" if self.update_existing_checkbox.isChecked() else "No",
            "Categories": ", ".join(synced_categories),
        }
        self.summary_text.setText("\n".join(f"{key}: {value}" for key, value in settings.items()))


    def complete_setup(self):
        """Save the settings and close the wizard."""
        # Retrieve all categories and their states
        all_categories = [self.synced_list.item(i).text() for i in range(self.synced_list.count())] + \
                         [self.not_synced_list.item(i).text() for i in range(self.not_synced_list.count())]
        enabled_categories = {category: False for category in all_categories}
        for i in range(self.synced_list.count()):
            enabled_categories[self.synced_list.item(i).text()] = True

        # Map display labels to internal values
        sync_behavior_mapping = {
            "Additive Only (Recommended)": "Additive Only",
            "Bidirectional": "Bidirectional",
        }
        sync_behavior = sync_behavior_mapping.get(self.sync_behavior_combo.currentText(), "Additive Only")

        # Prepare settings
        settings = {
            "iOverlay Path": self.ioverlay_input.text(),
            "CrewChief Path": self.crewchief_input.text(),
            "Backup Enabled": self.backup_checkbox.isChecked(),
            "Backup Retention Days": self.retention_spinbox.value(),
            "Sync Behavior": sync_behavior,
            "Update Existing Entries": self.update_existing_checkbox.isChecked(),
            "Categories": ", ".join([k for k, v in enabled_categories.items() if v]),
        }

        # Prepare configuration for saving
        config = {
            "ioverlay_settings_path": self.ioverlay_input.text(),
            "crewchief_reputations_path": self.crewchief_input.text(),
            "minimize_to_tray": False,
            "update_existing_entries": self.update_existing_checkbox.isChecked(),
            "sync_behavior": sync_behavior,
            "backup_files": self.backup_checkbox.isChecked(),
            "backup_retention_days": self.retention_spinbox.value(),
            "scheduler_interval": None,
            "enabled_categories": enabled_categories,
        }

        # Log the settings
        default_log_to_gui("Settings saved successfully:", "info")
        for key, value in settings.items():
            default_log_to_gui(f"{key}: {value}", "info")

        # Save the configuration to file
        with open("config.json", "w") as file:
            import json
            json.dump(config, file, indent=4)

        self.accept()

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    wizard = DriverSyncWizard()
    wizard.show()
    sys.exit(app.exec_())