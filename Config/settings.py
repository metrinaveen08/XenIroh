"""
Config/settings.py

Persistent XenIroh settings, stored per-user in:
    %APPDATA%\\XenIroh\\config.json

Currently holds just the watched-folder list, chosen by the user during
first-run setup (GUI/SetupDialog.py). Kept separate from AI/Assets so both
the tray app and the setup dialog can read/write it without importing GUI
code into each other.
"""

import json
import os

APP_NAME = "XenIroh"

DEFAULT_CONFIG = {
    "watchedPaths": [],
    "startAtLogin": True,
    "setupComplete": False,
}


def getConfigDir():
    appData = os.environ.get("APPDATA")
    if not appData:
        # Fallback for non-Windows dev/testing.
        appData = os.path.expanduser("~/.config")
    configDir = os.path.join(appData, APP_NAME)
    os.makedirs(configDir, exist_ok=True)
    return configDir


def getConfigPath():
    return os.path.join(getConfigDir(), "config.json")


def loadConfig():
    path = getConfigPath()
    if not os.path.isfile(path):
        return dict(DEFAULT_CONFIG)

    try:
        with open(path, "r", encoding="utf-8") as fileHandle:
            config = json.load(fileHandle)
    except Exception:
        return dict(DEFAULT_CONFIG)

    merged = dict(DEFAULT_CONFIG)
    merged.update(config)
    return merged


def saveConfig(config):
    path = getConfigPath()
    with open(path, "w", encoding="utf-8") as fileHandle:
        json.dump(config, fileHandle, indent=2)


def isSetupComplete():
    return loadConfig().get("setupComplete", False)


def getWatchedPaths():
    return loadConfig().get("watchedPaths", [])
