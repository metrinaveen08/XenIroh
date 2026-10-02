import os
import stat


class PermissionError_(Exception):
    pass


def isRunningAsAdmin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def openReadOnly(path):
    if not os.path.isfile(path):
        raise PermissionError_(f"Not a regular file: {path}")

    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    fd = os.open(path, flags)
    return os.fdopen(fd, "rb")


def ensureNotWritableByAnalysis(path):
    try:
        mode = os.stat(path).st_mode
    except Exception:
        return False
    return stat.S_ISREG(mode)


def describePrivilegeContext():
    return {
        "runningAsAdmin": isRunningAsAdmin(),
        "recommendation": "Run as a standard non-admin user for static analysis."
    }
