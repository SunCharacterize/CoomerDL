from abc import ABC, abstractmethod


class FrontendBridge(ABC):
    @abstractmethod
    def log(self, domain: str, message: str):
        pass

    @abstractmethod
    def enable_widgets(self):
        pass

    @abstractmethod
    def update_progress(self, downloaded, total, file_id=None, file_path=None, speed=None, eta=None, status=None):
        pass

    @abstractmethod
    def update_global_progress(self, completed_files, total_files):
        pass

    @abstractmethod
    def get_download_folder(self) -> str:
        pass

    @abstractmethod
    def get_max_downloads(self) -> int:
        pass

    @abstractmethod
    def get_download_images(self) -> bool:
        pass

    @abstractmethod
    def get_download_videos(self) -> bool:
        pass

    @abstractmethod
    def get_download_compressed(self) -> bool:
        pass

    @abstractmethod
    def get_tr(self):
        pass