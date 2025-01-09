# DriverSync

DriverSync is a python-based application designed to synchronize your drivers data between iOverlay and CrewChief. DriverSync ensures smooth synchronization while maintaining data integrity. 
By syncing iOverlay with CrewChief, you gain both a visual and audible perspective on any problematic drivers.

In the General section of iOverlay, there’s an option called Driver Tags. This feature lets you add drivers under various group names, such as friends or dirty drivers. CrewChief offers a similar functionality called Reputations, where you can mark drivers as “dirty,” indicating that you should be cautious around them.

DriverSync enables you to synchronize these “dirty” driver lists. It creates a new group in iOverlay named CrewChief, automatically populates it with the synchronized drivers, and also updates CrewChief with any tagged drivers from iOverlay.

---

## Releases
[DriverSync_v0.1.zip](https://github.com/cenodude/DriverSync/releases/download/0.1/DriverSync_v0.1.zip) for the Python version or/and [DriverSync.v0.1_Windows_Executable.zip](https://github.com/cenodude/DriverSync/releases/download/0.1/DriverSync.v0.1_Windows_Executable.zip) for the Windows Executable version that doesnt require Python.

IMPORTANT: The Windows executable was compiled using PyInstaller, which may cause certain antivirus programs to flag it as a threat. Rest assured, this is a false positive. Please whitelist the executable in your antivirus settings to use it, or consider using the Python version instead.

## Features

- **Synchronization:** Bidirectional syncing of driver tags and reputations between iOverlay (`settings.dat`) and CrewChief (`iracing_reputations.json`).
- **Backup:** Automatic creation of timestamped backups for data safety.
- **Customizable Settings:** Configure sync paths, update behavior, and more through the settings dialog.
- **User-Friendly GUI:** Dark-themed interface with real-time logs
- **Logging:** logs saved to `DriverSync.log` for debugging and tracking.
- **Automatic Dependency Management:** Installs required Python modules automatically.
- **Silent mode** Once you’ve completed your initial configuration in the GUI, you can enable the Silent mode parameter.
- 
---

## Disclaimer
This script is an independent, third-party tool intended for use with iOverlay and CrewChief. It is not affiliated with, endorsed by, or supported by iOverlay, CrewChief, or their respective owners. Use of this script is at your own risk, and no warranty—express or implied—is provided. The author assumes no responsibility for any damage, loss, or other issues arising from its use.

### Prerequisites

- For running the Python (DriveSync.py) script:
  - Python 3.8+
  - Required modules: `PyQt5`

- For running the Windows Executable: 
  - The Windows executable is just a single file.be sure to place it in its own dedicated folder.

### Installation for DriverSync Python Version

- Install Python from the Microsoft Store (Windows 10 or later) or http://www.python.org/downloads

#### Running the Script

1. Run the Python version in GUI mode:
   ```bash
   python DriverSync.py 
   ```

 Or run the Windows Executable version in GUI mode:
   ```bash
  DriverSync.exe 
   ```

2. Run the Python Version in SILENT mode:
   ```bash
   python DriverSync.py --run
   ```
 
Or run the Windows Executable version in SILENT mode:
  ```bash
  DriverSync.exe --run
   ```
#### Running the Windows Executable 

1. Run the application in GUI mode:
   ```bash
   DriverSync.exe 
   ```

2. Run the application in SILENT mode:
   ```bash
   DriverSync.exe --run
   ```
Once you’ve completed the initial GUI configuration, you can run DriverSync in silent mode, which allows you to schedule the script for automatic execution. 

---

## Usage

1. Launch the application.
2. Configure file paths for iOverlay and CrewChief data in the Settings dialog if needed. DriverSync will automatically look for the default paths of iOverlay and CrewChief.
3. Click "Sync Now" to start the synchronization process.

---

## Backup

Backups are stored in the `Backup` folder with filenames including timestamps for easy identification. Backups ensure data safety before synchronization.

---

## Configuration

The application uses `config.json` to store default settings:

```json
{
  "ioverlay_settings_path": "<default_path_to_settings.dat>",
  "crewchief_reputations_path": "<default_path_to_iracing_reputations.json>",
  "update_existing_entries": false,
  "sync_behavior": "Additive Only"
}
```

Please avoid making manual changes; instead, use the DriveSync settings dialog.

---
## Logs

Logs are stored in the `Logs` folder and include detailed information about synchronization operations and any errors encountered.

---

## Credits

DriverSync is developed by **Pazzie**.
