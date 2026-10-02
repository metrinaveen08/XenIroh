from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QTextEdit,
)

from Ai.probabilityandrules.rules_advisor import RULE_CATALOG
from config.rules import loadPrivateRules, savePrivateRules, getPublicRulesPath


class RulesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.unlockedPolicy = None
        self.currentPassword = None
        self.buildUi()

    def buildUi(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Protection Policy & Rules</b>"))

        self.rulesList = QListWidget()
        for ruleId, info in RULE_CATALOG.items():
            item = QListWidgetItem(f"[{ruleId}] {info['title']} - {info['description']}")
            self.rulesList.addItem(item)
        layout.addWidget(self.rulesList)

        passRow = QHBoxLayout()
        self.passInput = QLineEdit()
        self.passInput.setPlaceholderText("Enter developer/admin access password...")
        self.passInput.setEchoMode(QLineEdit.Password)
        passRow.addWidget(self.passInput)

        unlockBtn = QPushButton("Unlock Policy")
        unlockBtn.clicked.connect(self.onUnlock)
        passRow.addWidget(unlockBtn)
        layout.addLayout(passRow)

        self.statusBox = QTextEdit()
        self.statusBox.setReadOnly(True)
        self.loadPublicSummary()
        layout.addWidget(self.statusBox)

        self.setLayout(layout)

    def loadPublicSummary(self):
        try:
            with open(getPublicRulesPath(), "r", encoding="utf-8") as f:
                self.statusBox.setPlainText(f.read())
        except Exception:
            self.statusBox.setPlainText("No public rules summary file generated yet.")

    def onUnlock(self):
        pwd = self.passInput.text().strip()
        if not pwd:
            QMessageBox.warning(self, "Password Required", "Please enter your password.")
            return

        try:
            policy = loadPrivateRules(pwd)
            self.unlockedPolicy = policy
            self.currentPassword = pwd
            self.statusBox.setPlainText(
                f"Policy Unlocked Successfully!\nOwner: {policy.get('accessOwner')}\n"
                f"Enabled rules: {policy.get('enabledRules', [])}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to decrypt private rules: {exc}")
