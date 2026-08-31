import os
from concurrent.futures import as_completed

from downloader.core.base_api_downloader import BaseApiDownloader
from downloader.adapters.simpcity_adapter import SimpCityAdapter


class SimpCity(BaseApiDownloader):
    def __init__(
        self,
        download_folder,
        max_workers=5,
        log_callback=None,
        enable_widgets_callback=None,
        update_progress_callback=None,
        update_global_progress_callback=None,
        tr=None,
        max_retries=3,
        retry_interval=1.0,
    ):
        super().__init__(
            download_folder=download_folder,
            max_workers=max_workers,
            log_callback=log_callback,
            enable_widgets_callback=enable_widgets_callback,
            update_progress_callback=update_progress_callback,
            update_global_progress_callback=update_global_progress_callback,
            tr=tr,
            download_images=True,
            download_videos=True,
            download_compressed=True,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        self.adapter = SimpCityAdapter(
            log_callback=self.log_callback,
            tr=self.tr,
        )
        self.domain_name = "simpcity"

    def download_images_from_simpcity(self, url, paginate=True):
        try:
            self.log("SIMPCITY_PROCESSING_THREAD", url=url)

            resolved = self.adapter.resolve_thread(url, paginate=paginate)
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
                    post_id=entry.get("post_id"),
                    post_name=entry.get("title"),
                    post_time=entry.get("published"),
                    download_id=media_url,
                    target_folder=target_folder,
                    forced_filename=entry.get("filename"),
                )
                futures.append(future)

            self.futures = futures

            for future in as_completed(futures):
                if self.cancel_requested.is_set():
                    self.log("SIMPCITY_DOWNLOAD_CANCELLED")
                    break
                future.result()

            self.log("SIMPCITY_DOWNLOAD_COMPLETED")
        except Exception as e:
            self.log("SIMPCITY_ERROR_PROCESSING_THREAD", error=e)
        finally:
            self.shutdown_executor()