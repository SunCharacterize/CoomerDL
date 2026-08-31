import os
from concurrent.futures import as_completed

from downloader.core.base_api_downloader import BaseApiDownloader
from downloader.adapters.bunkr_adapter import BunkrAdapter


class BunkrDownloader(BaseApiDownloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adapter = BunkrAdapter(
            session=self.session,
            headers=self.headers,
            log_callback=self.log_callback,
            tr=self._translate_text,
        )
        self.domain_name = "bunkr"

    def descargar_post_bunkr(self, url_post):
        try:
            self.log("BUNKR_STARTING_POST_DOWNLOAD", url=url_post)

            resolved = self.adapter.resolve_url(url_post)
            folder_name = resolved["folder_name"]
            media_entries = resolved["media"]

            target_folder = os.path.join(self.download_folder, folder_name)
            os.makedirs(target_folder, exist_ok=True)

            self.total_files = len(media_entries)
            self.completed_files = 0
            futures = []

            for entry in media_entries:
                media_url = entry["media_url"]
                future = self.executor.submit(
                    self.process_media_element,
                    media_url,
                    user_id=None,
                    post_id=entry["post_id"],
                    post_name=entry["title"],
                    post_time=entry["published"],
                    download_id=media_url,
                    target_folder=target_folder,
                )
                futures.append(future)

            self.futures = futures

            for future in as_completed(futures):
                if self.cancel_requested.is_set():
                    break
                future.result()

        except Exception as e:
            self.log("BUNKR_ERROR_PROCESSING_POST", url=url_post, error=e)
        finally:
            self.shutdown_executor()

    def descargar_perfil_bunkr(self, url_perfil):
        try:
            self.log("BUNKR_STARTING_PROFILE_DOWNLOAD", url=url_perfil)

            resolved = self.adapter.resolve_url(url_perfil)
            folder_name = resolved["folder_name"]
            media_entries = resolved["media"]

            target_folder = os.path.join(self.download_folder, folder_name)
            os.makedirs(target_folder, exist_ok=True)

            self.total_files = len(media_entries)
            self.completed_files = 0
            futures = []

            for entry in media_entries:
                media_url = entry["media_url"]
                future = self.executor.submit(
                    self.process_media_element,
                    media_url,
                    user_id=None,
                    post_id=entry["post_id"],
                    post_name=entry["title"],
                    post_time=entry["published"],
                    download_id=media_url,
                    target_folder=target_folder,
                )
                futures.append(future)

            self.futures = futures

            for future in as_completed(futures):
                if self.cancel_requested.is_set():
                    break
                future.result()

        except Exception as e:
            self.log("BUNKR_ERROR_PROCESSING_PROFILE", url=url_perfil, error=e)
        finally:
            self.shutdown_executor()