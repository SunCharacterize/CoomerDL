import os
from concurrent.futures import as_completed

from downloader.core.base_api_downloader import BaseApiDownloader
from downloader.adapters.erome_adapter import EromeAdapter


class EromeDownloader(BaseApiDownloader):
    def __init__(
        self,
        log_callback=None,
        enable_widgets_callback=None,
        update_progress_callback=None,
        update_global_progress_callback=None,
        download_images=True,
        download_videos=True,
        headers=None,
        language="en",
        is_profile_download=False,
        direct_download=False,
        tr=None,
        max_workers=5,
        download_folder="downloads",
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
            headers=headers,
            download_images=download_images,
            download_videos=download_videos,
            download_compressed=False,
            tr=tr,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        self.language = language
        self.is_profile_download = is_profile_download
        self.direct_download = direct_download

        self.adapter = EromeAdapter(
            session=self.session,
            headers=self.headers,
            log_callback=self._capture_log,
            tr=self.tr,
            should_cancel=self.cancel_requested.is_set,
        )
        self.domain_name = "erome"

    def _capture_log(self, domain_or_message, message=None):
        if message is None:
            final_message = domain_or_message
        else:
            final_message = message

        if self.log_callback:
            self.log_callback(self.domain_name, final_message)

    def request_cancel(self):
        self.cancel_requested.set()
        self.log("EROME_DOWNLOAD_CANCELLED")
        if self.is_profile_download and self.enable_widgets_callback:
            self.enable_widgets_callback()

    def _download_entries(self, media_entries, root_folder):
        self.total_files = len(media_entries)
        self.completed_files = 0
        futures = []

        for entry in media_entries:
            media_url = entry["media_url"]
            folder_name = entry.get("folder_name") or "erome_album"
            target_folder = os.path.join(root_folder, folder_name) if not os.path.isabs(folder_name) else folder_name

            os.makedirs(target_folder, exist_ok=True)

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
                self.log("EROME_CANCELLING_REMAINING_DOWNLOADS")
                break
            future.result()

    def process_album_page(self, page_url, base_folder, download_images=True, download_videos=True):
        try:
            if self.cancel_requested.is_set():
                return

            self.log("EROME_PROCESSING_ALBUM_URL", page_url=page_url)
            resolved = self.adapter._resolve_album(
                page_url,
                download_images=download_images,
                download_videos=download_videos,
                direct_download=self.direct_download,
            )

            self._download_entries(resolved["media"], base_folder)
            self.log("EROME_ALBUM_DOWNLOAD_COMPLETE", folder_name=resolved["folder_name"])

        except Exception as e:
            self.log("EROME_ERROR_ACCESSING_PAGE", page_url=page_url, status_code=str(e))
        finally:
            self.shutdown_executor()

    def process_profile_page(self, url, download_folder, download_images, download_videos):
        try:
            if self.cancel_requested.is_set():
                return

            self.log("EROME_PROCESSING_PROFILE_URL", url=url)
            resolved = self.adapter._resolve_profile(
                url,
                download_images=download_images,
                download_videos=download_videos,
                direct_download=self.direct_download,
            )

            self._download_entries(resolved["media"], download_folder)
            self.log("EROME_PROFILE_DOWNLOAD_COMPLETE", username=resolved["folder_name"])

        except Exception as e:
            self.log("EROME_ERROR_ACCESSING_PAGE", page_url=url, status_code=str(e))
        finally:
            self.shutdown_executor()