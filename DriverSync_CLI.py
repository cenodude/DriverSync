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

from pathlib import Path
import sys
import time
import argparse
import subprocess
import json

from _driversync_logics import DriverSync
from _backup import BackupManager

ABOUT_TEXT = """
DriverSync
Version: 0.8
Developed by Pazzie
DriverSync helps synchronize data between iOverlay and CrewChief, ensuring consistency and efficiency.
GitHub Repository: https://github.com/cenodude/DriverSync
"""

CONFIG_FILE = Path("config.json")
LOGS_FOLDER = Path("Logs")
BACKUP_FOLDER = Path("Backup")
ANALYTICS_FILE = Path("analytics.json")

DEFAULT_CONFIG = {
    "ioverlay_settings_path": "",
    "crewchief_reputations_path": "",
    "backup_files": True,
    "backup_retention_days": 5,
    "minimize_to_tray": False,
    "update_existing_entries": False,
    "sync_behavior": "Additive Only",
    "scheduler_interval": None,
    "enabled_categories": {}
}

def validate_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Error: '{CONFIG_FILE}' is missing.\n"
            "Please set up the configuration using the DriverSync GUI to create a valid config.json.\n"
        )
    try:
        with CONFIG_FILE.open("r") as file:
            config = json.load(file)
            if not all(key in config for key in ["ioverlay_settings_path", "crewchief_reputations_path"]):
                raise ValueError(
                    "Invalid configuration. Missing required keys in config.json.\n"
                )
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            f"Error: '{CONFIG_FILE}' is invalid. {e}\n"
        )

def perform_backup(synchronizer):
    print("Creating backup...")
    try:
        files_to_backup = [Path(synchronizer.ioverlay_path), Path(synchronizer.crewchief_path)]
        backup_manager = BackupManager()
        backup_path = backup_manager.create_backup_zip(
            files=files_to_backup, backup_folder=BACKUP_FOLDER, log_func=synchronizer.log
        )
        print(f"Backup created successfully: {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")

def perform_sync(synchronizer):
    print("Starting synchronization...")
    try:
        success, stats = synchronizer.synchronize_files(dry_run=False)
        if success:
            print("Synchronization completed successfully.")
            print(f"Drivers added to iOverlay: {stats.get('added_to_ioverlay', 0)}")
            print(f"Drivers added to CrewChief: {stats.get('added_to_crewchief', 0)}")
        else:
            print("Synchronization failed.")
    except Exception as e:
        print(f"Error during synchronization: {e}")

def start_scheduler(synchronizer, interval):
    import schedule

    def job():
        print("Running scheduled synchronization...")
        perform_sync(synchronizer)

    print(f"Starting scheduler with an interval of {interval} hour(s).")
    schedule.every(interval).hours.do(job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped.")

def run_in_background(script_args):
    script_path = sys.executable if getattr(sys, "frozen", False) else Path(__file__)
    subprocess.Popen(
        [str(script_path)] + script_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    print("DriverSync CLI is running in the background.")

def reset_config():
    """
    Deletes the configuration file (config.json) to reset the application to its default state.
    """
    print("Resetting configuration...")
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        print("Configuration reset successfully (config.json deleted).")
    else:
        print("Configuration file not found. No reset needed.")

def show_analytics():
    if not ANALYTICS_FILE.exists():
        print("No analytics data found.")
        return

    with ANALYTICS_FILE.open("r") as file:
        analytics_data = json.load(file)

    if not analytics_data:
        print("No analytics data found.")
        return

    latest_record = analytics_data[-1]
    print("Latest Synchronization Analytics:")
    print(f"  Total Drivers in iOverlay: {latest_record['total_ioverlay']}")
    print(f"  Total Drivers in CrewChief: {latest_record['total_crewchief']}")

def show_about():
    print(ABOUT_TEXT)

def main():
    parser = argparse.ArgumentParser(description="DriverSync Helper CLI", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--sync", action="store_true", help="Perform synchronization based on config.json settings.")
    parser.add_argument("--backup", action="store_true", help="Create a backup of the iOverlay and CrewChief files.")
    parser.add_argument("--about", action="store_true", help="Display information about DriverSync, including version and GitHub link.")
    parser.add_argument("--scheduler", type=int, help="Run synchronization periodically at the specified interval (in hours).")
    parser.add_argument("--background", action="store_true", help="Run the script in the background (used with --scheduler).")
    parser.add_argument("--reset", action="store_true", help="Reset configuration.")
    parser.add_argument("--analytics", action="store_true", help="Show analytics summary.")
    args = parser.parse_args()

    if args.reset:
        reset_config()
        return

    if not args.about:
        try:
            validate_config()
        except (FileNotFoundError, ValueError) as e:
            print(e)
            sys.exit(1)

    if args.about:
        show_about()
        return

    synchronizer = DriverSync(log_to_gui=lambda *args, **kwargs: None)

    if args.backup:
        perform_backup(synchronizer)

    if args.sync:
        perform_sync(synchronizer)

    if args.scheduler:
        if args.background:
            run_in_background(["--scheduler", str(args.scheduler)])
        else:
            start_scheduler(synchronizer, args.scheduler)

    if args.analytics:
        show_analytics()

    if not any(vars(args).values()):
        parser.print_help()

if __name__ == "__main__":
    main()
