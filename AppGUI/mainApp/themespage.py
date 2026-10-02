from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QApplication,
)

from config.settings import loadConfig, saveConfig

THEMES = {
    "Green / White": """
        QMainWindow, QWidget {
            background-color: #f8fafc;
            color: #0f172a;
            font-family: 'Segoe UI', -apple-system, sans-serif;
            font-size: 13px;
        }
        QLabel {
            color: #0f172a;
        }
        QFrame#sidebar {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
        QFrame#fileCard {
            background-color: #ffffff;
            border: 2px dashed #059669;
            border-radius: 8px;
            padding: 14px;
        }
        QLabel#pathLabel {
            color: #475569;
            font-size: 13px;
        }
        QPushButton {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #ecfdf5;
            border-color: #059669;
            color: #065f46;
        }
        QPushButton:pressed {
            background-color: #d1fae5;
        }
        QPushButton:disabled {
            background-color: #f1f5f9;
            color: #94a3b8;
            border-color: #e2e8f0;
        }
        QPushButton#analyzeBtn, QPushButton#primaryBtn {
            background-color: #059669;
            color: #ffffff;
            border: 1px solid #047857;
            font-weight: 600;
        }
        QPushButton#analyzeBtn:hover, QPushButton#primaryBtn:hover {
            background-color: #047857;
        }
        QPushButton#analyzeBtn:disabled, QPushButton#primaryBtn:disabled {
            background-color: #a7f3d0;
            color: #ffffff;
            border-color: #a7f3d0;
        }
        QPushButton#deleteBtn {
            background-color: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fca5a5;
        }
        QPushButton#deleteBtn:hover {
            background-color: #fecaca;
        }
        QPushButton#deleteBtn:disabled {
            background-color: #f8fafc;
            color: #cbd5e1;
            border-color: #e2e8f0;
        }
        QTextEdit, QListWidget, QLineEdit {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 8px;
        }
        QListWidget#navSidebar {
            background-color: #ffffff;
            border: none;
            padding: 8px;
        }
        QListWidget#navSidebar::item {
            padding: 10px 14px;
            margin: 2px 0px;
            border-radius: 6px;
            color: #334155;
            font-weight: 500;
        }
        QListWidget#navSidebar::item:hover {
            background-color: #ecfdf5;
            color: #047857;
        }
        QListWidget#navSidebar::item:selected {
            background-color: #059669;
            color: #ffffff;
            font-weight: 600;
        }
        QScrollBar:vertical {
            border: none;
            background: #f1f5f9;
            width: 8px;
        }
        QScrollBar::handle:vertical {
            background: #cbd5e1;
            border-radius: 4px;
        }
    """,
    "Dark Emerald": """
        QMainWindow, QWidget {
            background-color: #111827;
            color: #f9fafb;
            font-family: 'Segoe UI', -apple-system, sans-serif;
            font-size: 13px;
        }
        QLabel { color: #f9fafb; }
        QFrame#sidebar { background-color: #1f2937; border-right: 1px solid #374151; }
        QFrame#fileCard { background-color: #1f2937; border: 2px dashed #10b981; border-radius: 8px; padding: 14px; }
        QLabel#pathLabel { color: #9ca3af; font-size: 13px; }
        QPushButton {
            background-color: #1f2937;
            color: #f9fafb;
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 8px 16px;
        }
        QPushButton:hover { background-color: #374151; border-color: #10b981; }
        QPushButton#analyzeBtn, QPushButton#primaryBtn { background-color: #059669; color: #ffffff; border: 1px solid #047857; }
        QPushButton#analyzeBtn:hover, QPushButton#primaryBtn:hover { background-color: #047857; }
        QPushButton#deleteBtn { background-color: #7f1d1d; color: #fecaca; border: 1px solid #991b1b; }
        QTextEdit, QListWidget, QLineEdit { background-color: #1f2937; color: #f9fafb; border: 1px solid #374151; border-radius: 6px; }
        QListWidget#navSidebar { background-color: #1f2937; border: none; }
        QListWidget#navSidebar::item { padding: 10px 14px; margin: 2px 0px; border-radius: 6px; color: #d1d5db; }
        QListWidget#navSidebar::item:hover { background-color: #064e3b; color: #a7f3d0; }
        QListWidget#navSidebar::item:selected { background-color: #059669; color: #ffffff; font-weight: 600; }
    """,
    "Light Clean": """
        QMainWindow, QWidget { background-color: #f7f9fa; color: #222222; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
        QPushButton { background-color: #e2e8f0; color: #1a202c; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 6px; }
        QPushButton:hover { background-color: #cbd5e1; }
        QPushButton#analyzeBtn, QPushButton#primaryBtn { background-color: #2563eb; color: #ffffff; border: 1px solid #1d4ed8; }
        QTextEdit, QListWidget, QLineEdit { background-color: #ffffff; color: #1e293b; border: 1px solid #cbd5e1; border-radius: 6px; }
        QListWidget#navSidebar { background-color: #ffffff; border-right: 1px solid #cbd5e1; }
        QListWidget#navSidebar::item:selected { background-color: #2563eb; color: #ffffff; font-weight: 600; }
    """
}

DEFAULT_THEME_NAME = "Green / White"


def applyTheme(themeName=None):
    if not themeName:
        config = loadConfig()
        themeName = config.get("theme", DEFAULT_THEME_NAME)
    qss = THEMES.get(themeName, THEMES[DEFAULT_THEME_NAME])
    app = QApplication.instance()
    if app:
        app.setStyleSheet(qss)


class ThemesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buildUi()

    def buildUi(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(QLabel("<b style='font-size: 15px;'>Visual Theme Selection</b>"))

        self.themeCombo = QComboBox()
        for name in THEMES.keys():
            self.themeCombo.addItem(name)

        config = loadConfig()
        savedTheme = config.get("theme", DEFAULT_THEME_NAME)
        idx = self.themeCombo.findText(savedTheme)
        if idx >= 0:
            self.themeCombo.setCurrentIndex(idx)

        layout.addWidget(self.themeCombo)

        applyBtn = QPushButton("Apply Theme")
        applyBtn.setObjectName("primaryBtn")
        applyBtn.clicked.connect(self.onApply)
        layout.addWidget(applyBtn)

        layout.addStretch()
        self.setLayout(layout)

    def onApply(self):
        chosen = self.themeCombo.currentText()
        applyTheme(chosen)
        config = loadConfig()
        config["theme"] = chosen
        saveConfig(config)
