import csv

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QHeaderView, QFileDialog, QLabel, 
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QBrush, QLinearGradient, QPalette

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

        # Apply gradient to the log table
        gradient = QLinearGradient(0, 0, 0, self.log_table.height())
        gradient.setColorAt(0.0, QColor(255, 255, 255))  # White
        gradient.setColorAt(1.0, QColor(230, 230, 230))  # Light Grey

        palette = QPalette()
        palette.setBrush(QPalette.Base, QBrush(gradient))
        self.log_table.setPalette(palette)

        # Style adjustments to make grid lines grey and table more embedded
        self.log_table.setGridStyle(Qt.SolidLine)
        self.log_table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 white, stop:1 #e6e6e6);
                border: none;
                gridline-color: #D3D3D3; /* Light grey grid lines */
                alternate-background-color: #F8F8F8; /* Slightly off-white for contrast */
            }
            QHeaderView::section {
                background-color: #EAEAEA; /* Light grey header */
                border: none;
                padding: 4px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #E0E0E0; /* Soft embedded row separation */
                padding: 5px;
            }
        """)


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
        """Refresh the log table to display logs with rounded labels for log levels."""
        self.log_table.setUpdatesEnabled(False)
        current_scroll_value = self.log_table.verticalScrollBar().value()
        max_scroll_value = self.log_table.verticalScrollBar().maximum()

        self.log_table.setRowCount(0)
        for log in self.logs:
            if self.passes_filter(log):
                row_position = self.log_table.rowCount()
                self.log_table.insertRow(row_position)

                # Set log level as a styled label
                level_widget = self.create_level_label(log["level"])
                self.log_table.setCellWidget(row_position, 0, level_widget)

                # Set message
                self.log_table.setItem(row_position, 1, QTableWidgetItem(log["message"]))

                # Set row height for each row
                self.log_table.setRowHeight(row_position, 30)  # Adjust height as needed

        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed) 
        self.log_table.setColumnWidth(0, 120)  # Width for level column
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Stretch message column

        self.log_table.verticalHeader().setDefaultSectionSize(30)  # Height for each row

        self.log_table.setUpdatesEnabled(True)
        if current_scroll_value == max_scroll_value:
            self.log_table.scrollToBottom()



    def create_level_label(self, level):
        """Create a rounded QLabel for log levels with colored backgrounds."""
        label = QLabel(level)
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(80, 25)  # Adjust label size
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.get_level_background(level)};
                color: white;
                font-weight: bold;
                border-radius: 12px;
                padding: 4px;
            }}
        """)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(label)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        widget.setLayout(layout)

        return widget

    def get_level_background(self, level):
        """Return the appropriate background color for the log level."""
        colors = {
            "Info": "#3498db",    # Blue
            "Success": "#2ecc71", # Green
            "Warning": "#f39c12", # Orange
            "Error": "#e74c3c"    # Red
        }
        return colors.get(level, "#95a5a6")  # Default: Grey


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
