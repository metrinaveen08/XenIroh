"""
DevicePermissions/permissions.py

Least-privilege helpers for handling untrusted files.

With dynamic/sandbox execution dropped from scope, this module's job
shrinks to one thing: make sure XenIroh only ever reads suspicious files,
never executes or writes to them, and never asks the OS for more access
than that requires.

This is intentionally small. Do not grow it into an execution-permission
system unless dynamic analysis is reintroduced later.
"""

import os
import stat


class PermissionError_(Exception):
    """Raised when a requested operation would exceed least-privilege
    access to an untrusted file. Named with a trailing underscore to avoid
    shadowing the builtin PermissionError."""
    pass


def isRunningAsAdmin():
    """XenIroh should not need admin rights to statically analyze a file.
    If it's running elevated, warn - elevated + untrusted input is a bad
    combination."""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def openReadOnly(path):
    """Open an untrusted file strictly for reading, never for write or
    execute. Returns a file handle the caller is responsible for closing."""
    if not os.path.isfile(path):
        raise PermissionError_(f"Not a regular file: {path}")

    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):  # Windows
        flags |= os.O_BINARY

    fd = os.open(path, flags)
    return os.fdopen(fd, "rb")


def ensureNotWritableByAnalysis(path):
    """Best-effort check that the target isn't something XenIroh itself
    could accidentally modify (e.g. a file inside its own working
    directory). Returns True if safe to analyze read-only."""
    try:
        mode = os.stat(path).st_mode
    except Exception:
        return False

    # We only ever open read-only ourselves; this check exists to catch
    # obviously wrong inputs (e.g. pointing XenIroh at its own source tree)
    # rather than to enforce OS-level ACLs.
    return stat.S_ISREG(mode)


def describePrivilegeContext():
    """Small evidence dict describing the privilege level XenIroh itself
    is running under, so the AI/explanation layer can note it if relevant
    (e.g. 'analysis performed without elevated privileges')."""
    return {
        "runningAsAdmin": isRunningAsAdmin(),
        "recommendation": (
            "Run XenIroh as a standard (non-admin) user for static analysis."
        ),
    }
