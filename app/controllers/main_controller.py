import threading

from app.models.download_request import DownloadRequest


DEAD_SITES = {
    "coomer.st": "coomerfans.com",
    "kemono.cr": "pawchive.pw",
    "jpg5.su": None,
}


class MainController:
    def __init__(self, app):
        self.app = app

    def build_request_from_ui(self) -> DownloadRequest:
        url = self.app.url_entry.get().strip()
        if url and "://" not in url:
            # Scheme-less URLs would parse with an empty host, bypassing
            # both the dead-site check and the host-based routing.
            url = "https://" + url

        return DownloadRequest(
            url=url,
            download_folder=self.app.download_folder,
            download_images=bool(self.app.download_images_check.get()),
            download_videos=bool(self.app.download_videos_check.get()),
            only_this_url=bool(self.app.only_this_url_check.get()),
        )

    def start_download(self):
        request = self.build_request_from_ui()

        if not request.download_folder:
            self.app.show_error(
                self.app.tr("ERROR"),
                self.app.tr("PLEASE_SELECT_DOWNLOAD_FOLDER")
            )
            return

        if not request.url:
            self.app.show_error(
                self.app.tr("ERROR"),
                self.app.tr("PLEASE_ENTER_VALID_URL")
            )
            return

        self.app.prepare_download_ui()

        parsed = self.app.url_service.parse_download_url(request.url)
        download_thread = None

        host = parsed.host
        dead_site = next(
            (d for d in DEAD_SITES if host == d or host.endswith("." + d)),
            None,
        )

        if dead_site:
            alternative = DEAD_SITES[dead_site]
            if alternative:
                message = self.app.tr(
                    "SITE_NO_LONGER_SUPPORTED_WITH_ALTERNATIVE",
                    site=host,
                    alternative=alternative,
                )
            else:
                message = self.app.tr("SITE_NO_LONGER_SUPPORTED", site=host)

            self.app.add_log_message_safe(message)
            self.app.show_error(self.app.tr("ERROR"), message)
            self.app.enable_widgets()
            return

        if parsed.site_type == "erome":
            self.app.add_log_message_safe(self.app.tr("DOWNLOADING_EROME"))
            self.app.setup_erome_downloader(is_profile_download=parsed.is_profile)
            self.app.active_downloader = self.app.erome_downloader

            if parsed.is_album:
                self.app.add_log_message_safe(self.app.tr("ALBUM_URL"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(
                        self.app.active_downloader,
                        self.app.active_downloader.process_album_page,
                        request.url,
                        request.download_folder,
                        request.download_images,
                        request.download_videos,
                    ),
                    daemon=True
                )
            else:
                self.app.add_log_message_safe("erome", self.app.tr("PROFILE_URL"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(
                        self.app.active_downloader,
                        self.app.active_downloader.process_profile_page,
                        request.url,
                        request.download_folder,
                        request.download_images,
                        request.download_videos,
                    ),
                    daemon=True
                )

        elif parsed.site_type == "bunkr":
            self.app.add_log_message_safe("bunkr", self.app.tr("DOWNLOADING_BUNKR"))
            self.app.setup_bunkr_downloader()
            self.app.active_downloader = self.app.bunkr_downloader

            if parsed.is_post:
                self.app.add_log_message_safe(self.app.tr("POST_URL"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(self.app.bunkr_downloader, self.app.bunkr_downloader.descargar_post_bunkr, request.url),
                    daemon=True
                )
            else:
                self.app.add_log_message_safe("bunkr", self.app.tr("PROFILE_URL"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(self.app.bunkr_downloader, self.app.bunkr_downloader.descargar_perfil_bunkr, request.url),
                    daemon=True
                )

        elif parsed.site_type == "coomer_kemono":
            self.app.add_log_message_safe(self.app.tr("STARTING_DOWNLOAD"))
            self.app.setup_general_downloader()
            self.app.active_downloader = self.app.general_downloader

            site = parsed.host
            service = parsed.service
            user = parsed.user
            post = parsed.post

            if service is None or user is None:
                if service is None:
                    self.app.add_log_message_safe(self.app.tr("FAILED_TO_EXTRACT_SERVICE"))
                    self.app.show_error(
                        self.app.tr("ERROR"),
                        self.app.tr("FAILED_TO_EXTRACT_SERVICE")
                    )
                else:
                    self.app.add_log_message_safe(self.app.tr("FAILED_TO_EXTRACT_USER_ID"))
                    self.app.show_error(
                        self.app.tr("ERROR"),
                        self.app.tr("FAILED_TO_EXTRACT_USER_ID")
                    )

                self.app.add_log_message_safe("SYSTEM", self.app.tr("INVALID_URL"))
                self.app.enable_widgets()
                return

            self.app.add_log_message_safe(
                self.app.tr(
                    "EXTRACTED_SERVICE_SITE",
                    service=service,
                    site=site
                )
            )

            if parsed.is_post:
                self.app.add_log_message_safe(self.app.tr("DOWNLOADING_SINGLE_POST"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(
                        self.app.active_downloader,
                        self.start_ck_post_download,
                        self.app.active_downloader,
                        site,
                        service,
                        user,
                        post,
                    ),
                    daemon=True
                )
            else:
                self.app.add_log_message_safe(self.app.tr("DOWNLOADING_ALL_USER_CONTENT"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(
                        self.app.active_downloader,
                        self.start_ck_profile_download,
                        self.app.active_downloader,
                        site,
                        service,
                        user,
                        parsed.query,
                        True,
                        parsed.offset,
                        request.only_this_url,
                    ),
                    daemon=True
                )

        elif parsed.site_type == "simpcity":
            self.app.add_log_message_safe(self.app.tr("DOWNLOADING_SIMPCITY"))
            self.app.setup_simpcity_downloader()
            self.app.active_downloader = self.app.simpcity_downloader
            download_thread = threading.Thread(
                target=self.wrapped_download,
                args=(
                    self.app.active_downloader,
                    self.app.active_downloader.download_images_from_simpcity,
                    request.url,
                    not request.only_this_url,
                ),
                daemon=True
            )

        elif parsed.site_type == "jpg5":
            self.app.add_log_message_safe(self.app.tr("DOWNLOADING_FROM_JPG5"))
            self.app.setup_jpg5_downloader()
            download_thread = threading.Thread(
                target=self.wrapped_download,
                args=(self.app.active_downloader, self.app.active_downloader.descargar_imagenes),
                daemon=True
            )

        elif parsed.site_type == "coomerfans":
            self.app.add_log_message_safe(self.app.tr("DOWNLOADING_COOMERFANS"))
            self.app.setup_coomerfans_downloader(is_profile_download=parsed.is_profile)
            self.app.active_downloader = self.app.coomerfans_downloader

            if parsed.is_post:
                self.app.add_log_message_safe(self.app.tr("POST_URL"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(
                        self.app.active_downloader,
                        self.app.active_downloader.process_post_page,
                        request.url,
                        request.download_folder,
                        request.download_images,
                        request.download_videos,
                    ),
                    daemon=True
                )
            else:
                self.app.add_log_message_safe(self.app.tr("PROFILE_URL"))
                download_thread = threading.Thread(
                    target=self.wrapped_download,
                    args=(
                        self.app.active_downloader,
                        self.app.active_downloader.process_profile_page,
                        request.url,
                        request.download_folder,
                        request.download_images,
                        request.download_videos,
                    ),
                    daemon=True
                )

        else:
            self.app.add_log_message_safe(self.app.tr("INVALID_URL"))
            self.app.enable_widgets()
            return

        if download_thread:
            download_thread.start()
            self.app.download_thread = download_thread

    def wrapped_download(self, downloader, download_method, *args):
        try:
            download_method(*args)
        except Exception as e:
            self.app.add_log_message_safe(self.app.tr("DOWNLOAD_THREAD_ERROR", error=e))
        finally:
            # Only clear if a newer download has not replaced it already
            if self.app.active_downloader is downloader:
                self.app.active_downloader = None
            self.app.enable_widgets()
            self.app.export_logs(downloader)

    def start_ck_profile_download(self, downloader, site, service, user, query, download_all, initial_offset, only_this_url=False):
        download_info = downloader.download_media(
            site,
            user,
            service,
            query=query,
            download_all=download_all,
            initial_offset=initial_offset,
            only_first_page=only_this_url,
        )
        if download_info:
            self.app.add_log_message_safe(
                self.app.tr("DOWNLOAD_INFO", download_info=download_info)
            )
        return download_info

    def start_ck_post_download(self, downloader, site, service, user, post):
        download_info = downloader.download_single_post(site, post, service, user)
        if download_info:
            self.app.add_log_message_safe(
                self.app.tr("DOWNLOAD_INFO", download_info=download_info)
            )
        return download_info

    def cancel_download(self):
        if self.app.active_downloader:
            try:
                self.app.active_downloader.request_cancel()
            except Exception:
                pass
            self.app.active_downloader = None
            self.app.clear_progress_bars()
        else:
            self.app.add_log_message_safe(self.app.tr("NO_ACTIVE_DOWNLOAD_TO_CANCEL"))

        self.app.enable_widgets()