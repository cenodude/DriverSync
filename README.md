
```
░▒▓███████▓▒░░▒▓███████▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓███████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒▒▓█▓▒░░▒▓██████▓▒░ ░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░        
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░  ░▒▓██▓▒░  ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░   ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  
                                                                                                                           
```  

# DriverSync

**DriverSync** is a Python-based application designed to synchronize driver data between **iOverlay** and **CrewChief**. It ensures seamless synchronization while maintaining data integrity. By syncing iOverlay with CrewChief, you gain both a visual and audible perspective on potentially problematic drivers.

---

## **How It Works**

In the General section of **iOverlay**, you can tag drivers under various categories such as "friends" or "dirty drivers." Similarly, **CrewChief** allows marking drivers as "dirty," letting you instruct Jim (CrewChief) to "mark the driver [ahead/behind] as dirty."

DriverSync synchronizes these "dirty" driver lists between iOverlay and CrewChief. It:
- Creates a new group in iOverlay named "CrewChief."
- Automatically populates this group with synchronized drivers.
- Updates CrewChief with tagged drivers from iOverlay.

---

## **Disclaimer**

DriverSync is an independent, third-party tool not affiliated with or supported by iOverlay, CrewChief, or their respective owners. Use it at your own risk. No warranty is provided, and the author assumes no responsibility for any damages or issues arising from its use.

> **Note**: The Windows executable was created using PyInstaller, which may cause antivirus programs to flag it as a threat. This is a false positive. Please whitelist the executable or consider using the Python version.

---

## **Features (GUI)** 
- **DriverSync GUI and DriverSync CLI**: The GUI provides a user-friendly interface for configuring and managing synchronization interactively, while the DriverSync CLI offers a lightweight, command-line alternative for automation and integration into scripts or scheduled tasks.
- **Synchronization Modes**:
  - **Additive Only**: Adds missing drivers without deleting existing data.
  - **Bidirectional**: Fully synchronizes data by adding missing drivers and removing obsolete ones.
- **Update Existing Entries**: Keeps driver details (e.g., name or category) updated across systems.
- **Category Filtering**: Synchronize drivers only from selected categories.
- **Preview Mode**: See a detailed preview of synchronization changes before applying them.
- **Backup Support**: Automatically creates backups of iOverlay and CrewChief files to prevent data loss.
- **Delta Reporting**: Displays a summary of synchronization actions, including drivers added, deleted, and total counts.

---

## **Sync Behavior**

The `sync_behavior` configuration controls how synchronization handles additions and deletions:

| **Scenario**                                          | **Additive Only** | **Bidirectional** | **Update Existing Entries** |
|-------------------------------------------------------|--------------------|--------------------|-----------------------------|
| Keep both systems identical by adding/deleting drivers. | ❌                 | ✅                 | ❌                          |
| Prevent deletions while adding missing drivers.        | ✅                 | ❌                 | ❌                          |
| Correct mismatched driver details (e.g., name updates).| ❌                 | ❌                 | ✅                          |
| Fully synchronize both systems, including updates.     | ❌                 | ✅                 | ✅                          |
| Avoid data loss by preserving existing driver details. | ✅                 | ✅                 | ❌                          |

---

## **Examples**
1. **Additive Only with `update_existing_entries`:**
   - Drivers are only added between systems.
   - Existing driver details are synchronized (e.g., name corrections).

2. **Bidirectional Without `update_existing_entries`:**
   - Drivers are added or deleted as needed.
   - No updates to existing driver details.

3. **Bidirectional with `update_existing_entries`:**
   - Adds and deletes drivers as needed.
   - Updates details for drivers already present in both systems.

---

## **Prerequisites**
- **Python Version**:
  - Python 3.8+
  - Required modules: `PyQt5, requests, schedule`
- **Windows Executable**:
  - Place the executable in a dedicated folder.

---

## **Installation for DriverSync (Python Version)**

1. Install Python from the [official site](http://www.python.org/downloads) or the Microsoft Store.
2. Install required modules:
   ```bash
   pip install PyQt5 requests schedule
   ```

---

## **Usage Instructions**

### Running the Python Version
```bash
python DriverSync.py                   # GUI mode
python DriverSync.py --run             # Silent mode
python DriverSync.py --background      # Background mode (systray)
python DriverSync.py --reset           # Reset all settings, stats, and logs
python DriverSync.py --help            # Show help information
```

### Running the Windows Executable
```bash
DriverSync.exe                          # GUI mode
DriverSync.exe --run                    # Silent mode
DriverSync.exe --background-process     # Background mode (systray)
```

Once you’ve completed the initial GUI configuration, you can run DriverSync in silent or background mode. Alternatively, use `DriverSync_CLI` for integration into automation scripts or cron jobs.

---

## **DriverSync_CLI Command-Line Arguments**

DriverSync_CLI provides several options for managing synchronization and backups:
- `--sync`          Perform synchronization based on `config.json`.
- `--preview`       Preview synchronization changes without applying them.
- `--backup`        Create a backup of the iOverlay and CrewChief files.
- `--about`         Display information about DriverSync.
- `--scheduler N`   Run synchronization every N hours.
- `--background`    Run the script in the background (used with `--scheduler`).
- `--reset`         Reset the application.
- `--analytics`     Show analytics summary.

Example:
```bash
# Perform synchronization
python DriverSync_CLI.py --sync

# Preview changes
python DriverSync_CLI.py --preview

# Schedule synchronization every 2 hours in the background
python DriverSync_CLI.py --scheduler 2 --background
```

---

## **Credits**

DriverSync is developed by **Pazzie**. If you find this tool useful, consider giving it a star on [GitHub](https://github.com/cenodude/DriverSync)!"
