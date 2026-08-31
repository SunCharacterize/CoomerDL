import os
from concurrent.futures import as_completed

from downloader.core.base_api_downloader import BaseApiDownloader
from downloader.adapters.jpg5_adapter import Jpg5Adapter


class Jpg5Downloader(BaseApiDownloader):
    def __init__(
        self,
        url,
        carpeta_destino,
        log_callback=None,
        tr=None,
        update_progress_callback=None,
        update_global_progress_callback=None,
        max_workers=3,
        max_retries=3,
        retry_interval=1.0,
    ):
        super().__init__(
            download_folder=carpeta_destino,
            max_workers=max_workers,
            log_callback=log_callback,
            update_progress_callback=update_progress_callback,
            update_global_progress_callback=update_global_progress_callback,
            download_images=True,
            download_videos=False,
            download_compressed=False,
            tr=tr,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )
        self.url = url
        self.adapter = Jpg5Adapter(
            session=self.session,
            headers=self.headers,
            log_callback=self.log_callback,
            tr=self.tr,
        )
        self.domain_name = "jpg5"

    def descargar_imagenes(self):
        try:
            os.makedirs(self.download_folder, exist_ok=True)

            resolved = self.adapter.resolve_gallery(self.url)
            media_entries = resolved["media"]

            self.total_files = len(media_entries)
            self.completed_files = 0
            futures = []

            for entry in media_entries:
                media_url = entry["media_url"]

                if self.cancel_requested.is_set():
                    self.log("JPG5_DOWNLOAD_CANCELLED_BY_USER")
                    return

                future = self.executor.submit(
                    self.process_media_element,
                    media_url,
                    user_id=None,
                    post_id=entry.get("post_id"),
                    post_name=entry.get("title"),
                    post_time=entry.get("published"),
                    download_id=media_url,
                    target_folder=self.download_folder,
                    forced_filename=entry.get("filename"),
                )
                futures.append(future)

            self.futures = futures

            for future in as_completed(futures):
                if self.cancel_requested.is_set():
                    self.log("JPG5_DOWNLOAD_CANCELLED_BY_USER")
                    break
                future.result()

        except Exception as e:
            self.log("JPG5_ERROR_PROCESSING_GALLERY", url=self.url, error=e)
        finally:
            self.shutdown_executor()