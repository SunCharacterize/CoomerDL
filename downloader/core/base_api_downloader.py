from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore
from urllib.parse import urlparse
import os
import re
import requests
import threading
import time
import zlib
import sqlite3


class BaseApiDownloader:
    def __init__(
        self,
        download_folder,
        max_workers=5,
        log_callback=None,
        enable_widgets_callback=None,
        update_progress_callback=None,
        update_global_progress_callback=None,
        headers=None,
        max_retries=3,
        retry_interval=1.0,
        download_images=True,
        download_videos=True,
        download_compressed=True,
        tr=None,
        folder_structure="default",
        rate_limit_interval=1.0,
    ):
        self.download_folder = download_folder
        self.log_callback = log_callback
        self.enable_widgets_callback = enable_widgets_callback
        self.update_progress_callback = update_progress_callback
        self.update_global_progress_callback = update_global_progress_callback
        self.cancel_requested = threading.Event()
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Referer": "https://coomer.st/",
            "Accept": "text/css",
        }
        self.session = requests.Session()
        self.max_workers = max_workers
        self.per_domain_limit = 2
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.domain_locks = defaultdict(lambda: Semaphore(self.per_domain_limit))
        self.domain_last_request = defaultdict(float)
        self.rate_limit_interval = rate_limit_interval

        self.video_extensions = (".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".wmv", ".m4v")
        self.image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff")
        self.document_extensions = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx")
        self.compressed_extensions = (".zip", ".rar", ".7z", ".tar", ".gz")

        self.download_images = download_images
        self.download_videos = download_videos
        self.download_compressed = download_compressed

        self.futures = []
        self.total_files = 0
        self.completed_files = 0
        self.skipped_files = []
        self.failed_files = []
        self.tr = tr
        self.shutdown_called = False
        self.folder_structure = folder_structure
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.file_lock = threading.Lock()
        self.counter_lock = threading.Lock()
        self.post_attachment_counter = defaultdict(int)
        self.subdomain_cache = {}
        self.subdomain_locks = defaultdict(threading.Lock)
        self.request_timeout = (10, 120)

        db_folder = os.path.join("resources", "config")
        os.makedirs(db_folder, exist_ok=True)
        self.db_path = os.path.join(db_folder, "downloads.db")
        self.db_lock = threading.Lock()
        self.init_db()
        self.load_download_cache()
        self.domain_name = "system"

    def _translate_text(self, key, **kwargs):
        if callable(self.tr):
            try:
                return self.tr(key, **kwargs)
            except TypeError:
                text = self.tr(key)
                if kwargs:
                    try:
                        return text.format(**kwargs)
                    except Exception:
                        return text
                return text

        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def init_db(self):
        self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db_cursor = self.db_connection.cursor()
        self.db_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_url TEXT UNIQUE,
                file_path TEXT,
                file_size INTEGER,
                user_id TEXT,
                post_id TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.db_connection.commit()

    def load_download_cache(self):
        with self.db_lock:
            self.db_cursor.execute("SELECT media_url, file_path, file_size FROM downloads")
            rows = self.db_cursor.fetchall()
        self.download_cache = {row[0]: (row[1], row[2]) for row in rows}

    def log(self, message, **kwargs):
        final_message = self._translate_text(message, **kwargs)
        domain = getattr(self, "domain_name", "system")
        if self.log_callback:
            self.log_callback(domain, final_message)

    def sanitize_filename(self, filename):
        return re.sub(r'[<>:"/\\\\|?*]', "_", filename)

    def request_cancel(self):
        self.cancel_requested.set()
        self.log("DOWNLOAD_CANCELLATION_REQUESTED")
        for future in self.futures:
            future.cancel()

    def shutdown_executor(self):
        if not self.shutdown_called:
            self.shutdown_called = True
            if self.executor:
                self.executor.shutdown(wait=True)
            if self.enable_widgets_callback:
                self.enable_widgets_callback()
            self.log("ALL_DOWNLOADS_COMPLETED_OR_CANCELLED")
            with self.db_lock:
                try:
                    self.db_connection.close()
                except Exception:
                    pass

    def get_filename(self, media_url, post_id=None, post_name=None, attachment_index=1, post_time=None):
        base_name = os.path.basename(media_url).split("?")[0]
        name_no_ext, extension = os.path.splitext(base_name)

        if not hasattr(self, "file_naming_mode"):
            self.file_naming_mode = 0

        mode = self.file_naming_mode

        def sanitize(name):
            return self.sanitize_filename(name).strip()

        if mode == 0:
            sanitized = sanitize(name_no_ext) or "file"
            return f"{sanitized}_{attachment_index}{extension}"
        elif mode == 1:
            sanitized_post = sanitize(post_name or "") or (f"post_{post_id}" if post_id else "post")
            short_hash = f"{zlib.crc32(media_url.encode('utf-8')) & 0xFFFF:04x}"
            return f"{sanitized_post}_{attachment_index}_{short_hash}{extension}"
        elif mode == 2:
            sanitized_post = sanitize(post_name or "") or (f"post_{post_id}" if post_id else "post")
            return f"{sanitized_post} - {post_id}_{attachment_index}{extension}" if post_id else f"{sanitized_post}_{attachment_index}{extension}"
        elif mode == 3:
            sanitized_post = sanitize(post_name or "") or (f"post_{post_id}" if post_id else "post")
            sanitized_time = sanitize(post_time or "")
            short_hash = f"{zlib.crc32(media_url.encode('utf-8')) & 0xFFFF:04x}"
            return f"{sanitized_time} - {sanitized_post}_{attachment_index}_{short_hash}{extension}"

        return sanitize(name_no_ext) + extension

    def get_media_folder(self, extension, user_id, post_id=None):
        if extension in self.video_extensions:
            folder_name = "videos"
        elif extension in self.image_extensions:
            folder_name = "images"
        elif extension in self.document_extensions:
            folder_name = "documents"
        elif extension in self.compressed_extensions:
            folder_name = "compressed"
        else:
            folder_name = "other"

        if self.folder_structure == "post_number" and post_id:
            return os.path.join(self.download_folder, user_id, f"post_{post_id}", folder_name)

        return os.path.join(self.download_folder, user_id, folder_name)

    def safe_request(self, url, max_retries=None, headers=None):
        if max_retries is None:
            max_retries = self.max_retries
        if headers is None:
            headers = self.headers

        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path

        for attempt in range(max_retries + 1):
            if self.cancel_requested.is_set():
                return None

            with self.domain_locks[domain]:
                elapsed_time = time.time() - self.domain_last_request[domain]
                if elapsed_time < self.rate_limit_interval:
                    time.sleep(self.rate_limit_interval - elapsed_time)

                try:
                    self.domain_last_request[domain] = time.time()
                    response = self.session.get(url, stream=True, headers=headers, timeout=self.request_timeout)
                    sc = response.status_code

                    if sc in (403, 404) and ("coomer" in domain or "kemono" in domain):
                        if self.update_progress_callback:
                            self.update_progress_callback(0, 0, status=f"{sc} - probing subdomains")

                        with self.subdomain_locks[path]:
                            if path in self.subdomain_cache:
                                alt_url = self.subdomain_cache[path]
                            else:
                                alt_url = self._find_valid_subdomain(url)
                                self.subdomain_cache[path] = alt_url

                        if alt_url != url:
                            found = urlparse(alt_url).netloc
                            if self.update_progress_callback:
                                self.update_progress_callback(0, 0, status=f"Subdomain found: {found}")

                            response = self.session.get(alt_url, stream=True, headers=headers, timeout=self.request_timeout)
                            response.raise_for_status()
                            return response

                        if self.update_progress_callback:
                            self.update_progress_callback(0, 0, status="Exhausted subdomains")
                        return None

                    response.raise_for_status()
                    return response

                except requests.exceptions.RequestException as e:
                    status_code = getattr(e.response, "status_code", None)

                    if status_code in (429, 500, 502, 503, 504):
                        self.log(
                            "HTTP_RETRY_REQUEST",
                            attempt=attempt + 1,
                            total=max_retries + 1,
                            status_code=status_code,
                            url=url,
                        )
                        time.sleep(self.retry_interval)

                    elif isinstance(e, requests.exceptions.ReadTimeout):
                        self.log(
                            "READ_TIMEOUT_RETRY",
                            attempt=attempt + 1,
                            total=max_retries + 1,
                            timeout=self.request_timeout[1],
                        )
                        time.sleep(self.retry_interval)

                    elif status_code not in (403, 404):
                        url_display = getattr(e.request, "url", url)
                        if len(url_display) > 60:
                            url_display = url_display[:60] + "..."
                        self.log(
                            "ERROR_ACCESSING_URL",
                            attempt=attempt + 1,
                            total=max_retries + 1,
                            url=url_display,
                            error=e,
                        )
                        if attempt < max_retries:
                            time.sleep(self.retry_interval)

                    if status_code in (403, 404) and ("coomer" in domain or "kemono" in domain) and attempt == max_retries:
                        self.log(
                            "FINAL_FAILURE_ACCESSING_URL",
                            url=url,
                            status_code=status_code,
                        )

        return None

    def _find_valid_subdomain(self, url, max_subdomains=10):
        parsed = urlparse(url)
        original_path = parsed.path

        path = original_path
        if not original_path.startswith("/data/"):
            path = ("/data" + original_path) if not original_path.startswith("/data") else original_path

        host = parsed.netloc

        if "coomer" in host:
            base_domains = ["coomer.st"]
        elif "kemono" in host:
            base_domains = ["kemono.cr", "kemono.su"]
        else:
            base_domains = [host]

        for base in base_domains:
            for i in range(1, max_subdomains + 1):
                domain = f"n{i}.{base}"
                test_url = parsed._replace(netloc=domain, path=path).geturl()

                if self.update_progress_callback:
                    self.update_progress_callback(0, 0, status=f"Testing subdomain: {domain}")

                try:
                    resp = self.session.get(test_url, headers=self.headers, timeout=self.request_timeout, stream=True)
                    if resp.status_code == 200:
                        return test_url
                except Exception:
                    pass

        return url

    def process_media_element(
        self,
        media_url,
        user_id=None,
        post_id=None,
        post_name=None,
        post_time=None,
        download_id=None,
        target_folder=None,
        forced_filename=None,
    ):
        if self.cancel_requested.is_set():
            return

        extension = os.path.splitext(media_url.split("?")[0])[1].lower()

        if (extension in self.image_extensions and not self.download_images) or \
        (extension in self.video_extensions and not self.download_videos) or \
        (extension in self.compressed_extensions and not self.download_compressed):
            self.log("SKIPPING_MEDIA_DUE_TO_SETTINGS", media_url=media_url)
            return

        if post_id:
            with self.counter_lock:
                self.post_attachment_counter[post_id] += 1
                attachment_index = self.post_attachment_counter[post_id]
        else:
            attachment_index = 1

        filename = forced_filename or self.get_filename(
            media_url,
            post_id=post_id,
            post_name=post_name,
            post_time=post_time,
            attachment_index=attachment_index,
        )

        if target_folder:
            media_folder = target_folder
        else:
            effective_user_id = user_id or "generic"
            media_folder = self.get_media_folder(extension, effective_user_id, post_id)

        os.makedirs(media_folder, exist_ok=True)

        final_path = os.path.normpath(os.path.join(media_folder, filename))
        tmp_path = final_path + ".tmp"

        if media_url in self.download_cache:
            self.log("FILE_ALREADY_IN_DB_SKIPPING", media_url=media_url)
            with self.file_lock:
                self.skipped_files.append(final_path)
            return

        self.log("STARTING_DOWNLOAD_FROM", media_url=media_url)

        response = self.safe_request(media_url, max_retries=self.max_retries)

        if response is None:
            self.log(
                "FAILED_TO_DOWNLOAD_AFTER_ATTEMPTS",
                media_url=media_url,
                total=self.max_retries + 1,
            )
            with self.file_lock:
                self.failed_files.append(media_url)
            return

        try:
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            start_time = time.time()

            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1048576):
                    if self.cancel_requested.is_set():
                        raise Exception("CANCELLATION_REQUESTED")
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if self.update_progress_callback:
                            elapsed_time = time.time() - start_time
                            speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                            remaining_time = (total_size - downloaded_size) / speed if speed > 0 and total_size > 0 else 0
                            self.update_progress_callback(
                                downloaded_size,
                                total_size,
                                file_id=download_id,
                                file_path=tmp_path,
                                speed=speed,
                                eta=remaining_time,
                            )

            zero_progress_rounds = 0
            while total_size and downloaded_size < total_size:
                resume_headers = self.headers.copy()
                resume_headers["Range"] = f"bytes={downloaded_size}-"
                self.log(
                    "RESUMING_DOWNLOAD_AT_BYTE",
                    downloaded_size=downloaded_size,
                    media_url=media_url,
                )

                part_response = self.safe_request(media_url, max_retries=self.max_retries, headers=resume_headers)
                if part_response is None:
                    raise Exception("RESUMPTION_FAILED_AFTER_RETRIES")

                if part_response.status_code == 200:
                    # Server ignored the Range header and sent the full file again
                    downloaded_size = 0
                    open_mode = "wb"
                else:
                    open_mode = "ab"

                bytes_before_round = downloaded_size

                with open(tmp_path, open_mode) as f:
                    for chunk in part_response.iter_content(chunk_size=1048576):
                        if self.cancel_requested.is_set():
                            raise Exception("CANCELLATION_REQUESTED")
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if self.update_progress_callback:
                                elapsed_time = time.time() - start_time
                                speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                                remaining_time = (total_size - downloaded_size) / speed if speed > 0 and total_size > 0 else 0
                                self.update_progress_callback(
                                    downloaded_size,
                                    total_size,
                                    file_id=download_id,
                                    file_path=tmp_path,
                                    speed=speed,
                                    eta=remaining_time,
                                )

                if downloaded_size == bytes_before_round:
                    zero_progress_rounds += 1
                    if zero_progress_rounds >= 3:
                        raise Exception("RESUME_NO_PROGRESS")
                else:
                    zero_progress_rounds = 0

            if total_size > 0 and downloaded_size != total_size:
                raise Exception(
                    self._translate_text(
                        "FINAL_SIZE_MISMATCH",
                        expected=total_size,
                        actual=downloaded_size,
                    )
                )

            with self.file_lock:
                if os.path.exists(final_path):
                    os.remove(final_path)
                os.rename(tmp_path, final_path)
                self.completed_files += 1

            self.log("DOWNLOAD_SUCCESS_FROM", media_url=media_url)

            if self.update_global_progress_callback:
                self.update_global_progress_callback(self.completed_files, self.total_files)

            with self.db_lock:
                self.db_cursor.execute(
                    """
                    INSERT OR REPLACE INTO downloads (media_url, file_path, file_size, user_id, post_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (media_url, final_path, total_size, user_id, post_id),
                )
                self.db_connection.commit()

            self.download_cache[media_url] = (final_path, total_size)

        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

            if str(e) == "CANCELLATION_REQUESTED" or str(e) == self._translate_text("CANCELLATION_REQUESTED"):
                self.log("DOWNLOAD_CANCELLED_FROM", media_url=media_url)
                return

            self.log(
                "FAILED_TO_DOWNLOAD_AFTER_ATTEMPTS",
                media_url=media_url,
                total=self.max_retries + 1,
            )
            with self.file_lock:
                self.failed_files.append(media_url)

    def update_max_downloads(self, new_max):
        try:
            new_max = int(new_max)
        except (TypeError, ValueError):
            return

        if new_max < 1:
            new_max = 1

        self.max_workers = new_max

        # wait=False: this runs on the UI thread when settings are applied
        # mid-download; waiting would freeze the interface until every
        # queued file finishes. In-flight tasks drain on the old executor.
        if self.executor:
            self.executor.shutdown(wait=False)

        self.executor = ThreadPoolExecutor(max_workers=new_max)
        self.domain_locks = defaultdict(lambda: Semaphore(self.per_domain_limit))

        self.log(
            "UPDATED_MAX_WORKERS",
            new_max=new_max,
            per_domain_limit=self.per_domain_limit,
        )