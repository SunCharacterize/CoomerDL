from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
)

from app.services.settings_service import SettingsService
from app.services.translation_service import TranslationService


class StartupCommunityDialog(QDialog):
    def __init__(self, parent=None, initial_language="en"):
        super().__init__(parent)

        self.settings_service = SettingsService()
        self.translation_service = TranslationService(language=initial_language)
        self.current_language = initial_language
        self._dont_show_again = False

        self.setModal(True)
        self.setWindowTitle(self.tr_text("STARTUP_DIALOG_TITLE"))
        self.resize(700, 360)

        self._build_ui()
        self._load_languages()
        self._apply_language(initial_language)

    def tr_text(self, key, **kwargs):
        return self.translation_service.tr(key, **kwargs)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(self.title_label)

        self.language_combo = QComboBox()
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self.language_combo)

        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.message_label.setStyleSheet("""
            font-size: 14px;
            padding: 12px 4px 4px 4px;
        """)
        layout.addWidget(self.message_label, 1)

        self.dont_show_again_checkbox = QCheckBox()
        layout.addWidget(self.dont_show_again_checkbox)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)

        self.continue_button = QPushButton()
        self.continue_button.clicked.connect(self._save_and_accept)
        buttons_row.addWidget(self.continue_button)

        layout.addLayout(buttons_row)

    def _load_languages(self):
        self.language_combo.blockSignals(True)
        self.language_combo.clear()

        available_languages = self.translation_service.get_available_languages()

        seen = set()
        for item in available_languages:
            if not isinstance(item, dict):
                continue

            code = item.get("code")
            name = item.get("name", code)

            if not code or code in seen:
                continue

            seen.add(code)
            self.language_combo.addItem(name, code)

        self.language_combo.blockSignals(False)

    def _apply_language(self, language_code):
        self.current_language = language_code
        self.translation_service.set_language(language_code)

        self.setWindowTitle(self.tr_text("STARTUP_DIALOG_TITLE"))
        self.title_label.setText(self.tr_text("STARTUP_WELCOME_TITLE"))
        self.message_label.setText(self.tr_text("STARTUP_COMMUNITY_MESSAGE_BODY"))
        self.dont_show_again_checkbox.setText(self.tr_text("STARTUP_DONT_SHOW_AGAIN"))
        self.continue_button.setText(self.tr_text("STARTUP_CONTINUE_BUTTON"))

        index = self.language_combo.findData(language_code)
        if index >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)

    def _on_language_changed(self, _index):
        language_code = self.language_combo.currentData()
        if language_code:
            self._apply_language(language_code)

    def _save_and_accept(self):
        self._dont_show_again = self.dont_show_again_checkbox.isChecked()
        self.settings_service.save_language_preference(self.current_language)
        self.settings_service.set("startup_show_community_message", not self._dont_show_again)
        self.accept()

    def selected_language(self):
        return self.current_language