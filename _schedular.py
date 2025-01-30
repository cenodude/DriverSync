import threading
import schedule
import time
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from _logging import log_to_gui

class DriverSyncScheduler:

    def __init__(self, synchronizer, log_to_gui, parent=None):
        self.synchronizer = synchronizer
        self.log_to_gui = log_to_gui
        self.scheduler_thread = None
        self.running = False
        self.interval_hours = None
        self.parent = parent

    def start_scheduler(self, interval_hours):
        """
        Start the scheduler to run the synchronization task at specified intervals.

        Args:
            interval_hours (int): The interval in hours for the scheduler.
        """
        if self.running:
            self.log_to_gui("Scheduler is already running.", "info")
            return

        self.log_to_gui(f"Starting scheduler to run every {interval_hours} hour(s)...", "info")

        # Store the interval for later use
        self.interval_hours = interval_hours

        # Clear existing scheduled tasks to prevent duplicate jobs
        schedule.clear()

        # Schedule the synchronization task
        schedule.every(interval_hours).hours.do(self.run_synchronization)

        # Start the scheduler in a separate thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def run_synchronization(self):
        """
        Perform the synchronization task and log the results.
        """
        self.log_to_gui(f"Starting synchronization at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...", "info")
        try:
            success, stats = self.synchronizer.synchronize_files(dry_run=False)
            if success:
                self.log_to_gui("Scheduled synchronization completed successfully!", "success")
            else:
                self.log_to_gui("Scheduled synchronization failed.", "error")
        except Exception as e:
            self.log_to_gui(f"Error during synchronization: {e}", "error")

    def run_scheduler(self):
        """
        Run the scheduler in a loop to check and execute pending tasks.
        """
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)  # Prevent high CPU usage
        except Exception as e:
            self.log_to_gui(f"Scheduler encountered an error: {e}", "error")
        finally:
            self.log_to_gui("Scheduler stopped.", "info")

    def stop_scheduler(self):
        if not self.running:
            self.log_to_gui("Scheduler is not running.", "info")
            return

        self.log_to_gui("Stopping scheduler...", "info")
        self.running = False
        schedule.clear()

    def show_settings_dialog(self):
        dialog = SchedulerSettingsDialog(self.interval_hours, self.parent)
        if dialog.exec():
            new_interval = dialog.get_interval()
            if new_interval != self.interval_hours:
                self.stop_scheduler()
                self.start_scheduler(new_interval)

class SchedulerSettingsDialog(QDialog):
    """
    Dialog to configure scheduler settings, such as interval hours.
    """
    def __init__(self, current_interval, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scheduler Settings")
        self.resize(400, 200)
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
        layout = QVBoxLayout()

        # Interval input
        layout.addWidget(QLabel("Set Scheduler Interval (in hours):", alignment=Qt.AlignCenter))
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 24)
        self.interval_input.setValue(self.current_interval or 1)
        layout.addWidget(self.interval_input, alignment=Qt.AlignCenter)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_interval(self):
        """
        Get the interval entered by the user.

        Returns:
            int: The interval in hours.
        """
        return self.interval_input.value()
