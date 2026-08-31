from concurrent.futures import as_completed

from downloader.core.base_api_downloader import BaseApiDownloader
from downloader.adapters.coomerfans_adapter import CoomerfansAdapter


class CoomerfansDownloader(BaseApiDownloader):
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
        tr=None,
        max_workers=5,
        download_folder="downloads",
        folder_structure="default",
        max_retries=3,
        retry_interval=2.0,
        rate_limit_interval=0.0,
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
            folder_structure=folder_structure,
            max_retries=max_retries,
            retry_interval=retry_interval,
            rate_limit_interval=rate_limit_interval,
        )

        self.language = language
        self.is_profile_download = is_profile_download

        self.adapter = CoomerfansAdapter(
            session=self.session,
            headers=self.headers,
            log_callback=self._capture_log,
            tr=self.tr,
            should_cancel=self.cancel_requested.is_set,
        )
        self.domain_name = "coomerfans"

    def _capture_log(self, domain_or_message, message=None):
        if message is None:
            final_message = domain_or_message
        else:
            final_message = message

        if self.log_callback:
            self.log_callback(self.domain_name, final_message)

    def request_cancel(self):
        self.cancel_requested.set()
        self.log("COOMERFANS_DOWNLOAD_CANCELLED")
        if self.is_profile_download and self.enable_widgets_callback:
            self.enable_widgets_callback()

    def _download_entries(self, media_entries, default_user_id=None):
        self.total_files = len(media_entries)
        self.completed_files = 0
        futures = []

        for entry in media_entries:
            media_url = entry["media_url"]
            user_id = entry.get("user_id") or default_user_id or "coomerfans"

            kwargs = dict(
                user_id=user_id,
                post_id=entry.get("post_id"),
                post_name=entry.get("title"),
                post_time=entry.get("published"),
                download_id=media_url,
            )

            future = self.executor.submit(self.process_media_element, media_url, **kwargs)
            futures.append(future)

        self.futures = futures

        for future in as_completed(futures):
            if self.cancel_requested.is_set():
                self.log("COOMERFANS_CANCELLING_REMAINING_DOWNLOADS")
                break
            future.result()

    def process_post_page(self, page_url, base_folder, download_images=True, download_videos=True):
        try:
            if self.cancel_requested.is_set():
                return

            self.log("COOMERFANS_PROCESSING_POST_URL", page_url=page_url)
            resolved = self.adapter._resolve_post(
                page_url,
                download_images=download_images,
                download_videos=download_videos,
            )

            self._download_entries(resolved["media"], default_user_id=resolved.get("folder_name"))
            self.log("COOMERFANS_POST_DOWNLOAD_COMPLETE", folder_name=resolved["folder_name"])

        except Exception as e:
            self.log("COOMERFANS_ERROR_ACCESSING_PAGE", page_url=page_url, status_code=str(e))
        finally:
            self.shutdown_executor()

    def process_profile_page(self, url, download_folder, download_images, download_videos):
        try:
            if self.cancel_requested.is_set():
                return

            self.log("COOMERFANS_PROCESSING_PROFILE_URL", url=url)
            resolved = self.adapter._resolve_profile(
                url,
                download_images=download_images,
                download_videos=download_videos,
            )

            self._download_entries(resolved["media"], default_user_id=resolved.get("folder_name"))
            self.log("COOMERFANS_PROFILE_DOWNLOAD_COMPLETE", username=resolved["folder_name"])

        except Exception as e:
            self.log("COOMERFANS_ERROR_ACCESSING_PAGE", page_url=url, status_code=str(e))
        finally:
            self.shutdown_executor()
