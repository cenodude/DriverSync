import re
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from pathlib import Path
import sys

def resource_path(relative_path):
    """
    Get the absolute path to a resource, compatible with PyInstaller.
    """
    base_path = getattr(sys, '_MEIPASS', Path(".").resolve())
    return str(Path(base_path) / relative_path)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About DriverSync")
        self.resize(450, 400)
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

        # Fetch version dynamically
        version = self.get_version_from_file("DriverSync.py")

        # Main Layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Section
        title_label = QLabel("DriverSync")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #007BFF;
            }
        """)
        layout.addWidget(title_label)

        version_label = QLabel(f"Version: <b>{version}</b>")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 14px; color: #555555;")
        layout.addWidget(version_label)

        developer_label = QLabel("Developed by <b>Pazzie</b>")
        developer_label.setAlignment(Qt.AlignCenter)
        developer_label.setStyleSheet("font-size: 14px; color: #555555;")
        layout.addWidget(developer_label)

        # Description Section
        description_label = QLabel(
            "DriverSync enables seamless synchronization between iOverlay and CrewChief, "
            "providing efficient data management and integration."
        )
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 12px; color: #333333;")
        layout.addWidget(description_label)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        # GitHub Section
        github_section = QHBoxLayout()
        github_label = QLabel("Love DriverSync? ♥")
        github_label.setStyleSheet("font-size: 14px; color: #555555;")
        github_section.addWidget(github_label)

        github_button = QPushButton("⭐ Star me on GitHub!")
        github_button.setCursor(Qt.PointingHandCursor)
        github_button.setStyleSheet("""
            QPushButton {
                background-color: #24292E;
                color: white;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0366D6;
            }
        """)
        github_button.clicked.connect(lambda: self.open_github())
        github_section.addWidget(github_button)
        github_section.addStretch()
        layout.addLayout(github_section)

        # Disclaimer Section
        disclaimer_label = QLabel(
            "<div style='font-size: 12px; color: #555555; text-align: justify;'>"
            "<strong>Disclaimer:</strong><br>"
            "DriverSync is an independent, third-party tool not affiliated with or supported by iOverlay, "
            "CrewChief, or their respective owners. Use it at your own risk. No warranty is provided, and the "
            "the author assumes no responsibility for any damages or issues caused by its use."
            "</div>"
        )
        disclaimer_label.setWordWrap(True)
        layout.addWidget(disclaimer_label)

        # Close Button
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    @staticmethod
    def get_version_from_file(file_path):
        """Extract the version from the specified file."""
        try:
            actual_path = resource_path(file_path)  # Adjust for PyInstaller compatibility
            with open(actual_path, "r", encoding="utf-8") as file:
                content = file.read()
            match = re.search(r"Version:\s*([\d.]+)", content)
            if match:
                return match.group(1)
            return "Unknown"
        except FileNotFoundError:
            return "File not found"
        except Exception as e:
            return f"Error: {e}"

    def open_github(self):
        """Open the GitHub repository in a web browser."""
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://github.com/cenodude/DriverSync"))
