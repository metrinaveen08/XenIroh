"""
GUI/XenIroh.py

PyQt5 front end. Responsibilities:
    - let the user pick a file (or drop one) to check
    - call Assets.FileAnalyzer / Assets.ImageAnalyzer to collect evidence
    - hand that evidence to AI.agent for reasoning
    - display the explainable result
    - offer to delete the file if the verdict is suspicious

This file should stay UI wiring only. Analysis logic lives in Assets/,
reasoning lives in AI/.
"""

import os
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QMessageBox,
)
from PyQt5.QtCore import Qt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Assets.FileAnalyzer import analyzeFile
from Assets.ImageAnalyzer import analyzeImage
from Assets.AiBridge import callAiAgent, formatReport
from DevicePermissions.permissions import describePrivilegeContext

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}


class XenIrohWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.currentPath = None
        self.currentVerdict = None
        self.buildUi()

    def buildUi(self):
        self.setWindowTitle("XenIroh")
        self.setMinimumSize(640, 480)
        self.setAcceptDrops(True)

        layout = QVBoxLayout()

        self.pathLabel = QLabel("No file selected. Choose or drop a file to analyze.")
        self.pathLabel.setWordWrap(True)
        layout.addWidget(self.pathLabel)

        buttonRow = QHBoxLayout()
        chooseButton = QPushButton("Choose File...")
        chooseButton.clicked.connect(self.onChooseFile)
        buttonRow.addWidget(chooseButton)

        self.analyzeButton = QPushButton("Analyze")
        self.analyzeButton.setEnabled(False)
        self.analyzeButton.clicked.connect(self.onAnalyze)
        buttonRow.addWidget(self.analyzeButton)

        self.deleteButton = QPushButton("Delete File")
        self.deleteButton.setEnabled(False)
        self.deleteButton.clicked.connect(self.onDelete)
        buttonRow.addWidget(self.deleteButton)

        layout.addLayout(buttonRow)

        self.reportBox = QTextEdit()
        self.reportBox.setReadOnly(True)
        self.reportBox.setPlaceholderText("Analysis report will appear here.")
        layout.addWidget(self.reportBox)

        privilegeInfo = describePrivilegeContext()
        if privilegeInfo["runningAsAdmin"]:
            warnLabel = QLabel(
                "Warning: XenIroh is running with administrator privileges. "
                "Run as a standard user for static analysis."
            )
            warnLabel.setStyleSheet("color: #b00;")
            layout.addWidget(warnLabel)

        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.setSelectedFile(urls[0].toLocalFile())

    def onChooseFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a file to analyze")
        if path:
            self.setSelectedFile(path)

    def setSelectedFile(self, path):
        self.currentPath = path
        self.pathLabel.setText(f"Selected: {path}")
        self.analyzeButton.setEnabled(True)
        self.deleteButton.setEnabled(False)
        self.reportBox.clear()

    def onAnalyze(self):
        if not self.currentPath:
            return
        self.analyzePath(self.currentPath)

    def analyzePath(self, path):
        """Run analysis on a specific path and populate the window with the
        result. Used both by the "Analyze" button and by the tray app when
        opening a report for a file the background watcher already flagged."""
        self.setSelectedFile(path)

        extension = os.path.splitext(path)[1].lower()
        if extension in IMAGE_EXTENSIONS:
            evidence = analyzeImage(path)
        else:
            evidence = analyzeFile(path)

        aiResult = callAiAgent(evidence)
        self.currentVerdict = aiResult.get("verdict")

        self.reportBox.setPlainText(formatReport(evidence, aiResult))
        self.deleteButton.setEnabled(self.currentVerdict == "Suspicious")

    def onDelete(self):
        if not self.currentPath:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete this file?\n\n{self.currentPath}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            os.remove(self.currentPath)
            QMessageBox.information(self, "Deleted", "File deleted.")
            self.pathLabel.setText("No file selected. Choose or drop a file to analyze.")
            self.reportBox.clear()
            self.currentPath = None
            self.analyzeButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not delete file: {exc}")


def launchGui():
    app = QApplication(sys.argv)
    window = XenIrohWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launchGui()
