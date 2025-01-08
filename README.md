# DriverSync

## What's This Tool About?
DriverSync is a handy little python script that helps you keep your driver tags in sync between iOverlay (settings.dat) and CrewChief (iracing_reputations.json). It makes sure the tags you use in one app show up in the other. No more juggling or manual edits!

The script is still in its very early stages of development and primarily intended for personal use. However, if you'd like to give it a try, feel free!

## A Heads-Up (Disclaimer)
This script is shared as-is, with absolutely NO guarantees. It’s a personal project and **NOT** officially connected to CrewChief nor iOverlay. Use it at your own risk.

### Before You Start
- Always back up your files just in case.
- It directly edits your files, so double-check the results before you rely on them.
- You need administrative rights to execute this script; otherwise, the files cannot be modified.

### What You Need
- **Python**: Make sure Python 3.x is installed on your computer.
- **Dependencies?** Don’t worry, DriverSync will grab any missing modules for you.

### How to Set It Up
1. Download the script and put it in a folder.

### How to Use It
1. Run the script by double-clicking it, or open a terminal and type:
   ```
   python tags_sync.py
   ```
2. A window will pop up. (hopefully)
3. If needed, use the buttons to select your iOverlay and CrewChief files. If you see two lovely green checks, that means the files are already in the default locations and ready to go.
4. Hit the `Start Synchronization` button.
5. Check the status updates in the app to see what’s going on.

## Need Help?
Logs are saved in `driver_tags_sync.log`. Check this file if something’s not working right. It’ll show you what happened and why.

If you’re still stuck, reach out to me in Discord. Just keep in mind this isn’t an official tool, so support might be limited.

Enjoy syncing your driver tags.
