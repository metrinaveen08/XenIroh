"""
main.py

XenIroh entry point. Stays clean on purpose - no analysis or reasoning
logic here.

Default: launches the tray app (background monitoring + system tray icon).
This is what runs both when the user double-clicks XenIroh and when
Windows starts it automatically at login.
"""

from GUI.TrayApp import launchTrayApp

if __name__ == "__main__":
    launchTrayApp()
