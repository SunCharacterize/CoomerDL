import json
import os


class SettingsWindowService:
    DEFAULT_SETTINGS = {
        "max_downloads": 3,
        "folder_structure": "default",
        "language": "en",
        "max_retries": 3,
        "retry_interval": 2.0,
        "file_naming_mode": 0,
    }

    def __init__(self, config_path, on_settings_changed=None):
        self.config_path = config_path
        self.on_settings_changed = on_settings_changed

    def load_settings(self):
        if not os.path.exists(self.config_path):
            return dict(self.DEFAULT_SETTINGS)

        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if not isinstance(data, dict):
                    return dict(self.DEFAULT_SETTINGS)

                merged = dict(self.DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except (OSError, ValueError):
            # OSError covers missing/unreadable files; ValueError covers
            # json.JSONDecodeError and UnicodeDecodeError
            return dict(self.DEFAULT_SETTINGS)

    def save_settings(self, settings: dict):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=4, ensure_ascii=False)

        if callable(self.on_settings_changed):
            self.on_settings_changed(settings)

    def get_language_name(self, languages: dict, lang_code: str):
        for name, code in languages.items():
            if code == lang_code:
                return name
        return "English"

    def apply_language_settings(
        self,
        settings: dict,
        selected_language_name: str,
        languages: dict,
        save_language_preference_func,
        load_translations_func,
        update_ui_texts_func,
    ):
        if selected_language_name not in languages:
            return False, "PLEASE_SELECT_LANGUAGE"

        selected_language_code = languages[selected_language_name]
        settings["language"] = selected_language_code
        self.save_settings(settings)
        save_language_preference_func(selected_language_code)
        load_translations_func(selected_language_code)
        update_ui_texts_func()
        return True, "LANGUAGE_APPLIED_SUCCESS"