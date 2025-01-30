from pathlib import Path
import time
from datetime import datetime
import zipfile
import json
from _logging import log_to_gui

class BackupManager:
    CONFIG_FILE = Path("config.json")

    def __init__(self, log_func=None):
        self.log_file = Path("backup.log")
        self.log_to_gui = log_func

    def log(self, message, level="info", html=False, to_gui=True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level.upper()}] {message}"

        # Write to the log file
        with self.log_file.open("a") as log_file:
            log_file.write(entry + "\n")

        # Send log messages to the GUI, if applicable
        if self.log_to_gui and to_gui:
            if html:
                self.log_to_gui(message, level, html=True)
            else:
                self.log_to_gui(entry, level)

    def create_backup_zip(self, files, backup_folder, log_func=None, retention_days=None):
        """
        Creates a backup zip file and removes old backups based on retention settings.

        Args:
            files (list): Paths to files to include in the backup.
            backup_folder (str or Path): Destination folder for backups.
            log_func (function, optional): Optional logging function.
            retention_days (int, optional): Number of days to keep backups.
        """
        backup_folder = Path(backup_folder)
        backup_folder.mkdir(parents=True, exist_ok=True)

        # Create a unique zip file name based on the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_zip_path = backup_folder / f"backup_{timestamp}.zip"

        try:
            with zipfile.ZipFile(backup_zip_path, "w") as backup_zip:
                for file_path in files:
                    file_path = Path(file_path)
                    if file_path.exists():
                        backup_zip.write(file_path, arcname=file_path.name)
                    else:
                        if log_func:
                            log_func(f"File not found: {file_path}", "warning")
            if log_func:
                log_func(f"Backup created: {backup_zip_path}", "info", to_gui=False)
        except IOError as e:
            raise IOError(f"Error creating backup zip: {e}")

        # Handle retention policy
        if retention_days is None:
            retention_days = self._get_retention_days(log_func)
        self._cleanup_old_backups(backup_folder, retention_days, log_func)

        return backup_zip_path

    def _cleanup_old_backups(self, backup_folder, retention_days, log_func=None):
        """
        Removes backups older than the specified retention period.

        Args:
            backup_folder (Path): Folder containing backup files.
            retention_days (int): Retention period in days.
            log_func (function): Optional logging function.
        """
        retention_seconds = retention_days * 86400  # Convert days to seconds
        current_time = time.time()

        for backup_file in Path(backup_folder).iterdir():
            if backup_file.is_file():
                file_age = current_time - backup_file.stat().st_mtime
                if file_age > retention_seconds:
                    backup_file.unlink()
                    if log_func:
                        log_func(f"Removed old backup: {backup_file}", "info")

    def _get_retention_days(self, log_func=None):
        """
        Retrieves the retention period from the config file or defaults to 5 days.

        Args:
            log_func (function): Optional logging function.

        Returns:
            int: Retention period in days.
        """
        try:
            if self.CONFIG_FILE.exists():
                with self.CONFIG_FILE.open("r") as file:
                    config = json.load(file)
                    return config.get("backup_retention_days", 5)
            else:
                if log_func:
                    log_func(f"Config file '{self.CONFIG_FILE}' not found. Defaulting to 5 days.", "warning", to_gui=False)
                return 5
        except Exception as e:
            if log_func:
                log_func(f"Error reading retention days: {e}", "error")
            return 5
