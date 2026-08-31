from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QLabel


class ProgressDialog(QDialog):
    def __init__(self, parent=None, tr=None):
        super().__init__(parent)

        self.tr = tr if tr else (lambda key, **kwargs: key.format(**kwargs) if kwargs else key)

        self.setWindowTitle(self.tr("PROGRESS_DIALOG_TITLE"))
        self.resize(700, 500)
        self.setWindowFlag(Qt.Window, True)

        layout = QVBoxLayout(self)

        self.empty_label = QLabel(self.tr("PROGRESS_DIALOG_NO_ACTIVE_DOWNLOADS"))
        layout.addWidget(self.empty_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll, 1)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(8)
        self.container_layout.addStretch(1)

        self.scroll.setWidget(self.container)

    def show_empty(self, visible: bool):
        self.empty_label.setVisible(visible)

    def retranslate_ui(self):
        self.setWindowTitle(self.tr("PROGRESS_DIALOG_TITLE"))
        self.empty_label.setText(self.tr("PROGRESS_DIALOG_NO_ACTIVE_DOWNLOADS"))

    def closeEvent(self, event):
        self.hide()
        event.ignore()