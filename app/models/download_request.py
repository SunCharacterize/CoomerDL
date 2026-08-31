from dataclasses import dataclass


@dataclass
class DownloadRequest:
    url: str
    download_folder: str
    download_images: bool = True
    download_videos: bool = True
    only_this_url: bool = False
