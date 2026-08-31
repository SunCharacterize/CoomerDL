from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit


class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        root.addWidget(self.log_text, 1)
