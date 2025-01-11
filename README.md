# DriverSync

DriverSync is a python-based application designed to synchronize your drivers data between iOverlay and CrewChief. DriverSync ensures smooth synchronization while maintaining data integrity. 
By syncing iOverlay with CrewChief, you gain both a visual and audible perspective on any problematic drivers.

# How does it function?
In the General section of iOverlay, there’s an option called Driver Tags. This feature lets you add drivers under various group names, such as friends or dirty drivers. 
CrewChief offers a similar functionality called Reputations, where you can mark drivers as “dirty,” indicating that you should be cautious around them. You can tell Jim(CrewChief) to "mark the driver [ahead/behind] as dirty" 

DriverSync enables you to synchronize these “dirty” driver lists with iOverlay and CrewChief. It creates a new group in iOverlay named CrewChief, automatically populates it with the synchronized drivers, and also updates CrewChief with any tagged drivers from iOverlay.
---
IMPORTANT: The Windows executable was compiled using PyInstaller, which may cause certain antivirus programs to flag it as a threat. Rest assured, this is a false positive. Please whitelist the executable in your antivirus settings to use it, or consider using the Python version instead.

## Features

- **Synchronization:** Bidirectional syncing of driver tags and reputations between iOverlay (`settings.dat`) and CrewChief (`iracing_reputations.json`)
- **iOverlay Category Selection:** Dynamically select iOverlay categories to be include in the synchronization.
- **Dynamic Path Detection**: Detects both localized `OneDrive` paths for CrewChief files (e.g., `Documenten` for Dutch systems) and traditional Documents folders 
- **Analytics Dialog**: View synchronization statistics
- **Synchronization Preview**: Preview changes before applying them.
- **Backup:** Automatic creation of timestamped backups for data safety.
- **Customizable Settings:** Configure sync paths, update behavior, and more through the settings dialog.
- **Scheduler with Countdown Timer**: Schedule automatic synchronization tasks with a countdown timer.
- **User-Friendly GUI:** Dark-themed interface with real-time logs
- **Logging:** logs saved to `DriverSync.log` for debugging and tracking.
- **Automatic Dependency Management:** Installs required Python modules automatically.
- **Silent mode** Once you’ve completed your initial configuration in the GUI, you can enable the Silent mode parameter.
- **Background modus** Automatically starts in the systray
---

## Disclaimer
This script is an independent, third-party tool intended for use with iOverlay and CrewChief. It is not affiliated with, endorsed by, or supported by iOverlay, CrewChief, or their respective owners. Use of this script is at your own risk, and no warranty—express or implied—is provided. The author assumes no responsibility for any damage, loss, or other issues arising from its use.

### Prerequisites

- For running the Python (DriveSync.py) script:
  - Python 3.8+
  - Required modules: `PyQt5, requests, schedule`

- For running the Windows Executable: 
  - The Windows executable is just a single file.be sure to place it in its own dedicated folder.

### Installation for DriverSync Python Version

- Install Python from the Microsoft Store or http://www.python.org/downloads

#### Running the Script

Run the Python version:
   ```bash
   python DriverSync.py                   GUI mode
   python DriverSync.py --run             Silent mode
   python DriverSync.py --background      Background mode (in systray)
   python DriverSync.py --reset           Reset all settings. statistics and logs
   python DriverSync.py --help            Help me :-)
   ```

 Or run the Windows Executable version:
   ```bash
  DriverSync.exe                          GUI mode
  DriverSync.exe --run                    Silent mode
  DriverSync.exe --background-process     Background mode (in systray)
   ```

Once you’ve completed the initial GUI configuration, you can run DriverSync in silent or background mode.

## Usage

1. Launch the application.
2. Configure file paths for iOverlay and CrewChief data in the Settings dialog if needed. DriverSync will automatically look for the default paths of iOverlay and CrewChief.
3. Click "Sync Now" or "Preview"to start/Show the synchronization process.

## Credits

DriverSync is developed by **Pazzie**.
