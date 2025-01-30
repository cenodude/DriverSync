from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import QTimer


def log_to_gui(instance, message, level="info", bold=False, include_timestamp=False, html=False, to_file=True):
    """
    Logs a message to the GUI dashboard and optionally to a file.
    The 'instance' parameter refers to the caller object.
    """
    # Generate the log message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if include_timestamp else ""
    full_message = f"{timestamp} {message}".strip()

    # Define basic colors for message levels
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
    if hasattr(instance, "log_dashboard") and instance.log_dashboard is not None:
        QTimer.singleShot(0, lambda: instance.log_dashboard.add_log(level.capitalize(), full_message))

    # Write to the log file if enabled
    if to_file:
        try:
            _log_to_file(full_message, level)
        except Exception as e:
            # Log the error only to the file if writing fails
            _log_to_file(f"[ERROR] Failed to write to log file: {e}", "error")


def _log_to_file(message, level):
    """
    Appends a log entry to the log file with a timestamp and level.
    Ensures the log file is stored in a Logs directory.
    """
    log_file = initialize_log_file()

    # Prepare the log entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level.upper()}] {message}"

    # Write to the log file
    with log_file.open("a") as file:
        file.write(log_entry + "\n")


def initialize_log_file(log_folder="Logs", log_file_name="DriverSync.log"):
    """
    Ensures the Logs directory and log file exist.
    Returns the path to the log file.
    """
    log_folder_path = Path(log_folder)
    log_folder_path.mkdir(parents=True, exist_ok=True)  # Create directory if not exists
    return log_folder_path / log_file_name