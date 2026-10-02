from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)

from Ai.chatandagents.chat import welcome_message, respond


class ChatPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.evidence = None
        self.result = None
        self.buildUi()

    def buildUi(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Local Security Guide Chat</b> (100% On-Device)"))

        self.chatLog = QTextEdit()
        self.chatLog.setReadOnly(True)
        self.chatLog.append(f"Guide: {welcome_message()}\n")
        layout.addWidget(self.chatLog)

        inputRow = QHBoxLayout()
        self.msgInput = QLineEdit()
        self.msgInput.setPlaceholderText("Ask a question about a file verdict, rule, or warning...")
        self.msgInput.returnPressed.connect(self.onSend)
        inputRow.addWidget(self.msgInput)

        sendBtn = QPushButton("Send")
        sendBtn.clicked.connect(self.onSend)
        inputRow.addWidget(sendBtn)

        layout.addLayout(inputRow)
        self.setLayout(layout)

    def setAnalysisContext(self, evidence, result):
        self.evidence = evidence
        self.result = result
        if result:
            self.chatLog.append(
                f"Guide: File '{evidence.get('path')}' analyzed -> Verdict: {result.get('verdict')}\n"
            )

    def onSend(self):
        text = self.msgInput.text().strip()
        if not text:
            return

        self.chatLog.append(f"You: {text}")
        self.msgInput.clear()

        reply = respond(text, self.evidence, self.result)
        self.chatLog.append(f"Guide: {reply}\n")
