import os

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QMessageBox,
)

from config.settings import loadConfig, saveConfig
from config.protection import getQuarantineDir, clearQuarantine
from StartupAndWatcher.startup import enableStartup, disableStartup


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = loadConfig()
        self.buildUi()

    def buildUi(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Monitored Folders</b>"))

        self.pathList = QListWidget()
        for p in self.config.get("watchedPaths", []):
            self.pathList.addItem(p)
        layout.addWidget(self.pathList)

        btnRow = QHBoxLayout()
        addBtn = QPushButton("Add Folder...")
        addBtn.clicked.connect(self.onAddFolder)
        btnRow.addWidget(addBtn)

        removeBtn = QPushButton("Remove Selected")
        removeBtn.clicked.connect(self.onRemoveSelected)
        btnRow.addWidget(removeBtn)
        layout.addLayout(btnRow)

        self.startupCheck = QCheckBox("Start XenIroh automatically when Windows boots")
        self.startupCheck.setChecked(self.config.get("startAtLogin", True))
        layout.addWidget(self.startupCheck)

        layout.addWidget(QLabel("<b>Quarantine Management</b>"))
        self.quarantineLabel = QLabel(f"Location: {getQuarantineDir()}")
        layout.addWidget(self.quarantineLabel)

        clearBtn = QPushButton("Empty Quarantine Folder")
        clearBtn.clicked.connect(self.onClearQuarantine)
        layout.addWidget(clearBtn)

        saveBtn = QPushButton("Apply Settings")
        saveBtn.clicked.connect(self.onSave)
        layout.addWidget(saveBtn)

        self.setLayout(layout)

    def onAddFolder(self):
        p = QFileDialog.getExistingDirectory(self, "Choose folder")
        if p:
            current = [self.pathList.item(i).text() for i in range(self.pathList.count())]
            if p not in current:
                self.pathList.addItem(p)

    def onRemoveSelected(self):
        for item in self.pathList.selectedItems():
            self.pathList.takeItem(self.pathList.row(item))

    def onClearQuarantine(self):
        confirm = QMessageBox.question(
            self,
            "Clear Quarantine",
            "Permanently delete all files in quarantine?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            clearQuarantine()
            QMessageBox.information(self, "Cleared", "Quarantine cleared.")

    def onSave(self):
        watched = [self.pathList.item(i).text() for i in range(self.pathList.count())]
        self.config["watchedPaths"] = watched
        startAtLogin = self.startupCheck.isChecked()
        self.config["startAtLogin"] = startAtLogin
        saveConfig(self.config)

        if startAtLogin:
            enableStartup()
        else:
            disableStartup()

        QMessageBox.information(self, "Saved", "Settings saved successfully.")
