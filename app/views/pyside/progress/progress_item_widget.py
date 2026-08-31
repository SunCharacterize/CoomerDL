from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar


def format_bytes(num_bytes: int) -> str:
    try:
        value = float(num_bytes or 0)
    except Exception:
        value = 0.0

    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0

    while value >= 1024 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1

    if idx == 0:
        return f"{int(value)} {units[idx]}"
    return f"{value:.2f} {units[idx]}"


class ProgressItemWidget(QWidget):
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)

        self.file_path = file_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.file_label = QLabel(file_path)
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1f1f1f;
                border: 1px solid #5a5a5a;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background-color: #16a34a;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)

        bottom = QHBoxLayout()

        self.percent_label = QLabel("0%")
        self.size_label = QLabel("0 B / 0 B")
        self.eta_label = QLabel("ETA: N/A")

        bottom.addWidget(self.percent_label)
        bottom.addSpacing(10)
        bottom.addWidget(self.size_label)
        bottom.addStretch(1)
        bottom.addWidget(self.eta_label)

        layout.addLayout(bottom)

    def update_progress(self, downloaded: int, total: int, eta_text: str = "ETA: N/A"):
        if total > 0:
            percentage = int((downloaded / total) * 100)
        else:
            percentage = 0

        self.progress_bar.setValue(percentage)
        self.percent_label.setText(f"{percentage}%")
        self.size_label.setText(f"{format_bytes(downloaded)} / {format_bytes(total)}")
        self.eta_label.setText(eta_text)