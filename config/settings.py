import json
import os

APP_NAME = "XenIroh"

DEFAULT_CONFIG = {
    "watchedPaths": [],
    "startAtLogin": True,
    "setupComplete": False,
    "theme": "Green / White"
}


def getConfigDir():
    appData = os.environ.get("APPDATA")
    if not appData:
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
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return dict(DEFAULT_CONFIG)

    merged = dict(DEFAULT_CONFIG)
    merged.update(config)
    return merged


def saveConfig(config):
    path = getConfigPath()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def isSetupComplete():
    return loadConfig().get("setupComplete", False)


def getWatchedPaths():
    return loadConfig().get("watchedPaths", [])
