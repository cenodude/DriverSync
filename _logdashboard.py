import csv

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QHeaderView, QFileDialog, QLabel
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

class LogDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.logs = []  # Placeholder for logs

        # Main Layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Log Table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(2)
        self.log_table.setHorizontalHeaderLabels(["Level", "Message"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Level column
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Message column
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.verticalHeader().setDefaultSectionSize(20)  # Set compact row height
        self.main_layout.addWidget(self.log_table)

        # Control Panel
        self.control_panel = QHBoxLayout()
        self.main_layout.addLayout(self.control_panel)

        # Log Level Filter
        self.filter_label = QLabel("Filter by Level:")
        self.control_panel.addWidget(self.filter_label)

        self.log_level_filter = QComboBox()
        self.log_level_filter.addItems(["All", "Info", "Success", "Warning", "Error"])
        self.log_level_filter.currentIndexChanged.connect(self.filter_logs)
        self.control_panel.addWidget(self.log_level_filter)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search logs...")
        self.search_bar.textChanged.connect(self.filter_logs)
        self.control_panel.addWidget(self.search_bar)

        # Clear Logs Button
        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        self.control_panel.addWidget(self.clear_button)

        # Export Logs Button
        self.export_button = QPushButton("Export Logs")
        self.export_button.clicked.connect(self.export_logs)
        self.control_panel.addWidget(self.export_button)

        # Timer for real-time updates (if needed)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_log_table)
        self.timer.start(1000)  # Example: Update every second

    def add_log(self, level, message):
        """Add a new log entry to the dashboard."""
        if level == "Debug":
            return  # Skip debug messages

        new_log = {
            "level": level,
            "message": message
        }
        self.logs.append(new_log)
        self.refresh_log_table()

    def refresh_log_table(self):
        """Refresh the log table to display logs."""
        self.log_table.setUpdatesEnabled(False)  # Temporarily disable updates for performance
        current_scroll_value = self.log_table.verticalScrollBar().value()
        max_scroll_value = self.log_table.verticalScrollBar().maximum()

        self.log_table.setRowCount(0)
        for log in self.logs:
            if self.passes_filter(log):
                row_position = self.log_table.rowCount()
                self.log_table.insertRow(row_position)

                # Set level with color coding
                level_item = QTableWidgetItem(log["level"])
                level_color = self.get_level_color(log["level"])
                level_item.setForeground(level_color)
                self.log_table.setItem(row_position, 0, level_item)

                # Set message
                self.log_table.setItem(row_position, 1, QTableWidgetItem(log["message"]))

        self.log_table.setUpdatesEnabled(True)  # Re-enable updates
        if current_scroll_value == max_scroll_value:  # If already scrolled to the bottom
            self.log_table.scrollToBottom()  # Keep it scrolled

    def get_level_color(self, level):
        """Return the appropriate color for the log level."""
        colors = {
            "Info": QColor("blue"),
            "Success": QColor("green"),
            "Warning": QColor("orange"),
            "Error": QColor("red")
        }
        return colors.get(level, QColor("black"))

    def passes_filter(self, log):
        """Check if a log passes the current filter criteria."""
        level_filter = self.log_level_filter.currentText()
        search_text = self.search_bar.text().lower()

        if level_filter != "All" and log["level"] != level_filter:
            return False

        if search_text and search_text not in log["message"].lower():
            return False

        return True

    def filter_logs(self):
        """Filter logs based on the selected level and search text."""
        self.refresh_log_table()

    def clear_logs(self):
        """Clear all logs from the table."""
        self.logs = []
        self.refresh_log_table()

    def export_logs(self):
        """Export logs to a CSV file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Logs", "", "CSV Files (*.csv);;All Files (*)", options=options)

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Level", "Message"])  # CSV Header
                    for log in self.logs:
                        writer.writerow([log["level"], log["message"]])
                self.add_log("Success", f"Logs successfully exported to: {file_path}")
            except Exception as e:
                print(f"Error exporting logs: {e}")
