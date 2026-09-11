"""
GUI/SetupDialog.py

Shown on first run (and reopenable from the tray icon's "Settings"). Lets
the user choose which folders XenIroh should actively monitor, and whether
XenIroh should start automatically at login. Nothing is watched until the
user has explicitly chosen it here.
"""

import os

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QCheckBox,
    QFileDialog,
)

from Config.settings import loadConfig, saveConfig

COMMON_SUGGESTIONS = ["Downloads", "Desktop"]


def getSuggestedPaths():
    home = os.path.expanduser("~")
    suggestions = []
    for folderName in COMMON_SUGGESTIONS:
        candidate = os.path.join(home, folderName)
        if os.path.isdir(candidate):
            suggestions.append(candidate)
    return suggestions


class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("XenIroh Setup")
        self.setMinimumSize(480, 360)
        self.config = loadConfig()
        self.buildUi()

    def buildUi(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel(
            "Choose the folders XenIroh should watch. New files placed in "
            "these folders will be analyzed automatically."
        ))

        self.pathList = QListWidget()
        for path in self.config.get("watchedPaths", []):
            self.pathList.addItem(path)
        layout.addWidget(self.pathList)

        suggestionRow = QHBoxLayout()
        for suggestedPath in getSuggestedPaths():
            if self.config.get("watchedPaths") and suggestedPath in self.config["watchedPaths"]:
                continue
            suggestButton = QPushButton(f"Add {os.path.basename(suggestedPath)}")
            suggestButton.clicked.connect(
                lambda _checked, p=suggestedPath: self.addPath(p)
            )
            suggestionRow.addWidget(suggestButton)
        layout.addLayout(suggestionRow)

        buttonRow = QHBoxLayout()
        addButton = QPushButton("Add Custom Folder...")
        addButton.clicked.connect(self.onAddCustomFolder)
        buttonRow.addWidget(addButton)

        removeButton = QPushButton("Remove Selected")
        removeButton.clicked.connect(self.onRemoveSelected)
        buttonRow.addWidget(removeButton)
        layout.addLayout(buttonRow)

        self.startupCheckbox = QCheckBox("Start XenIroh automatically when Windows starts")
        self.startupCheckbox.setChecked(self.config.get("startAtLogin", True))
        layout.addWidget(self.startupCheckbox)

        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.onSave)
        layout.addWidget(saveButton)

        self.setLayout(layout)

    def addPath(self, path):
        existingPaths = [self.pathList.item(i).text() for i in range(self.pathList.count())]
        if path not in existingPaths:
            self.pathList.addItem(path)

    def onAddCustomFolder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose a folder to watch")
        if path:
            self.addPath(path)

    def onRemoveSelected(self):
        for item in self.pathList.selectedItems():
            self.pathList.takeItem(self.pathList.row(item))

    def onSave(self):
        watchedPaths = [self.pathList.item(i).text() for i in range(self.pathList.count())]

        self.config["watchedPaths"] = watchedPaths
        self.config["startAtLogin"] = self.startupCheckbox.isChecked()
        self.config["setupComplete"] = True
        saveConfig(self.config)

        self.accept()
