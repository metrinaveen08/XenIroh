import os
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QMessageBox,
    QFrame,
    QListWidget,
    QStackedWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from Assets.Analyzers.FileAnalyzer import analyzeFile
from Assets.Analyzers.ImageAnalyzer import analyzeImage
from Assets.AiConnector.aibridge import callAiAgent, formatReport
from config.permissions import isRunningAsAdmin
from AppGUI.mainApp.chatpage import ChatPage
from AppGUI.mainApp.rulespage import RulesPage
from AppGUI.mainApp.themespage import ThemesPage, applyTheme
from AppGUI.mainApp.settings import SettingsPage
from AppGUI.mainApp.protectmode import ProtectModePage

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}


class XenIrohApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.currentPath = None
        self.currentVerdict = None

        self.setWindowTitle("XenIroh Security Platform")
        self.setMinimumSize(850, 600)
        self.resize(920, 650)
        self.setAcceptDrops(True)

        self.buildUi()
        applyTheme()

    def buildUi(self):
        central = QWidget()
        rootLayout = QHBoxLayout(central)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # 1. Left Sidebar Navigation
        sidebarFrame = QFrame()
        sidebarFrame.setObjectName("sidebar")
        sidebarFrame.setFixedWidth(210)
        sidebarLayout = QVBoxLayout(sidebarFrame)
        sidebarLayout.setContentsMargins(12, 16, 12, 16)
        sidebarLayout.setSpacing(10)

        brandLabel = QLabel("<b>XenIroh</b>")
        brandLabel.setStyleSheet("font-size: 18px; color: #059669; padding-left: 6px;")
        sidebarLayout.addWidget(brandLabel)

        subLabel = QLabel("Security Analyzer")
        subLabel.setStyleSheet("font-size: 11px; color: #64748b; padding-left: 6px; margin-bottom: 8px;")
        sidebarLayout.addWidget(subLabel)

        self.navSidebar = QListWidget()
        self.navSidebar.setObjectName("navSidebar")
        self.navSidebar.addItem("Scanner")
        self.navSidebar.addItem("Security Chat")
        self.navSidebar.addItem("Rules")
        self.navSidebar.addItem("Themes")
        self.navSidebar.addItem("Settings")
        self.navSidebar.addItem("Protect Mode")
        self.navSidebar.setCurrentRow(0)
        self.navSidebar.currentRowChanged.connect(self.onNavChanged)
        sidebarLayout.addWidget(self.navSidebar)

        sidebarLayout.addStretch()
        rootLayout.addWidget(sidebarFrame)

        # 2. Main Content Stack
        self.stack = QStackedWidget()

        # Page 0: File Scanner
        scannerPage = QWidget()
        scanLayout = QVBoxLayout(scannerPage)
        scanLayout.setContentsMargins(24, 20, 24, 20)
        scanLayout.setSpacing(14)

        headerTitle = QLabel("<b style='font-size: 16px;'>File Inspection & Static Analysis</b>")
        scanLayout.addWidget(headerTitle)

        self.fileCard = QFrame()
        self.fileCard.setObjectName("fileCard")
        cardLayout = QVBoxLayout(self.fileCard)
        cardLayout.setContentsMargins(18, 18, 18, 18)

        self.pathLabel = QLabel("No file selected. Choose or drop a file to analyze.")
        self.pathLabel.setObjectName("pathLabel")
        self.pathLabel.setWordWrap(True)
        self.pathLabel.setAlignment(Qt.AlignCenter)
        cardLayout.addWidget(self.pathLabel)
        scanLayout.addWidget(self.fileCard)

        btnRow = QHBoxLayout()
        btnRow.setSpacing(10)

        chooseButton = QPushButton("Choose File...")
        chooseButton.clicked.connect(self.onChooseFile)
        btnRow.addWidget(chooseButton)

        self.analyzeButton = QPushButton("Analyze File")
        self.analyzeButton.setObjectName("analyzeBtn")
        self.analyzeButton.setEnabled(False)
        self.analyzeButton.clicked.connect(self.onAnalyze)
        btnRow.addWidget(self.analyzeButton)

        self.deleteButton = QPushButton("Delete File")
        self.deleteButton.setObjectName("deleteBtn")
        self.deleteButton.setEnabled(False)
        self.deleteButton.clicked.connect(self.onDelete)
        btnRow.addWidget(self.deleteButton)
        scanLayout.addLayout(btnRow)

        self.reportBox = QTextEdit()
        self.reportBox.setReadOnly(True)
        self.reportBox.setFont(QFont("Consolas", 10))
        self.reportBox.setPlaceholderText("Analysis report and findings will appear here.")
        scanLayout.addWidget(self.reportBox)

        if isRunningAsAdmin():
            warnLabel = QLabel(
                "Warning: XenIroh is running with administrator privileges. "
                "Run as a standard user for static analysis."
            )
            warnLabel.setStyleSheet("color: #d97706; font-size: 12px; font-weight: bold;")
            scanLayout.addWidget(warnLabel)

        self.stack.addWidget(scannerPage)

        # Page 1: Security Chat
        self.chatPage = ChatPage()
        self.stack.addWidget(self.chatPage)

        # Page 2: Rules
        self.rulesPage = RulesPage()
        self.stack.addWidget(self.rulesPage)

        # Page 3: Themes
        self.themesPage = ThemesPage()
        self.stack.addWidget(self.themesPage)

        # Page 4: Settings
        self.settingsPage = SettingsPage()
        self.stack.addWidget(self.settingsPage)

        # Page 5: Protect Mode
        self.protectModePage = ProtectModePage()
        self.stack.addWidget(self.protectModePage)

        rootLayout.addWidget(self.stack)
        self.setCentralWidget(central)

    def onNavChanged(self, index):
        self.stack.setCurrentIndex(index)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isfile(path):
                self.navSidebar.setCurrentRow(0)
                self.setSelectedFile(path)
                self.analyzePath(path)

    def onChooseFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a file to analyze")
        if path:
            self.setSelectedFile(path)

    def setSelectedFile(self, path):
        self.currentPath = path
        self.pathLabel.setText(f"<b>Selected:</b> {path}")
        self.pathLabel.setStyleSheet("color: #059669; font-size: 13px;")
        self.analyzeButton.setEnabled(True)
        self.deleteButton.setEnabled(False)
        self.reportBox.clear()

    def onAnalyze(self):
        if self.currentPath:
            self.analyzePath(self.currentPath)

    def analyzePath(self, path):
        self.navSidebar.setCurrentRow(0)
        self.setSelectedFile(path)

        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            evidence = analyzeImage(path)
        else:
            evidence = analyzeFile(path)

        aiResult = callAiAgent(evidence)
        self.currentVerdict = aiResult.get("verdict")

        report = formatReport(evidence, aiResult)
        self.reportBox.setPlainText(report)
        self.deleteButton.setEnabled(self.currentVerdict == "Suspicious")

        self.chatPage.setAnalysisContext(evidence, aiResult)

    def onDelete(self):
        if not self.currentPath or not os.path.exists(self.currentPath):
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Permanently delete this suspicious file?\n\n{self.currentPath}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            os.remove(self.currentPath)
            QMessageBox.information(self, "Deleted", "File was deleted.")
            self.pathLabel.setText("No file selected. Choose or drop a file to analyze.")
            self.pathLabel.setStyleSheet("color: #475569; font-size: 13px;")
            self.reportBox.clear()
            self.currentPath = None
            self.analyzeButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not delete file: {exc}")


def launchGui():
    app = QApplication(sys.argv)
    window = XenIrohApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launchGui()
