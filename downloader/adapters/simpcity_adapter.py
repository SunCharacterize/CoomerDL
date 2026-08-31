import json
import os
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


class SimpCityAdapter:
    site_name = "simpcity"

    def __init__(self, cookies_path="resources/config/cookies/simpcity.json", log_callback=None, tr=None):
        self.cookies_path = cookies_path
        self.log_callback = log_callback
        self.tr = tr if tr else (lambda x, **kwargs: x.format(**kwargs) if kwargs else x)

        try:
            import cloudscraper
        except ImportError as e:
            raise ImportError(
                "SimpCity requires the 'cloudscraper' package. "
                "Install it with: pip install cloudscraper"
            ) from e

        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )

        self.title_selector = "h1[class=p-title-value]"
        self.posts_selector = "div[class*=message-main]"
        self.post_content_selector = "div[class*=message-userContent]"
        self.images_selector = "img[class*=bbImage]"
        self.videos_selector = "video source"
        self.attachments_block_selector = "section[class=message-attachments]"
        self.attachments_selector = "a"
        self.next_page_selector = "a[class*=pageNav-jump--next]"

        self.set_cookies()

    def log(self, message, **kwargs):
        if kwargs:
            message = self.tr(message, **kwargs)
        else:
            message = self.tr(message)

        if self.log_callback:
            self.log_callback(self.site_name, message)

    def sanitize_folder_name(self, name):
        return re.sub(r'[<>:"/\\|?*]', "_", name)

    def set_cookies(self):
        if not os.path.exists(self.cookies_path):
            return

        with open(self.cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        if isinstance(cookies, dict):
            if "name" in cookies and "value" in cookies:
                # single browser-export cookie object
                cookies = [cookies]
            else:
                # plain name -> value mapping, the format the settings
                # dialog placeholder suggests
                for name, value in cookies.items():
                    self.scraper.cookies.set(name, str(value))
                return

        for c in cookies:
            if isinstance(c, dict) and "name" in c and "value" in c:
                self.scraper.cookies.set(c["name"], c["value"])

    def fetch_page(self, url):
        response = self.scraper.get(url, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")

    def resolve_thread(self, url, paginate=True, download_images=True, download_videos=True, download_attachments=True):
        self.log("SIMPCITY_PROCESSING_THREAD", url=url)

        all_media = []
        visited = set()
        current_url = url
        folder_name = None

        while current_url and current_url not in visited:
            visited.add(current_url)

            soup = self.fetch_page(current_url)

            if folder_name is None:
                title_element = soup.select_one(self.title_selector)
                folder_name = (
                    self.sanitize_folder_name(title_element.text.strip())
                    if title_element
                    else self.tr("SIMPCITY_DEFAULT_FOLDER")
                )

            page_media = self._extract_page_media(
                soup,
                base_url=current_url,
                folder_name=folder_name,
                download_images=download_images,
                download_videos=download_videos,
                download_attachments=download_attachments,
            )
            all_media.extend(page_media)

            if not paginate:
                break

            next_page = soup.select_one(self.next_page_selector)
            if next_page and next_page.get("href"):
                current_url = urljoin(current_url, next_page.get("href"))
            else:
                current_url = None

        return {
            "folder_name": folder_name or self.tr("SIMPCITY_DEFAULT_FOLDER"),
            "media": all_media,
        }

    def _extract_page_media(self, soup, base_url, folder_name, download_images=True, download_videos=True, download_attachments=True):
        media = []
        seen = set()

        message_inners = soup.select(self.posts_selector)
        for post in message_inners:
            post_content = post.select_one(self.post_content_selector)
            if not post_content:
                continue

            if download_images:
                for img in post_content.select(self.images_selector):
                    src = img.get("src")
                    if not src:
                        continue
                    src = urljoin(base_url, src)
                    if src in seen:
                        continue
                    seen.add(src)

                    media.append({
                        "media_url": src,
                        "post_id": None,
                        "title": folder_name,
                        "published": "",
                        "folder_name": folder_name,
                        "filename": os.path.basename(urlparse(src).path) or "image",
                    })

            if download_videos:
                for video in post_content.select(self.videos_selector):
                    src = video.get("src")
                    if not src:
                        continue
                    src = urljoin(base_url, src)
                    if src in seen:
                        continue
                    seen.add(src)

                    media.append({
                        "media_url": src,
                        "post_id": None,
                        "title": folder_name,
                        "published": "",
                        "folder_name": folder_name,
                        "filename": os.path.basename(urlparse(src).path) or "video",
                    })

            if download_attachments:
                attachments_block = post_content.select_one(self.attachments_block_selector)
                if attachments_block:
                    for attachment in attachments_block.select(self.attachments_selector):
                        href = attachment.get("href")
                        if not href:
                            continue
                        href = urljoin(base_url, href)
                        if href in seen:
                            continue
                        seen.add(href)

                        media.append({
                            "media_url": href,
                            "post_id": None,
                            "title": folder_name,
                            "published": "",
                            "folder_name": folder_name,
                            "filename": os.path.basename(urlparse(href).path) or "attachment",
                        })

        return media