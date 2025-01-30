import json
import csv
import os

from datetime import datetime
from PyQt5.QtCore import QTimer
from pathlib import Path

from _analytics import record_analytics
from _editor import Editor
from _logging import log_to_gui

def get_onedrive_documents_path():
    """
    Retrieves the Documents path, prioritizing OneDrive if available, with fallback to local Documents.
    Handles localization and missing folders gracefully.
    """
    try:
        onedrive_path = os.environ.get("OneDrive", None)
        if not onedrive_path or not Path(onedrive_path).exists():
            user_profile = os.environ.get("USERPROFILE", "")
            fallback_path = os.path.join(user_profile, "Documents")
            return fallback_path if Path(fallback_path).exists() else None

        for folder in os.listdir(onedrive_path):
            folder_path = os.path.join(onedrive_path, folder)
            if os.path.isdir(folder_path) and "document" in folder.lower():
                return folder_path

        return os.path.join(onedrive_path, "Documents")

    except Exception as e:
        default_log_to_gui(f"Error resolving Documents path: {e}", "error")
        return None

class DriverSync:
    def __init__(self, log_to_gui=None, ui=None):
        self.log_to_gui = log_to_gui
        self.ui = ui  # Reference to the UI class if passed

        log_folder = "Logs"
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        self.log_file = os.path.join(log_folder, "DriverSync.log")
        self.log_messages = []
        self.config_file = "config.json"
        self.config_path = Path(self.config_file)
        self.default_config = {
            "ioverlay_settings_path": "",
            "crewchief_reputations_path": "",
            "minimize_to_tray": False,
            "update_existing_entries": False,
            "sync_behavior": "Additive Only",
            "backup_files": True,
            "backup_retention_days": 5,
            "scheduler_interval": None,
            "enabled_categories": {}
        }

        # Ensure config.json exists
        self.config = self.load_or_create_config()

        # Load default paths and configurations
        defaults = self.get_default_paths()
        self.ioverlay_path = self.config.get("ioverlay_settings_path", defaults[0])
        self.crewchief_path = self.config.get("crewchief_reputations_path", defaults[1])

        if not self.config.get("ioverlay_settings_path"):
            self.log_empty_path("ioverlay_settings_path", defaults[0])
            self.config["ioverlay_settings_path"] = defaults[0]

        if not self.config.get("crewchief_reputations_path"):
            self.log_empty_path("crewchief_reputations_path", defaults[1])
            self.config["crewchief_reputations_path"] = defaults[1]

        # Validate or create necessary files
        self.validate_and_create_files()

        # Load synchronization settings
        self.update_existing_entries = self.config.get("update_existing_entries", False)
        self.sync_behavior = self.config.get("sync_behavior", "Additive Only")
        self.enabled_categories = self.config.get("enabled_categories", {})
        
        # Enable CrewChief category if not already configured
        if "CrewChief" not in self.enabled_categories:
            self.enabled_categories["CrewChief"] = True
            self.save_config()

        # Explicitly save missing keys to config.json
        if "update_existing_entries" not in self.config:
            self.log("Adding 'update_existing_entries' to configuration with default value: False", "info")
            self.config["update_existing_entries"] = False
            self.save_config()
        
    def log(self, message, level="info", show_debug_in_gui=False, html=False, to_gui=True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level.upper()}] {message}"

        # Write to the log file
        with open(self.log_file, "a") as log_file:
            log_file.write(entry + "\n")

        # Log to GUI if enabled and to_gui is True
        if self.log_to_gui and to_gui and (level != "debug" or show_debug_in_gui):
            if html:
                self.log_to_gui(message, level, html=True)  # GUI log with HTML formatting
            else:
                self.log_to_gui(f"[{level.upper()}] {message}", level)  # GUI log without timestamp

    def load_or_create_config(self):
        """
        Load the configuration file or create it with default values if it does not exist.
        Ensures all necessary keys are present and logs updates where applicable.
        """
        default_ioverlay_path, default_crewchief_path = self.get_default_paths()

        # Create default configuration if config file does not exist
        if not os.path.exists(self.config_file):
            self.log("Config file not found. Creating with default values.", "info")
            self.default_config.update({
                "ioverlay_settings_path": str(default_ioverlay_path),
                "crewchief_reputations_path": str(default_crewchief_path),
                "enabled_categories": {"CrewChief": True},
                "update_existing_entries": False,  # Default value
                "sync_behavior": "Additive Only",  # Default value
            })
            self.save_config(self.default_config)
            return self.default_config

        try:
            with open(self.config_file, "r") as file:
                config = json.load(file)

            updates_made = False

            # Validate and update paths if empty
            if not config.get("ioverlay_settings_path"):
                self.log("iOverlay path is empty in config.json. Using default.", "warning")
                config["ioverlay_settings_path"] = str(default_ioverlay_path)
                updates_made = True

            if not config.get("crewchief_reputations_path"):
                self.log("CrewChief path is empty in config.json. Using default.", "warning")
                config["crewchief_reputations_path"] = str(default_crewchief_path)
                updates_made = True

            # Ensure CrewChief category is always enabled
            if "CrewChief" not in config.get("enabled_categories", {}):
                config["enabled_categories"] = config.get("enabled_categories", {})
                config["enabled_categories"]["CrewChief"] = True
                updates_made = True

            # Add missing configuration keys with default values
            if "update_existing_entries" not in config:
                self.log("Adding 'update_existing_entries' to config with default value: False.", "info")
                config["update_existing_entries"] = False
                updates_made = True

            if "sync_behavior" not in config:
                self.log("Adding 'sync_behavior' to config with default value: Additive Only.", "info")
                config["sync_behavior"] = "Additive Only"
                updates_made = True

            if updates_made:
                self.save_config(config)
                self.log("Configuration updated with default values where necessary.", "info")

            return config

        except json.JSONDecodeError as e:
            # Log the error and reset to default configuration
            self.log(f"Invalid config.json. Error: {e}. Resetting to default.", "error")
            self.default_config.update({
                "ioverlay_settings_path": str(default_ioverlay_path),
                "crewchief_reputations_path": str(default_crewchief_path),
                "enabled_categories": {"CrewChief": True},
                "update_existing_entries": False,
                "sync_behavior": "Additive Only",
            })
            self.save_config(self.default_config)
            return self.default_config

        except Exception as e:
            # Log unexpected errors and reset to default configuration
            self.log(f"Unexpected error loading config.json: {e}. Resetting to default.", "error")
            self.default_config.update({
                "ioverlay_settings_path": str(default_ioverlay_path),
                "crewchief_reputations_path": str(default_crewchief_path),
                "enabled_categories": {"CrewChief": True},
                "update_existing_entries": False,
                "sync_behavior": "Additive Only",
            })
            self.save_config(self.default_config)
            return self.default_config

    def is_path_valid(self):
        crewchief_folder = os.path.dirname(self.crewchief_path)
        return os.path.exists(crewchief_folder) and os.path.exists(self.crewchief_path)

    def get_default_paths(self):
        profile = os.environ.get("USERPROFILE", "")
        ioverlay = os.path.join(profile, "AppData", "Roaming", "iOverlay", "settings.dat")
        onedrive_documents = get_onedrive_documents_path()
        crewchief = os.path.join(profile, "Documents", "CrewChiefV4", "iracing_reputations.json")
        onedrive_crewchief = os.path.join(onedrive_documents, "CrewChiefV4", "iracing_reputations.json") if onedrive_documents else None

        if os.path.exists(crewchief):
            return ioverlay, crewchief
        elif onedrive_crewchief and os.path.exists(onedrive_crewchief):
            return ioverlay, onedrive_crewchief
        return ioverlay, crewchief
        
    def validate_config_files(self):
        try:
            # Validate iOverlay path
            if not self.ioverlay_path or not os.path.exists(self.ioverlay_path):
                self.log(f"Invalid iOverlay file path: {self.ioverlay_path}", "error", to_gui=False)
                return False

            # Validate settings.dat structure
            try:
                ioverlay_data = self.read_file(self.ioverlay_path)
                if not self.is_valid_ioverlay_data(ioverlay_data):
                    self.log("Invalid iOverlay settings.dat structure. Missing required keys.", "error", to_gui=True)
                    return False
            except Exception as e:
                self.log(f"Error validating iOverlay file structure: {e}", "error", to_gui=True)
                return False

            # Validate CrewChief path
            if not self.crewchief_path or not os.path.exists(self.crewchief_path):
                self.log(f"Invalid CrewChief file path: {self.crewchief_path}", "error", to_gui=False)
                return False

            # Validate CrewChief file structure
            try:
                crewchief_data = self.read_file(self.crewchief_path)
                if not self.validate_crewchief_data(crewchief_data):
                    self.log("Invalid CrewChief file structure. Missing required fields.", "error", to_gui=True)
                    return False
            except Exception as e:
                self.log(f"Error validating CrewChief file structure: {e}", "error", to_gui=True)
                return False

            return True
        except Exception as e:
            self.log(f"Unexpected error during validation: {e}", "error", to_gui=True)
            return False

    def validate_crewchief_data(self, data):
        if not isinstance(data, list):
            return False

        required_keys = ["customer_id", "name"]
        for entry in data:
            if not all(key in entry for key in required_keys):
                return False

        return True

    def validate_and_create_files(self):
        try:
            validation_errors = []

            # Validate iOverlay path
            if not self.ioverlay_path:
                validation_errors.append("iOverlay path is empty in config.json.")
            elif not os.path.exists(self.ioverlay_path):
                validation_errors.append("iOverlay settings.dat file not found.")
            else:
                try:
                    ioverlay_data = self.read_file(self.ioverlay_path)
                    if not self.is_valid_ioverlay_data(ioverlay_data):
                        validation_errors.append("Invalid iOverlay settings.dat structure. Required fields are missing.")
                    else:
                        # Ensure the "CrewChief" category exists
                        tagcategories = ioverlay_data.get("modules", {}).get("drivertagging", {}).get("tagcategory", [])
                        crewchief_tag = next((cat for cat in tagcategories if cat["name"] == "CrewChief"), None)
                        if not crewchief_tag:
                            # Add "CrewChief" tag category
                            new_tag_id = max((cat["id"] for cat in tagcategories), default=0) + 1
                            crewchief_tag = {"id": new_tag_id, "name": "CrewChief", "color": "#00FF00"}  # Add color if needed
                            tagcategories.append(crewchief_tag)
                            ioverlay_data["modules"]["drivertagging"]["tagcategory"] = tagcategories
                            self.write_file(self.ioverlay_path, ioverlay_data)
                            self.log("Added 'CrewChief' category to iOverlay settings.", "info", to_gui=True)
                except Exception as e:
                    validation_errors.append(f"Error reading or validating iOverlay settings.dat: {e}")

            # Validate CrewChief path
            if self.crewchief_path:
                if not os.path.exists(self.crewchief_path):
                    try:
                        crewchief_folder = os.path.dirname(self.crewchief_path)
                        if not os.path.exists(crewchief_folder):
                            validation_errors.append("CrewChief folder not found.")
                        else:
                            # Create iracing_reputations.json with a valid empty array
                            self.write_file(self.crewchief_path, [])
                            self.log(f"CrewChief iracing_reputations.json created at {self.crewchief_path}.", "info", to_gui=True)
                    except Exception as e:
                        validation_errors.append(f"Error handling CrewChief path: {e}")
            else:
                # No CrewChief path in config.json; fallback to default logic
                default_crewchief = self.get_default_paths()[1]
                if not os.path.exists(default_crewchief):
                    validation_errors.append("CrewChief folder not found.")
                else:
                    self.crewchief_path = default_crewchief
                    self.log(f"Using default CrewChief path: {self.crewchief_path}", "info", to_gui=True)

            # Log validation errors if any
            if validation_errors:
                combined_message = "\n".join(validation_errors)
                self.log(combined_message, "warning", to_gui=True)
                self.sync_enabled = False
                return

            # Enable Sync and Preview if validations pass
            self.sync_enabled = True
            self.log("File validation and creation completed successfully.", "info", to_gui=False)

        except Exception as e:
            self.log(f"Failed to validate or create required files: {e}", "error", to_gui=False)
            raise


          
    def is_valid_ioverlay_data(self, data):
        try:
            modules = data.get("modules", {})
            drivertagging = modules.get("drivertagging", {})
            if not isinstance(drivertagging, dict):
                return False

            # Validate "tagcategory" and "drivertag" keys
            if "tagcategory" not in drivertagging or "drivertag" not in drivertagging:
                return False

            # Ensure "tagcategory" and "drivertag" are lists
            if not isinstance(drivertagging["tagcategory"], list) or not isinstance(drivertagging["drivertag"], list):
                return False

            return True
        except Exception as e:
            self.log(f"Error validating iOverlay settings.dat structure: {e}", "error")
            return False

    def read_file(self, path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except Exception as e:
            self.log(f"Failed to read file at {path}: {e}", "error")
            raise

    def save_config(self, config=None):
        """
        Saves the current configuration or a provided configuration to the config file.
        Ensures all Path objects are converted to strings before serialization.
        """
        if config is None:
            self.config.update({
                "ioverlay_settings_path": str(self.ioverlay_path),  # Convert to string
                "crewchief_reputations_path": str(self.crewchief_path),  # Convert to string
                "update_existing_entries": self.update_existing_entries,
                "backup_files": self.config.get("backup_files", True),
                "backup_retention_days": self.config.get("backup_retention_days", 5),
                "enabled_categories": self.enabled_categories,
                "sync_behavior": self.config.get("sync_behavior", "Additive Only"),
            })
            config_to_save = self.config
        else:
            # Convert any Path objects in the provided config to strings
            config_to_save = {
                key: str(value) if isinstance(value, Path) else value
                for key, value in config.items()
            }

        with open(self.config_file, "w") as file:
            json.dump(config_to_save, file, indent=4)

        self.log("Configuration saved successfully.", "info", to_gui=False)


    def load_categories(self):
        # Check if the settings.dat file exists
        if not os.path.exists(self.ioverlay_path):
            self.log(f"iOverlay settings.dat file not found at {self.ioverlay_path}. Returning empty categories.", "info", to_gui=False)
            return []

        try:
            # Load the settings.dat file
            with open(self.ioverlay_path, "r") as file:
                data = json.load(file)

            # Extract tag categories
            tagcategories = data.get("modules", {}).get("drivertagging", {}).get("tagcategory", [])
            if not isinstance(tagcategories, list):
                self.log(f"Invalid structure in settings.dat: 'tagcategory' must be a list. Returning empty categories.", "warning")
                return []

            # Sync enabled categories with settings.dat without saving changes
            updated_categories = {
                category.get("name"): self.enabled_categories.get(category.get("name"), False)
                for category in tagcategories
                if category.get("name")
            }

            # Update the enabled categories in memory
            self.enabled_categories = updated_categories
            return tagcategories

        except (KeyError, json.JSONDecodeError, ValueError) as e:
            self.log(f"Failed to load categories from settings.dat. {e}. Returning empty categories.", "error")
            return []


    def log_empty_path(self, key, default):
        self.log(f"{key} is empty in config.json. Using default: {default}", "warning")

    def write_file(self, path, data):
        """
        Writes data to a file in JSON format. Ensures an empty array is written if no data is provided.
        """
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data if data is not None else [], file, indent=4)
            self.log(f"File written successfully to {path}.", "info", to_gui=False)
        except Exception as e:
            self.log(f"Failed to write file at {path}: {e}", "error", to_gui=True)
            raise

    def synchronize_files(self, dry_run=False):
        added_to_ioverlay = 0
        added_to_crewchief = 0
        deleted_from_ioverlay = 0
        deleted_from_crewchief = 0
        preview_data = []

        try:
            # Ensure categories are selected
            self.log_to_gui(f"Checking enabled categories: {self.config.get('enabled_categories')}", "debug")
            if not self.config.get("enabled_categories") or not any(self.config["enabled_categories"].values()):
                self.log_to_gui("No iOverlay categories are selected. Synchronization skipped.", "warning")
                return False, {"error": "No categories selected"}, preview_data

            # Load data from files
            self.log_to_gui(f"Reading iOverlay data from {self.ioverlay_path}", "debug")
            ioverlay_data = self.read_file(self.ioverlay_path)
            self.log_to_gui(f"Reading CrewChief data from {self.crewchief_path}", "debug")
            crewchief_data = self.read_file(self.crewchief_path)

            # Extract and validate data
            tagcategories = ioverlay_data.get("modules", {}).get("drivertagging", {}).get("tagcategory", [])
            drivertags = ioverlay_data.get("modules", {}).get("drivertagging", {}).get("drivertag", [])
            enabled_tag_ids = {cat["id"] for cat in tagcategories if self.config["enabled_categories"].get(cat["name"], False)}

            self.log_to_gui(f"Enabled tag IDs: {enabled_tag_ids}", "debug")

            ioverlay_ids = {tag["identifier"] for tag in drivertags if tag["tagId"] in enabled_tag_ids}
            crewchief_ids = {str(driver["customer_id"]) for driver in crewchief_data}

            # Synchronize CrewChief to iOverlay
            for driver in crewchief_data:
                if str(driver["customer_id"]) not in ioverlay_ids:
                    if dry_run:
                        preview_data.append({
                            "action": "Add",
                            "source": "CrewChief",
                            "details": f"Add driver '{driver['name']}' to iOverlay"
                        })
                    else:
                        drivertags.append({
                            "id": max((tag["id"] for tag in drivertags), default=0) + 1,
                            "identifier": str(driver["customer_id"]),
                            "name": driver["name"],
                            "tagId": next((cat["id"] for cat in tagcategories if cat["name"] == "CrewChief"), None)
                        })
                        added_to_ioverlay += 1

            # Synchronize iOverlay to CrewChief
            for tag in drivertags:
                if tag["tagId"] in enabled_tag_ids and str(tag["identifier"]) not in crewchief_ids:
                    if dry_run:
                        preview_data.append({
                            "action": "Add",
                            "source": "iOverlay",
                            "details": f"Add driver '{tag['name']}' to CrewChief"
                        })
                    else:
                        crewchief_data.append({
                            "customer_id": int(tag["identifier"]),
                            "name": tag["name"],
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "carClass": "",
                            "comment": "Added from iOverlay"
                        })
                        added_to_crewchief += 1

            # Save updated data
            if not dry_run:
                self.log_to_gui(f"Saving updated data to files", "debug")
                ioverlay_data["modules"]["drivertagging"]["drivertag"] = drivertags
                self.write_file(self.ioverlay_path, ioverlay_data)
                self.write_file(self.crewchief_path, crewchief_data)

            # Generate and log synchronization stats
            stats = {
                "added_to_ioverlay": added_to_ioverlay,
                "added_to_crewchief": added_to_crewchief,
                "deleted_from_ioverlay": deleted_from_ioverlay,
                "deleted_from_crewchief": deleted_from_crewchief,
                "total_ioverlay": len(drivertags),
                "total_crewchief": len(crewchief_data),
            }
            self.generate_report(stats)

            # Record analytics
            if not dry_run:
                record_analytics(stats)

            return True, stats, preview_data

        except Exception as e:
            self.log_to_gui(f"Synchronization failed: {e}", "error")
            return False, {"error": str(e)}, preview_data

    def filter_drivers_by_category(self, drivers, enabled_categories):
        try:
            filtered = [driver for driver in drivers if driver.get("tagId") in enabled_categories]
            self.log(f"Filtered drivers based on enabled categories. Count: {len(filtered)}", "info")
            return filtered
        except Exception as e:
            self.log(f"Failed to filter drivers by category. {e}", "error")
            raise

    def count_drivers(self, data):
        try:
            count = len(data)
            self.log(f"Total drivers counted: {count}", "info")
            return count
        except Exception as e:
            self.log(f"Failed to count drivers. {e}", "error")
            raise

    def generate_report(self, stats):
        try:
            report = (
                f"Synchronization Report:\n"
                f"  Drivers added to iOverlay: {stats.get('added_to_ioverlay', 0)}\n"
                f"  Drivers added to CrewChief: {stats.get('added_to_crewchief', 0)}\n"
                f"  Total drivers in iOverlay: {stats.get('total_ioverlay', 0)}\n"
                f"  Total drivers in CrewChief: {stats.get('total_crewchief', 0)}\n"
            )

            return report
        except Exception as e:
            self.log(f"Failed to generate report. {e}", "error")
            raise

    def remove_driver(self, drivers, identifier):
        try:
            initial_count = len(drivers)
            drivers[:] = [driver for driver in drivers if driver.get("identifier") != identifier]
            if len(drivers) < initial_count:
                self.log(f"Removed driver with identifier: {identifier}", "info")
                return True
            else:
                self.log(f"No driver found with identifier: {identifier}", "warning")
                return False
        except Exception as e:
            self.log(f"Failed to remove driver with identifier {identifier}. {e}", "error")
            raise

    def validate_tag_categories(self, tagcategories):
        try:
            if not isinstance(tagcategories, list):
                return False
            for category in tagcategories:
                if not all(k in category for k in ["id", "name", "color"]):
                    return False
            self.log("Tag categories validated successfully.", "info")
            return True
        except Exception as e:
            self.log(f"Failed to validate tag categories. {e}", "error")
            return False

    def assign_category_to_driver(self, drivers, identifier, category_id):
        try:
            for driver in drivers:
                if driver.get("identifier") == identifier:
                    driver["tagId"] = category_id
                    self.log(f"Assigned category ID {category_id} to driver {identifier}.", "info")
                    return True
            self.log(f"Driver with identifier {identifier} not found.", "warning")
            return False
        except Exception as e:
            self.log(f"Failed to assign category ID {category_id} to driver {identifier}. {e}", "error")
            raise

    def update_driver_name(self, drivers, identifier, new_name):
        try:
            for driver in drivers:
                if driver.get("identifier") == identifier:
                    old_name = driver.get("name", "")
                    driver["name"] = new_name
                    self.log(f"Updated driver name from {old_name} to {new_name} for identifier {identifier}.", "info")
                    return True
            self.log(f"Driver with identifier {identifier} not found.", "warning")
            return False
        except Exception as e:
            self.log(f"Failed to update driver name for identifier {identifier}. {e}", "error")
            raise

    def list_all_drivers(self, drivers):
        try:
            driver_list = [{"identifier": driver.get("identifier"), "name": driver.get("name"), "tagId": driver.get("tagId")}
                           for driver in drivers]
            self.log(f"Generated list of all drivers. Count: {len(driver_list)}", "info")
            return driver_list
        except Exception as e:
            self.log(f"Failed to list all drivers. {e}", "error")
            raise

    def validate_and_save_file(self, path, data):
        try:
            if isinstance(data, (dict, list)):
                self.write_file(path, data)
                self.log(f"File saved successfully at {path}.", "success")
                return True
            else:
                self.log(f"Invalid data structure. File not saved at {path}.", "error")
                return False
        except Exception as e:
            self.log(f"Failed to validate and save file at {path}. {e}", "error")
            raise

    def delete_file(self, path):
        try:
            if os.path.exists(path):
                os.remove(path)
                self.log(f"File deleted successfully: {path}", "info")
                return True
            else:
                self.log(f"File not found for deletion: {path}", "warning")
                return False
        except Exception as e:
            self.log(f"Failed to delete file at {path}. {e}", "error")
            raise

    def duplicate_check(self, drivers):
        try:
            seen = set()
            duplicates = set()
            for driver in drivers:
                identifier = driver.get("identifier")
                if identifier in seen:
                    duplicates.add(identifier)
                else:
                    seen.add(identifier)
            self.log(f"Duplicate check completed. Found {len(duplicates)} duplicate(s).", "info")
            return list(duplicates)
        except Exception as e:
            self.log(f"Failed to perform duplicate check. {e}", "error")
            raise

    def fix_duplicates(self, drivers):
        try:
            seen = set()
            unique_drivers = []
            for driver in drivers:
                identifier = driver.get("identifier")
                if identifier not in seen:
                    unique_drivers.append(driver)
                    seen.add(identifier)
            self.log(f"Duplicate entries resolved. Unique drivers count: {len(unique_drivers)}.", "info")
            return unique_drivers
        except Exception as e:
            self.log(f"Failed to resolve duplicates. {e}", "error")
            raise

    def save_driver_data(self, path, drivers):
        try:
            self.write_file(path, drivers)
            #self.log(f"Driver data saved successfully at {path}.", "success", to_gui=False)
            return True
        except Exception as e:
            #self.log(f"Failed to save driver data at {path}. {e}", "error", to_gui=False)
            raise

    def load_driver_data(self, path):
        try:
            data = self.read_file(path)
            self.log(f"Driver data loaded successfully from {path}.", "info", to_gui=False)
            return data
        except Exception as e:
            self.log(f"Failed to load driver data from {path}. {e}", "error", to_gui=False)
            raise

    def export_drivers_to_csv(self, drivers, csv_path):
        try:
            import csv
            with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["identifier", "name", "tagId"])
                writer.writeheader()
                writer.writerows(drivers)
            self.log(f"Driver data exported to CSV successfully: {csv_path}", "success")
            return True
        except Exception as e:
            self.log(f"Failed to export drivers to CSV at {csv_path}. {e}", "error")
            raise

    def import_drivers_from_csv(self, csv_path):
        try:
            import csv
            with open(csv_path, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                drivers = [
                    {"identifier": row["identifier"], "name": row["name"], "tagId": int(row["tagId"])}
                    for row in reader
                ]
            self.log(f"Driver data imported from CSV successfully: {csv_path}", "success")
            return drivers
        except Exception as e:
            self.log(f"Failed to import drivers from CSV at {csv_path}. {e}", "error")
            raise

    def synchronize_with_csv(self, csv_path, drivers):
        try:
            csv_data = self.import_drivers_from_csv(csv_path)
            updated_drivers = self.merge_driver_data(drivers, csv_data, update_existing=True)
            self.log(f"Driver data synchronized with CSV successfully: {csv_path}", "success")
            return updated_drivers
        except Exception as e:
            self.log(f"Failed to synchronize with CSV at {csv_path}. {e}", "error")
            raise

    def clear_driver_data(self, path):
        try:
            self.write_file(path, [])
            self.log(f"Driver data cleared successfully at {path}.", "info")
            return True
        except Exception as e:
            self.log(f"Failed to clear driver data at {path}. {e}", "error")
            raise

    def backup_and_clear(self, path):
        try:
            backup_path = self.create_backup(path)
            if backup_path:
                self.clear_driver_data(path)
                self.log(f"Backup and clear operation completed successfully for {path}.", "success")
                return True
            else:
                self.log(f"Backup failed; clear operation aborted for {path}.", "error")
                return False
        except Exception as e:
            self.log(f"Failed to perform backup and clear operation for {path}. {e}", "error")
            raise

    def log_summary(self, message, stats):
        try:
            self.log(message, "info")
            for key, value in stats.items():
                self.log(f"{key}: {value}", "info")
        except Exception as e:
            self.log(f"Failed to log summary. {e}", "error")
            raise