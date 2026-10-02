import os
import threading

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

from config.settings import loadConfig
from config.protection import quarantineFile, clearQuarantine, getQuarantineDir
from StartupAndWatcher.watcher import waitUntilFileIsStable

IGNORED_SUFFIXES = (".crdownload", ".part", ".tmp", ".download")


# ---------------------------------------------------------------------------
# Watcher that quarantines new files instead of analysing them
# ---------------------------------------------------------------------------

class _QuarantineSignal(QObject):
    """Thread-safe bridge: background watcher -> Qt main thread."""
    fileQuarantined = pyqtSignal(str)  # emits the quarantine destination path


if HAS_WATCHDOG:
    class _ProtectHandler(FileSystemEventHandler):
        def __init__(self, callback):
            super().__init__()
            self._callback = callback

        def on_created(self, event):
            if not event.is_directory:
                self._callback(event.src_path)

        def on_moved(self, event):
            if not event.is_directory:
                self._callback(event.dest_path)


class _PollingProtectThread(threading.Thread):
    """Fallback poller when watchdog is unavailable."""
    def __init__(self, paths, callback, interval=1.0):
        super().__init__(daemon=True)
        self.paths = paths
        self.callback = callback
        self.interval = interval
        self.stopEvent = threading.Event()
        self.known = set()
        self._seed()

    def _seed(self):
        for p in self.paths:
            if os.path.isdir(p):
                try:
                    for f in os.listdir(p):
                        self.known.add(os.path.join(p, f))
                except OSError:
                    pass

    def run(self):
        while not self.stopEvent.is_set():
            for folder in self.paths:
                if not os.path.isdir(folder):
                    continue
                try:
                    for f in os.listdir(folder):
                        full = os.path.join(folder, f)
                        if os.path.isfile(full) and full not in self.known:
                            self.known.add(full)
                            self.callback(full)
                except OSError:
                    pass
            self.stopEvent.wait(self.interval)

    def stop(self):
        self.stopEvent.set()


class ProtectWatcher:
    """Monitors folders and quarantines every new file that appears."""

    def __init__(self, signalRelay):
        self._signal = signalRelay
        self._observer = None
        self._pollingThread = None
        self._lock = threading.Lock()

    # -- public API ----------------------------------------------------------

    def start(self, watchedPaths):
        self.stop()
        validPaths = [p for p in watchedPaths if os.path.isdir(p)]
        if not validPaths:
            return

        if HAS_WATCHDOG:
            self._observer = Observer()
            handler = _ProtectHandler(self._onNewFile)
            for p in validPaths:
                self._observer.schedule(handler, p, recursive=False)
            self._observer.start()
        else:
            self._pollingThread = _PollingProtectThread(
                validPaths, self._onNewFile
            )
            self._pollingThread.start()

    def stop(self):
        if HAS_WATCHDOG and self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=3)
            self._observer = None
        elif self._pollingThread is not None:
            self._pollingThread.stop()
            self._pollingThread.join(timeout=3)
            self._pollingThread = None

    def isRunning(self):
        if HAS_WATCHDOG and self._observer is not None:
            return self._observer.is_alive()
        if self._pollingThread is not None:
            return self._pollingThread.is_alive()
        return False

    # -- internal ------------------------------------------------------------

    def _onNewFile(self, path):
        """Called from a background thread."""
        if path.lower().endswith(IGNORED_SUFFIXES):
            return
        threading.Thread(
            target=self._quarantineWorker, args=(path,), daemon=True
        ).start()

    def _quarantineWorker(self, path):
        if not waitUntilFileIsStable(path):
            return
        if not os.path.isfile(path):
            return
        with self._lock:
            dest = quarantineFile(path)
        if dest:
            self._signal.fileQuarantined.emit(dest)


# ---------------------------------------------------------------------------
# UI Page
# ---------------------------------------------------------------------------

class ProtectModePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._relay = _QuarantineSignal()
        self._relay.fileQuarantined.connect(self._onFileQuarantined)
        self._watcher = ProtectWatcher(self._relay)
        self.buildUi()

    def buildUi(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        headerTitle = QLabel(
            "<b style='font-size: 16px;'>Protect Mode</b>"
        )
        layout.addWidget(headerTitle)

        descLabel = QLabel(
            "When enabled, every new file that appears in your monitored "
            "folders is automatically moved to quarantine with limited access. "
            "You can review, restore, or delete quarantined files below."
        )
        descLabel.setWordWrap(True)
        descLabel.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(descLabel)

        # Status card
        statusCard = QFrame()
        statusCard.setObjectName("fileCard")
        statusLayout = QVBoxLayout(statusCard)
        statusLayout.setContentsMargins(14, 14, 14, 14)

        self.statusLabel = QLabel("Protect Mode is <b>inactive</b>.")
        self.statusLabel.setStyleSheet("font-size: 13px;")
        statusLayout.addWidget(self.statusLabel)

        layout.addWidget(statusCard)

        # Toggle button
        self.toggleBtn = QPushButton("Enable Protect Mode")
        self.toggleBtn.setObjectName("analyzeBtn")
        self.toggleBtn.clicked.connect(self.onToggle)
        layout.addWidget(self.toggleBtn)

        # Quarantine list
        layout.addWidget(QLabel("<b>Quarantined Files</b>"))

        self.fileList = QListWidget()
        self.fileList.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.fileList)

        btnRow = QHBoxLayout()
        btnRow.setSpacing(10)

        refreshBtn = QPushButton("Refresh List")
        refreshBtn.clicked.connect(self.refreshQuarantineList)
        btnRow.addWidget(refreshBtn)

        restoreBtn = QPushButton("Restore Selected")
        restoreBtn.clicked.connect(self.onRestore)
        btnRow.addWidget(restoreBtn)

        deleteAllBtn = QPushButton("Delete All Quarantined")
        deleteAllBtn.setObjectName("deleteBtn")
        deleteAllBtn.clicked.connect(self.onDeleteAll)
        btnRow.addWidget(deleteAllBtn)

        layout.addLayout(btnRow)
        self.setLayout(layout)

        # Populate on first show
        self.refreshQuarantineList()

    # -- toggle --------------------------------------------------------------

    def onToggle(self):
        if self._watcher.isRunning():
            self._watcher.stop()
            self.toggleBtn.setText("Enable Protect Mode")
            self.statusLabel.setText("Protect Mode is <b>inactive</b>.")
            self.statusLabel.setStyleSheet("font-size: 13px; color: #475569;")
        else:
            config = loadConfig()
            paths = config.get("watchedPaths", [])
            if not paths:
                QMessageBox.warning(
                    self,
                    "No Folders",
                    "Add at least one monitored folder in Settings before "
                    "enabling Protect Mode.",
                )
                return
            self._watcher.start(paths)
            self.toggleBtn.setText("Disable Protect Mode")
            self.statusLabel.setText(
                f"Protect Mode is <b style='color:#059669;'>active</b> — "
                f"watching {len(paths)} folder(s)."
            )
            self.statusLabel.setStyleSheet("font-size: 13px;")

    # -- quarantine list -----------------------------------------------------

    def refreshQuarantineList(self):
        self.fileList.clear()
        qDir = getQuarantineDir()
        try:
            entries = sorted(os.listdir(qDir))
        except OSError:
            return
        for name in entries:
            fullPath = os.path.join(qDir, name)
            if os.path.isfile(fullPath):
                item = QListWidgetItem(name)
                item.setData(256, fullPath)  # Qt.UserRole == 256
                self.fileList.addItem(item)

    def _onFileQuarantined(self, destPath):
        """Slot called on the main thread when a file is quarantined."""
        name = os.path.basename(destPath)
        item = QListWidgetItem(name)
        item.setData(256, destPath)
        self.fileList.addItem(item)

    # -- restore -------------------------------------------------------------

    def onRestore(self):
        selected = self.fileList.selectedItems()
        if not selected:
            QMessageBox.information(
                self, "No Selection", "Select one or more files to restore."
            )
            return

        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads, exist_ok=True)

        restored = 0
        for item in selected:
            src = item.data(256)
            if not src or not os.path.isfile(src):
                continue
            # Strip the timestamp prefix (YYYYMMDD-HHMMSS-ffffff_) to recover
            # the original file name.
            baseName = os.path.basename(src)
            parts = baseName.split("_", 1)
            originalName = parts[1] if len(parts) > 1 else baseName

            dest = os.path.join(downloads, originalName)
            # Avoid overwriting: append a counter if needed.
            counter = 1
            root, ext = os.path.splitext(dest)
            while os.path.exists(dest):
                dest = f"{root} ({counter}){ext}"
                counter += 1

            try:
                import stat
                os.chmod(src, stat.S_IWRITE | stat.S_IREAD)
                import shutil
                shutil.move(src, dest)
                restored += 1
            except Exception:
                pass

        self.refreshQuarantineList()
        QMessageBox.information(
            self,
            "Restored",
            f"{restored} file(s) restored to:\n{downloads}",
        )

    # -- delete all ----------------------------------------------------------

    def onDeleteAll(self):
        if self.fileList.count() == 0:
            QMessageBox.information(
                self, "Empty", "Quarantine is already empty."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Delete All Quarantined Files",
            "Permanently delete ALL files in quarantine?\n\n"
            "This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        clearQuarantine()
        self.refreshQuarantineList()
        QMessageBox.information(self, "Cleared", "All quarantined files deleted.")
