import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
import json
from datetime import datetime
from _logging import log_to_gui


def get_analytics_file_path():
    """
    Resolve the correct path to _analytics.json based on execution context.
    """
    try:
        if hasattr(sys, '_MEIPASS'):  # PyInstaller temp directory
            base_path = Path(sys._MEIPASS)  # Directory for PyInstaller resources
        else:
            base_path = Path(__file__).parent.resolve()  # Script's directory during development

        analytics_file = base_path / "_analytics.json"
        return analytics_file
    except Exception as e:
        raise RuntimeError(f"Error resolving analytics file path: {e}")


def initialize_analytics_file():
    """
    Ensure that _analytics.json exists and is properly initialized.
    """
    try:
        file_path = get_analytics_file_path()
        if not file_path.exists():
            # print(f"Creating _analytics.json at {file_path}")
            with file_path.open("w", encoding="utf-8") as file:
                json.dump([], file)  # Initialize with an empty list
        return file_path
    except Exception as e:
        raise RuntimeError(f"Error initializing _analytics.json: {e}")



def record_analytics(analytics_record):
    """
    Records analytics data to _analytics.json.
    """
    try:
        # Ensure the file exists
        file_path = initialize_analytics_file()

        # Add timestamp if missing
        if "timestamp" not in analytics_record:
            analytics_record["timestamp"] = datetime.now().strftime("%d-%m-%Y %H:%M")

        # Load existing analytics data
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as file:
                analytics_data = json.load(file)
        else:
            analytics_data = []

        # Avoid duplicates
        if analytics_record in analytics_data:
            # print("Duplicate analytics record. Skipping.")
            return

        # Append the new record and save
        analytics_data.append(analytics_record)
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(analytics_data, file, indent=4)

        # print(f"Analytics record added: {analytics_record}")
        log_to_gui(None, f"Analytics record added: {analytics_record}", level="info", to_file=True)

    except Exception as e:
        # print(f"Failed to record analytics: {e}")
        log_to_gui(None, f"Failed to record analytics: {e}", level="error", to_file=True)
        raise

class AnalyticsOverviewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Synchronization Analytics")

        fixed_width = 950
        initial_height = 400
        self.resize(fixed_width, initial_height)

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

        self.layout = QVBoxLayout()

        self.analytics_data = self.load_analytics_data()
        # Reformat timestamps in loaded data
        self.analytics_data = self.reformat_timestamps(self.analytics_data)
        self.aggregated_data = self.aggregate_analytics_data(self.analytics_data)

        self.layout.addLayout(self.create_progress_bar("Total Added to iOverlay", "total_added_to_ioverlay"))
        self.layout.addLayout(self.create_progress_bar("Total Added to CrewChief", "total_added_to_crewchief"))
        self.layout.addLayout(self.create_progress_bar("Total Drivers in iOverlay", "total_ioverlay"))
        self.layout.addLayout(self.create_progress_bar("Total Drivers in CrewChief", "total_crewchief"))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Added to iOverlay", "Added to CrewChief", "Total iOverlay", "Total CrewChief"
        ])
        self.populate_table(self.analytics_data)

        self.table.verticalHeader().setDefaultSectionSize(20)  # Reduced row height

        self.layout.addWidget(self.table)

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        button_layout = QHBoxLayout()

        reset_button = QPushButton("Reset Analytics")
        reset_button.clicked.connect(self.reset_analytics)
        button_layout.addWidget(reset_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.adjust_window_size()

    def create_progress_bar(self, title, key):
        layout = QHBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-right: 10px;")
        title_label.setFixedWidth(200)

        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(min(self.aggregated_data[key], 100))
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 5px;
                background: #1e1e1e;
                height: 12px;
            }
            QProgressBar::chunk {
                background: #00BFFF;
            }
        """)
        progress_bar.setFixedHeight(12)

        value_label = QLabel(str(self.aggregated_data[key]))
        value_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-left: 10px;")
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(progress_bar, stretch=2)
        layout.addWidget(value_label)

        setattr(self, f"{key}_bar", progress_bar)  # Save the progress bar as an attribute
        setattr(self, f"{key}_label", value_label)  # Save the value label as an attribute

        return layout

    def load_analytics_data(self):
        """
        Load analytics data from the JSON file.
        """
        try:
            file_path = get_analytics_file_path()  # Use the helper function
            if file_path.exists():
                with file_path.open("r", encoding="utf-8") as file:
                    return json.load(file)
            return []
        except Exception as e:
            log_to_gui(None, f"Failed to load analytics data: {e}", level="error", to_file=True)
            return []

    def reformat_timestamps(self, analytics_data):
        """
        Reformat timestamps in analytics data to D-M-Y HH:MM format.
        """
        for record in analytics_data:
            if "timestamp" in record:
                try:
                    timestamp_dt = datetime.strptime(record["timestamp"], "%Y-%m-%d %H:%M:%S")  # Old format
                    record["timestamp"] = timestamp_dt.strftime("%d-%m-%Y %H:%M")  # New format
                except ValueError:
                    pass  # Skip if already in the correct format
        return analytics_data

    def aggregate_analytics_data(self, analytics_data):
        return {
            "total_added_to_ioverlay": sum(record.get("added_to_ioverlay", 0) for record in analytics_data),
            "total_added_to_crewchief": sum(record.get("added_to_crewchief", 0) for record in analytics_data),
            "total_ioverlay": max((record.get("total_ioverlay", 0) for record in analytics_data), default=0),
            "total_crewchief": max((record.get("total_crewchief", 0) for record in analytics_data), default=0),
        }

    def populate_table(self, analytics_data):
        self.table.setRowCount(len(analytics_data))
        for row, record in enumerate(analytics_data):
            self.add_table_row(row, record)

    def add_table_row(self, row, record):
        """
        Adds a row to the QTableWidget with all values centrally aligned.
        """
        items = [
            record.get("timestamp", ""),
            str(record.get("added_to_ioverlay", 0)),
            str(record.get("added_to_crewchief", 0)),
            str(record.get("total_ioverlay", 0)),
            str(record.get("total_crewchief", 0)),
        ]

        for col, value in enumerate(items):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)  # Centralize text
            self.table.setItem(row, col, item)

    def adjust_window_size(self):
        row_count = self.table.rowCount()
        row_height = self.table.verticalHeader().defaultSectionSize()
        table_height = row_count * row_height + self.table.horizontalHeader().height()

        padding = 150
        min_height = 400
        max_height = 800
        new_height = max(min_height, min(table_height + padding, max_height))

        self.resize(self.width(), new_height)

    def reset_analytics(self):
        """
        Reset analytics data by deleting the JSON file.
        """
        try:
            file_path = get_analytics_file_path()  # Use the helper function
            if file_path.exists():
                file_path.unlink()
                QMessageBox.information(self, "Reset Analytics", "All analytics data has been reset.")

            self.table.setRowCount(0)
            self.aggregated_data = self.aggregate_analytics_data([])
            self.refresh_progress_bars()
            self.adjust_window_size()

        except Exception as e:
            log_to_gui(None, f"Failed to reset analytics data: {e}", level="error", to_file=True)

    def refresh_progress_bars(self):
        """
        Refresh the progress bars to reflect reset values.
        """
        for key in ["total_added_to_ioverlay", "total_added_to_crewchief", "total_ioverlay", "total_crewchief"]:
            bar = getattr(self, f"{key}_bar", None)
            label = getattr(self, f"{key}_label", None)
            if bar and label:
                bar.setValue(0)
                label.setText("0")
