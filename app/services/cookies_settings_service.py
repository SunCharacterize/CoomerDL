import json
import os


class CookiesSettingsService:
    def __init__(self, cookies_path):
        self.cookies_path = cookies_path

    def ensure_parent_dir(self):
        os.makedirs(os.path.dirname(self.cookies_path), exist_ok=True)

    def load_cookies_text(self) -> str:
        if not os.path.exists(self.cookies_path):
            return ""

        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return json.dumps(data, indent=4, ensure_ascii=False)
                if isinstance(data, list):
                    return json.dumps(data, indent=4, ensure_ascii=False)
                return ""
        except Exception:
            try:
                with open(self.cookies_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return ""

    def parse_cookies_text(self, cookies_text: str):
        cookies_text = cookies_text.strip()
        if not cookies_text:
            return None

        return json.loads(cookies_text)

    def save_cookies_text(self, cookies_text: str):
        cookies_data = self.parse_cookies_text(cookies_text)
        self.ensure_parent_dir()

        with open(self.cookies_path, "w", encoding="utf-8") as f:
            json.dump(cookies_data, f, indent=4, ensure_ascii=False)

        return cookies_data

    def count_cookies(self) -> int:
        if not os.path.exists(self.cookies_path):
            return 0

        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, (dict, list)):
                return len(data)
        except Exception:
            pass

        return 0

    def clear_cookies(self):
        self.ensure_parent_dir()
        with open(self.cookies_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)

    def import_cookies_file(self, source_path: str) -> str:
        with open(source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # validar antes de devolver
        self.parse_cookies_text(content)
        return content