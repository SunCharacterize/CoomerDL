from dataclasses import dataclass


@dataclass
class AppState:
    download_folder: str = ""
    language: str = "en"
