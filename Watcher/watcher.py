"""
Watcher/watcher.py

Watches user-chosen folders (picked during first-run setup) for new files
and runs them through static analysis + AI reasoning automatically.

Uses the `watchdog` package for filesystem events. Runs on a background
thread; results are delivered via a callback so the tray app (Qt, on the
main thread) can safely show a notification.

Design notes:
    - A file that's still being written (e.g. mid-download) will fire
      "created" before it's complete. We debounce: wait until the file's
      size stops changing for a short window before analyzing it.
    - Only regular files are analyzed. Directories and temp/partial
      download artifacts (.crdownload, .part, .tmp) are ignored until
      they're renamed to their final name.
"""

import os
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from Assets.FileAnalyzer import analyzeFile
from Assets.ImageAnalyzer import analyzeImage
from Assets.AiBridge import callAiAgent

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}
IGNORED_SUFFIXES = (".crdownload", ".part", ".tmp", ".download")

STABLE_CHECK_INTERVAL_SECONDS = 1.0
STABLE_CHECK_REQUIRED_MATCHES = 2  # size unchanged for this many checks in a row


def waitUntilFileIsStable(path, timeoutSeconds=60):
    """Blocks (on the caller's thread, which should be a worker thread)
    until the file's size stops changing, or the timeout elapses."""
    lastSize = -1
    stableCount = 0
    deadline = time.time() + timeoutSeconds

    while time.time() < deadline:
        try:
            currentSize = os.path.getsize(path)
        except OSError:
            return False  # file disappeared (renamed mid-download, etc.)

        if currentSize == lastSize:
            stableCount += 1
            if stableCount >= STABLE_CHECK_REQUIRED_MATCHES:
                return True
        else:
            stableCount = 0
            lastSize = currentSize

        time.sleep(STABLE_CHECK_INTERVAL_SECONDS)

    return False


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, onResultCallback):
        super().__init__()
        self.onResultCallback = onResultCallback

    def on_created(self, event):
        if event.is_directory:
            return
        self._handleCandidate(event.src_path)

    def on_moved(self, event):
        # Covers "download finished, temp file renamed to final name".
        if event.is_directory:
            return
        self._handleCandidate(event.dest_path)

    def _handleCandidate(self, path):
        if path.lower().endswith(IGNORED_SUFFIXES):
            return
        threading.Thread(target=self._analyzeInBackground, args=(path,), daemon=True).start()

    def _analyzeInBackground(self, path):
        if not waitUntilFileIsStable(path):
            return  # file vanished or never stabilized; skip silently

        if not os.path.isfile(path):
            return

        extension = os.path.splitext(path)[1].lower()
        if extension in IMAGE_EXTENSIONS:
            evidence = analyzeImage(path)
        else:
            evidence = analyzeFile(path)

        aiResult = callAiAgent(evidence)

        try:
            self.onResultCallback(path, evidence, aiResult)
        except Exception:
            pass  # callback errors must never kill the watcher thread


class FolderWatcher:
    """Owns one watchdog Observer covering all configured paths. Start/stop
    are idempotent so the tray app can freely pause/resume monitoring."""

    def __init__(self, onResultCallback):
        self.onResultCallback = onResultCallback
        self.observer = None

    def start(self, watchedPaths):
        self.stop()

        validPaths = [p for p in watchedPaths if os.path.isdir(p)]
        if not validPaths:
            return

        self.observer = Observer()
        handler = NewFileHandler(self.onResultCallback)
        for path in validPaths:
            self.observer.schedule(handler, path, recursive=False)
        self.observer.start()

    def stop(self):
        if self.observer is not None:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None

    def isRunning(self):
        return self.observer is not None and self.observer.is_alive()
