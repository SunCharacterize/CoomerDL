import json
import os


class SettingsService:
    def __init__(self, settings_path="resources/config/settings.json"):
        self.settings_path = settings_path

    def ensure_settings_file(self):
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        if not os.path.exists(self.settings_path):
            self.save_settings({})

    def load_settings(self) -> dict:
        self.ensure_settings_file()
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save_settings(self, data: dict):
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        settings = self.load_settings()
        return settings.get(key, default)

    def set(self, key, value):
        settings = self.load_settings()
        settings[key] = value
        self.save_settings(settings)

    def load_download_folder(self, default_folder="downloads"):
        return self.get("download_folder", default_folder)

    def save_download_folder(self, folder):
        self.set("download_folder", folder)

    def load_language_preference(self, default_language="en"):
        return self.get("language", default_language)

    def save_language_preference(self, language):
        self.set("language", language)