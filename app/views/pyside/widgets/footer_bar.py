from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QStyle,
    QProgressBar,
)


class FooterBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.eta_label = QLabel("ETA: N/A")
        self.eta_label.setMinimumWidth(90)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1f1f1f;
                border: 1px solid #5a5a5a;
                border-radius: 8px;
            }
            QProgressBar::chunk {
                background-color: #16a34a;
                border-radius: 8px;
            }
        """)

        self.total_size_label = QLabel("Total: 0 B")
        self.total_size_label.setMinimumWidth(130)
        self.total_size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.speed_label = QLabel("Speed: 0 KB/s")
        self.speed_label.setMinimumWidth(120)
        self.speed_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.progress_label = QLabel("0%")
        self.progress_label.setMinimumWidth(40)
        self.progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.progress_details_button = QToolButton()
        self.progress_details_button.setCursor(Qt.PointingHandCursor)
        self.progress_details_button.setToolTip("Progress Details")
        self.progress_details_button.setIcon(
            self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        )
        self.progress_details_button.setIconSize(QSize(18, 18))
        self.progress_details_button.setFixedSize(34, 34)
        self.progress_details_button.setStyleSheet("""
            QToolButton {
                border-radius: 8px;
                border: 1px solid #4a4a4a;
                background-color: #3a3a3a;
            }
            QToolButton:hover {
                background-color: #4a4a4a;
            }
        """)

        layout.addWidget(self.eta_label, 0)
        layout.addWidget(self.progress_bar, 1)
        layout.addWidget(self.total_size_label, 0)
        layout.addWidget(self.speed_label, 0)
        layout.addWidget(self.progress_label, 0)
        layout.addWidget(self.progress_details_button, 0)