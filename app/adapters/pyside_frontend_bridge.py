from app.interfaces.frontend_bridge import FrontendBridge
from typing import Optional

class PySideFrontendBridge(FrontendBridge):
    def __init__(self, app):
        self.app = app


    def log(self, domain_or_message: str, message: Optional[str] = None):
        if message is None:
            self.app.add_log_message_safe(domain_or_message)
        else:
            self.app.add_log_message_safe(domain_or_message, message)

    def enable_widgets(self):
        self.app.enable_widgets()

    def update_progress(self, downloaded, total, file_id=None, file_path=None, speed=None, eta=None, status=None):
        self.app.update_progress(downloaded, total, file_id, file_path, speed, eta, status=status)

    def update_global_progress(self, completed_files, total_files):
        self.app.update_global_progress(completed_files, total_files)

    def get_download_folder(self) -> str:
        return self.app.download_folder

    def get_max_downloads(self) -> int:
        return self.app.max_downloads

    def get_download_images(self) -> bool:
        return bool(self.app.download_images_check.get())

    def get_download_videos(self) -> bool:
        return bool(self.app.download_videos_check.get())

    def get_download_compressed(self) -> bool:
        return bool(self.app.download_compressed_check.get())

    def get_tr(self):
        return self.app.tr