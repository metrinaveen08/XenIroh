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

from config.settings import loadConfig, saveConfig

COMMON_SUGGESTIONS = ["Downloads", "Desktop"]


def getSuggestedPaths():
    home = os.path.expanduser("~")
    suggestions = []
    for f in COMMON_SUGGESTIONS:
        candidate = os.path.join(home, f)
        if os.path.isdir(candidate):
            suggestions.append(candidate)
    return suggestions


class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("XenIroh Setup")
        self.resize(500, 380)
        self.config = loadConfig()
        self.buildUi()

    def buildUi(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Choose folders for XenIroh to monitor:"))

        self.pathList = QListWidget()
        for p in self.config.get("watchedPaths", []):
            self.pathList.addItem(p)
        layout.addWidget(self.pathList)

        sugRow = QHBoxLayout()
        for p in getSuggestedPaths():
            if self.config.get("watchedPaths") and p in self.config["watchedPaths"]:
                continue
            btn = QPushButton(f"Add {os.path.basename(p)}")
            btn.clicked.connect(lambda _, path=p: self.addPath(path))
            sugRow.addWidget(btn)
        layout.addLayout(sugRow)

        btnRow = QHBoxLayout()
        addBtn = QPushButton("Add Folder...")
        addBtn.clicked.connect(self.onAddFolder)
        btnRow.addWidget(addBtn)

        removeBtn = QPushButton("Remove Selected")
        removeBtn.clicked.connect(self.onRemoveSelected)
        btnRow.addWidget(removeBtn)
        layout.addLayout(btnRow)

        self.startupCheck = QCheckBox("Start XenIroh automatically at login")
        self.startupCheck.setChecked(self.config.get("startAtLogin", True))
        layout.addWidget(self.startupCheck)

        saveBtn = QPushButton("Save & Finish")
        saveBtn.clicked.connect(self.onSave)
        layout.addWidget(saveBtn)

        self.setLayout(layout)

    def addPath(self, path):
        current = [self.pathList.item(i).text() for i in range(self.pathList.count())]
        if path not in current:
            self.pathList.addItem(path)

    def onAddFolder(self):
        p = QFileDialog.getExistingDirectory(self, "Choose folder")
        if p:
            self.addPath(p)

    def onRemoveSelected(self):
        for item in self.pathList.selectedItems():
            self.pathList.takeItem(self.pathList.row(item))

    def onSave(self):
        watched = [self.pathList.item(i).text() for i in range(self.pathList.count())]
        self.config["watchedPaths"] = watched
        self.config["startAtLogin"] = self.startupCheck.isChecked()
        self.config["setupComplete"] = True
        saveConfig(self.config)
        self.accept()
