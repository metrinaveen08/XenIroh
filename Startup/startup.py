"""
Startup/startup.py

Registers XenIroh to launch automatically when the user logs in, using the
per-user HKCU "Run" registry key. This deliberately does NOT touch
HKLM/system-wide autorun - that would need admin rights and would run
XenIroh for every user on the machine, neither of which is appropriate
for a per-user security tray app.
"""

import sys

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "XenIroh"


def getLaunchCommand():
    """Command written to the registry. If running from a frozen .exe
    (PyInstaller etc.), sys.executable IS the app - just launch it.
    If running from source via `python main.py`, launch it the same way
    the developer would."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonExe = sys.executable
    mainScript = sys.argv[0]
    return f'"{pythonExe}" "{mainScript}" --startup'


def enableStartup():
    if not HAS_WINREG:
        return False, "winreg unavailable (not running on Windows)."

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, getLaunchCommand())
        winreg.CloseKey(key)
        return True, "Startup enabled."
    except Exception as exc:
        return False, f"Could not enable startup: {exc}"


def disableStartup():
    if not HAS_WINREG:
        return False, "winreg unavailable (not running on Windows)."

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, VALUE_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True, "Startup disabled."
    except Exception as exc:
        return False, f"Could not disable startup: {exc}"


def isStartupEnabled():
    if not HAS_WINREG:
        return False

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, VALUE_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False
