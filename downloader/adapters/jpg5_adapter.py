import os
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


class Jpg5Adapter:
    site_name = "jpg5"

    def __init__(self, session, headers=None, log_callback=None, tr=None):
        self.session = session
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0",
        }
        self.log_callback = log_callback
        self.tr = tr if tr else (lambda x, **kwargs: x.format(**kwargs) if kwargs else x)

    def log(self, message, **kwargs):
        if kwargs:
            message = self.tr(message, **kwargs)
        else:
            message = self.tr(message)

        if self.log_callback:
            self.log_callback(self.site_name, message)

    def _request_soup(self, url):
        response = self.session.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")

    def resolve_gallery(self, url):
        self.log("JPG5_PROCESSING_GALLERY", url=url)
        soup = self._request_soup(url)

        divs = soup.find_all("div", class_="list-item c8 gutter-margin-right-bottom")
        media = []

        for div in divs:
            enlaces = div.find_all("a", class_="image-container --media")
            for enlace in enlaces:
                href = enlace.get("href")
                if not href:
                    continue

                media_page_url = urljoin(url, href)

                try:
                    file_entry = self._resolve_media_page(media_page_url)
                    if file_entry:
                        media.append(file_entry)
                except Exception as e:
                    self.log("JPG5_ERROR_PROCESSING_MEDIA_PAGE", url=media_page_url, error=e)

        folder_name = self._build_folder_name(url)
        return {
            "folder_name": folder_name,
            "media": media,
        }

    def _resolve_media_page(self, media_page_url):
        self.log("JPG5_RESOLVING_MEDIA_PAGE", url=media_page_url)
        media_soup = self._request_soup(media_page_url)

        header_content = media_soup.find("div", class_="header-content-right")
        if not header_content:
            self.log("JPG5_HEADER_NOT_FOUND", url=media_page_url)
            return None

        btn_descarga = header_content.find("a", class_="btn btn-download default")
        if not btn_descarga or "href" not in btn_descarga.attrs:
            self.log("JPG5_FINAL_DOWNLOAD_LINK_NOT_FOUND", url=media_page_url)
            return None

        descarga_url = urljoin(media_page_url, btn_descarga["href"])
        filename = os.path.basename(urlparse(descarga_url).path) or "jpg5_file"

        return {
            "media_url": descarga_url,
            "post_id": None,
            "title": "jpg5_gallery",
            "published": "",
            "folder_name": self._build_folder_name(media_page_url),
            "filename": filename,
        }

    def _build_folder_name(self, url):
        path = urlparse(url).path.strip("/").replace("/", "_")
        return path or "jpg5_gallery"