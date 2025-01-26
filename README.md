# DriverSync Latest Version 0.8

**DriverSync** is like a matchmaker for iOverlay and CrewChief, bringing them together for perfect harmony. It ensures your driver data stays in sync while keeping things squeaky clean. Syncing iOverlay with CrewChief gives you both a visual heads-up and Jim’s melodious voice calling out those "problematic" drivers. It's like having a personal assistant who’s also a snitch!

But that’s not all! DriverSync doesn’t just sync—it manages your drivers with flair and gives you detailed reports so you know exactly what’s going on. Whether it’s tracking who’s in, who’s out, or figuring out what changed, DriverSync’s got your back. It’s like having an accountant, a bouncer, and a private investigator rolled into one handy tool.

---
## 🚀 **How It Works**

In the General section of **iOverlay**, you can tag drivers under various categories such as "friends" or "dirty drivers." Similarly, **CrewChief** allows marking drivers as "dirty," letting you instruct Jim (CrewChief) to "mark the driver [ahead/behind] as dirty."

DriverSync synchronizes these "dirty" driver lists between iOverlay and CrewChief. It:
- Creates a new group in iOverlay named "CrewChief."
- Automatically populates this group with synchronized drivers.
- Updates CrewChief with tagged drivers from iOverlay.  

## 🌟 **Features (GUI)** 
- **Setup Wizard** The Setup Wizard guides you seamlessly through the entire process with a simple "Next, Next, Next" approach.
- **DriverSync GUI and DriverSync CLI**: Choose between a user-friendly interface or command-line tools for automation.
- **Synchronization Modes**:
  - **Additive Only**: Adds missing drivers without deleting existing data.
  - **Bidirectional**: Fully synchronizes data by adding missing drivers and removing obsolete ones.
- **Update Existing Entries**: Keeps driver details (e.g., name or category) updated across systems.
- **Driver and Group Editor**: Edit, add drivers and groups.
- **Reputations Settings**: change iRacing Safety ratings, enable Club Reputations, Club Manager and editor
- **Preview Mode**: See a detailed preview of synchronization changes before applying them.
- **Backup Support**: Automatically creates backups of iOverlay and CrewChief files to prevent data loss.
- **Scheduling**: Automate your synchronization to run every X hours.
- **Delta Reporting**: Displays a summary of synchronization actions, including drivers added, deleted, and total counts.

---

## 📌 Prerequisites and how it works
CrewChief v4 must be installed and launched at least once.  
iOverlay must be installed and launched at least once. For full functionality, *a subscription is recommended*.

- **Step 1**: Configure your settings in DriverSync. The default options work just fine, but if you’re feeling adventurous, go wild and tweak away!
- **Step 2**: Start iRacing with Crewchief and Instruct Jim (CrewChief) to "mark the driver [ahead/behind] as dirty.

That’s it! Now this driver is synced with iOverlay, complete with a glaring heads-up (standings/relative overlays) and a friendly shout that they’re flagged as dirty/sketchy. Best of all, no more manual adding drivers

---

## 📜 **Sync Behavior**

The `sync_behavior` configuration controls how synchronization handles additions and deletions:

| **Scenario**                                          | **Additive Only** | **Bidirectional** | **Update Existing Entries** |
|-------------------------------------------------------|--------------------|--------------------|-----------------------------|
| Keep both systems identical by adding/deleting drivers. | ❌                 | ✅                 | ❌                          |
| Prevent deletions while adding missing drivers.        | ✅                 | ❌                 | ❌                          |
| Correct mismatched driver details (e.g., name updates).| ❌                 | ❌                 | ✅                          |
| Fully synchronize both systems, including updates.     | ❌                 | ✅                 | ✅                          |
| Avoid data loss by preserving existing driver details. | ✅                 | ✅                 | ❌                          |


## ▶️ **Usage Instructions**

### Running the Windows Executable
```bash
DriverSync.exe                          # GUI mode  <-- use this for most users
DriverSync_CLI.exe                      # CLI mode
```

Once you’ve completed the initial GUI configuration, you can run DriverSync in silent or background mode. Alternatively, use `DriverSync_CLI` for integration into automation scripts or cron jobs.

---
## 🖥️ **DriverSync_CLI Command-Line Arguments**

DriverSync_CLI provides several options for managing synchronization and backups:
- `--sync`          Perform synchronization based on `config.json`.
- `--preview`       Preview synchronization changes without applying them.
- `--backup`        Create a backup of the iOverlay and CrewChief files.
- `--about`         Display information about DriverSync.
- `--scheduler N`   Run synchronization every N hours.
- `--background`    Run the script in the background (used with `--scheduler`).
- `--reset`         Reset the application.
- `--analytics`     Show analytics summary.
---

## 📥 **Download Links**
- 💾 **[DriverSync.v0.8.Python.zip](https://github.com/cenodude/DriverSync/releases/download/0.8/DriverSync.v0.8.Python.zip)**: Full Python source code for developers.
- 🖥️ **[DriverSync.v0.8_Windows_Installer.zip](https://github.com/cenodude/DriverSync/releases/download/0.8/DriverSync.v0.8_Windows_Installer.zip)**: Windows installer (ZIP format).
- 🖥️ **[DriverSync.v0.8_Windows_Installer.exe](https://github.com/cenodude/DriverSync/releases/download/0.8/DriverSync.v0.8_Windows_Installer.exe)**: Windows installer (Executable format).

> ⚠️ **Important Note**:  
> The Windows executable was created using PyInstaller, which may cause antivirus programs to flag it as a threat. This is a **false positive**.  

## 🙌 **Credits**

---
DriverSync is developed by **Pazzie**. If you find this tool useful, consider giving it a star on [GitHub](https://github.com/cenodude/DriverSync)!  
For questions or support, reach out via:
- **Discord**: cenodude#2185

---

## ⚠️ **Disclaimer**

DriverSync is an independent, third-party tool not affiliated with or supported by iOverlay, CrewChief, or their respective owners. **Use it at your own risk.** No warranty is provided, and the author assumes no responsibility for any damages or issues arising from its use.

---
  
