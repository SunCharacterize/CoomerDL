from PySide6.QtCore import QObject, Signal, QTimer, Qt

from app.views.pyside.progress.progress_item_widget import ProgressItemWidget
from app.views.pyside.progress.progress_dialog import ProgressDialog


class ProgressSignals(QObject):
    upsert_item = Signal(str, object, object, str)
    clear_all = Signal()
    toggle_dialog = Signal()


class ProgressController:
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.tr = parent_window.tr
        self.dialog = ProgressDialog(parent_window, tr=parent_window.tr)
        self.signals = ProgressSignals()

        self.items = {}

        self.signals.upsert_item.connect(self._upsert_item)
        self.signals.clear_all.connect(self._clear_all)
        self.signals.toggle_dialog.connect(self._toggle_dialog)

    def _make_key(self, file_id: str, file_path: str) -> str:
        return f"{file_id}|{file_path}"

    def toggle_dialog(self):
        self.signals.toggle_dialog.emit()

    def update_item(self, file_id: str, file_path: str, downloaded: int, total: int, eta_text: str):
        packed_key = self._make_key(str(file_id), str(file_path))
        self.signals.upsert_item.emit(packed_key, downloaded, total, eta_text)

    def clear_all(self):
        self.signals.clear_all.emit()

    def _upsert_item(self, packed_key: str, downloaded, total, eta_text: str):
        file_id, file_path = packed_key.split("|", 1)

        downloaded = int(downloaded or 0)
        total = int(total or 0)

        if packed_key not in self.items:
            widget = ProgressItemWidget(file_path)
            self.items[packed_key] = widget
            self.dialog.container_layout.insertWidget(
                self.dialog.container_layout.count() - 1,
                widget
            )
            self.dialog.show_empty(False)

        widget = self.items[packed_key]
        widget.update_progress(downloaded, total, eta_text)

        if total > 0 and downloaded >= total:
            QTimer.singleShot(1500, lambda key=packed_key: self._remove_item(key))

    def _remove_item(self, item_key: str):
        removed_any = False

        widget = self.items.pop(item_key, None)
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
            removed_any = True
        else:
            prefix = f"{item_key}|"
            matching_keys = [key for key in list(self.items.keys()) if key.startswith(prefix)]

            for key in matching_keys:
                widget = self.items.pop(key, None)
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                    removed_any = True

        if removed_any:
            self.dialog.show_empty(len(self.items) == 0)

    def _clear_all(self):
        for item_key in list(self.items.keys()):
            self._remove_item(item_key)

    def _toggle_dialog(self):
        if self.dialog.windowState() & Qt.WindowMinimized:
            self.dialog.setWindowState(
                (self.dialog.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive
            )
            self.dialog.show()
            self.dialog.raise_()
            self.dialog.activateWindow()
            return

        if self.dialog.isVisible():
            self.dialog.hide()
        else:
            self.dialog.show()
            self.dialog.raise_()
            self.dialog.activateWindow()