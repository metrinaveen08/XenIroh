import sys

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QStyle
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from config.settings import loadConfig, isSetupComplete
from StartupAndWatcher.startup import enableStartup, disableStartup
from StartupAndWatcher.watcher import FolderWatcher
from AppGUI.mainApp.setup import SetupDialog
from AppGUI.mainApp.App import XenIrohApp


class WatcherSignalRelay(QObject):
    resultReady = pyqtSignal(str, dict, dict)


class SingleInstance(QObject):
    SERVER_NAME = "XenIroh.SingleInstance"
    activationRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handleActivation)

    def becomePrimaryOrActivateExisting(self):
        socket = QLocalSocket(self)
        socket.connectToServer(self.SERVER_NAME)

        if socket.waitForConnected(500):
            socket.write(b"activate")
            socket.waitForBytesWritten(500)
            socket.disconnectFromServer()
            return False

        QLocalServer.removeServer(self.SERVER_NAME)
        return self.server.listen(self.SERVER_NAME)

    def _handleActivation(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.readyRead.connect(socket.deleteLater)
            socket.disconnected.connect(socket.deleteLater)
            socket.disconnectFromServer()
            self.activationRequested.emit()


class TrayApp:
    def __init__(self, app):
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)

        self.analyzerWindow = None
        self.relay = WatcherSignalRelay()
        self.relay.resultReady.connect(self.onAnalysisResult)

        self.watcher = FolderWatcher(onResultCallback=self.onWatcherResult)

        self.trayIcon = QSystemTrayIcon()
        icon = self.app.style().standardIcon(QStyle.SP_ComputerIcon)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setToolTip("XenIroh")

        self.buildMenu()
        self.trayIcon.show()

        self.ensureSetupThenStart()

    def buildMenu(self):
        menu = QMenu()

        openAction = QAction("Open XenIroh", self.app)
        openAction.triggered.connect(self.openAnalyzerWindow)
        menu.addAction(openAction)

        menu.addSeparator()

        settingsAction = QAction("Settings...", self.app)
        settingsAction.triggered.connect(self.openSettings)
        menu.addAction(settingsAction)

        menu.addSeparator()

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
        paths = config.get("watchedPaths", [])
        self.watcher.start(paths)
        self.toggleAction.setText("Pause Monitoring")
        self.trayIcon.setToolTip(f"XenIroh - watching {len(paths)} folder(s)")

    def toggleMonitoring(self):
        if self.watcher.isRunning():
            self.watcher.stop()
            self.toggleAction.setText("Resume Monitoring")
            self.trayIcon.setToolTip("XenIroh - monitoring paused")
        else:
            self.startMonitoring()

    def onWatcherResult(self, path, evidence, aiResult):
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
            return

        msg = f"{path}\n{aiResult.get('conclusion', '')}"
        self.trayIcon.showMessage(title, msg[:250], icon, 8000)
        self._lastFlaggedPath = path

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.openAnalyzerWindow(preloadPath=getattr(self, "_lastFlaggedPath", None))

    def openAnalyzerWindow(self, preloadPath=None):
        if self.analyzerWindow is None:
            self.analyzerWindow = XenIrohApp()
        self.analyzerWindow.show()
        self.analyzerWindow.raise_()
        self.analyzerWindow.activateWindow()
        if preloadPath:
            self.analyzerWindow.analyzePath(preloadPath)

    def openSettings(self):
        self.openAnalyzerWindow()
        if self.analyzerWindow and hasattr(self.analyzerWindow, "navSidebar"):
            self.analyzerWindow.navSidebar.setCurrentRow(4)

    def quit(self):
        self.watcher.stop()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec_())


def launchTrayApp():
    app = QApplication(sys.argv)
    from AppGUI.mainApp.themespage import applyTheme
    applyTheme()

    singleInstance = SingleInstance(app)

    if not singleInstance.becomePrimaryOrActivateExisting():
        return

    trayApp = TrayApp(app)
    singleInstance.activationRequested.connect(trayApp.openAnalyzerWindow)
    trayApp.openAnalyzerWindow()
    trayApp.run()


if __name__ == "__main__":
    launchTrayApp()
