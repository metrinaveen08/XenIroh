"""
GUI/TrayApp.py

The actual "always running" XenIroh. Lives in the system tray. On launch:
    - if setup hasn't been completed, shows SetupDialog first
    - starts FolderWatcher on the configured paths
    - shows a tray balloon alert whenever a new file is analyzed as
      Suspicious
    - lets the user open the manual analyzer window, reopen settings,
      pause/resume monitoring, or quit

This is the file main.py should launch by default.
"""

import sys

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QStyle
from PyQt5.QtCore import QObject, pyqtSignal

from Config.settings import loadConfig, isSetupComplete
from Startup.startup import enableStartup, disableStartup
from Watcher.watcher import FolderWatcher
from GUI.SetupDialog import SetupDialog
from GUI.XenIroh import XenIrohWindow


class WatcherSignalRelay(QObject):
    """FolderWatcher's callback fires on a background thread; Qt widgets
    must only be touched from the main thread. This relay uses a Qt signal
    to safely hop back onto the main thread before showing any UI."""
    resultReady = pyqtSignal(str, dict, dict)


class TrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.analyzerWindow = None
        self.relay = WatcherSignalRelay()
        self.relay.resultReady.connect(self.onAnalysisResult)

        self.watcher = FolderWatcher(onResultCallback=self.onWatcherResult)

        self.trayIcon = QSystemTrayIcon()
        icon = self.app.style().standardIcon(QStyle.SP_ComputerIcon)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setToolTip("XenIroh - active protection")

        self.buildMenu()
        self.trayIcon.show()

        self.ensureSetupThenStart()

    def buildMenu(self):
        menu = QMenu()

        openAction = QAction("Open XenIroh", self.app)
        openAction.triggered.connect(self.openAnalyzerWindow)
        menu.addAction(openAction)

        settingsAction = QAction("Settings...", self.app)
        settingsAction.triggered.connect(self.openSettings)
        menu.addAction(settingsAction)

        self.toggleAction = QAction("Pause Monitoring", self.app)
        self.toggleAction.triggered.connect(self.toggleMonitoring)
        menu.addAction(self.toggleAction)

        menu.addSeparator()

        quitAction = QAction("Quit XenIroh", self.app)
        quitAction.triggered.connect(self.quit)
        menu.addAction(quitAction)

        self.trayIcon.setContextMenu(menu)
        self.trayIcon.activated.connect(self.onTrayActivated)

    def ensureSetupThenStart(self):
        if not isSetupComplete():
            dialog = SetupDialog()
            dialog.exec_()

        config = loadConfig()

        if config.get("startAtLogin", True):
            enableStartup()
        else:
            disableStartup()

        self.startMonitoring()

    def startMonitoring(self):
        config = loadConfig()
        self.watcher.start(config.get("watchedPaths", []))
        self.toggleAction.setText("Pause Monitoring")
        self.trayIcon.setToolTip(
            f"XenIroh - watching {len(config.get('watchedPaths', []))} folder(s)"
        )

    def toggleMonitoring(self):
        if self.watcher.isRunning():
            self.watcher.stop()
            self.toggleAction.setText("Resume Monitoring")
            self.trayIcon.setToolTip("XenIroh - monitoring paused")
        else:
            self.startMonitoring()

    def onWatcherResult(self, path, evidence, aiResult):
        # Called on the watcher's background thread - just relay via signal.
        self.relay.resultReady.emit(path, evidence, aiResult)

    def onAnalysisResult(self, path, evidence, aiResult):
        verdict = aiResult.get("verdict", "Unknown")

        if verdict == "Suspicious":
            icon = QSystemTrayIcon.Warning
            title = "XenIroh - Suspicious file detected"
        elif verdict == "Inconclusive":
            icon = QSystemTrayIcon.Information
            title = "XenIroh - Inconclusive result"
        else:
            return  # don't interrupt the user for files deemed safe

        message = f"{path}\n{aiResult.get('conclusion', '')}"
        self.trayIcon.showMessage(title, message[:250], icon, 8000)

        self._lastFlaggedPath = path

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.openAnalyzerWindow(preloadPath=getattr(self, "_lastFlaggedPath", None))

    def openAnalyzerWindow(self, preloadPath=None):
        if self.analyzerWindow is None:
            self.analyzerWindow = XenIrohWindow()
        self.analyzerWindow.show()
        self.analyzerWindow.raise_()
        self.analyzerWindow.activateWindow()
        if preloadPath:
            self.analyzerWindow.analyzePath(preloadPath)

    def openSettings(self):
        dialog = SetupDialog()
        if dialog.exec_():
            self.startMonitoring()  # restart watcher with the updated folder list

    def quit(self):
        self.watcher.stop()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec_())


def launchTrayApp():
    trayApp = TrayApp()
    trayApp.run()


if __name__ == "__main__":
    launchTrayApp()
