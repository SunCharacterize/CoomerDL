import json
import os


class TranslationService:
    def __init__(self, language="en", locales_dir="resources/config/i18n"):
        self.locales_dir = locales_dir
        self.language = language
        self.default_language = "en"
        self.translations = {}
        self.default_translations = {}
        self.load_translations(language)

    def _load_json_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def load_translations(self, language=None):
        if language:
            self.language = language

        default_path = os.path.join(self.locales_dir, f"{self.default_language}.json")
        target_path = os.path.join(self.locales_dir, f"{self.language}.json")

        self.default_translations = self._load_json_file(default_path)
        self.translations = self._load_json_file(target_path)

    def set_language(self, language):
        self.load_translations(language)

    def tr(self, key, **kwargs):
        text = self.translations.get(
            key,
            self.default_translations.get(key, key)
        )

        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def get_available_languages(self):
        manifest_path = os.path.join(self.locales_dir, "languages.json")
        manifest = self._load_json_file(manifest_path)

        languages = []

        if isinstance(manifest, dict):
            official = manifest.get("official", [])
            community = manifest.get("community", [])

            if isinstance(official, list):
                languages.extend(official)

            if isinstance(community, list):
                languages.extend(community)

        if not languages:
            languages = [
                {"code": "en", "name": "English"},
                {"code": "es", "name": "Español"},
            ]

        return languages