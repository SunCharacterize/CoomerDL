import hashlib
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class BunkrAdapter:
    site_name = "bunkr"

    def __init__(self, session, headers=None, log_callback=None, tr=None):
        self.session = session
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "Referer": "https://bunkr.site/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.log_callback = log_callback
        self.tr = tr

    def translate(self, key, **kwargs):
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

    def log(self, message):
        if self.log_callback:
            self.log_callback(self.site_name, message)

    def clean_filename(self, filename):
        return re.sub(r'[<>:"/\\|?*\u200b]', "_", str(filename or "")).strip()

    def get_consistent_folder_name(self, url, default_name):
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
        folder_name = f"{default_name}_{url_hash}"
        return self.clean_filename(folder_name)

    def resolve_url(self, url: str):
        if "/f/" in url:
            return self._resolve_f_url(url)

        return self._resolve_post_or_profile(url)

    def _request_soup(self, url):
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def _resolve_f_url(self, url):
        self.log(self.translate("BUNKR_RESOLVING_F_URL", url=url))
        soup = self._request_soup(url)

        first_anchor = soup.find(
            "a",
            {
                "class": "btn btn-main btn-lg rounded-full px-6 font-semibold flex-1 ic-download-01 ic-before before:text-lg"
            },
        )
        if not first_anchor or "href" not in first_anchor.attrs:
            self.log(self.translate("BUNKR_INTERMEDIATE_LINK_NOT_FOUND"))
            return {
                "folder_name": self.get_consistent_folder_name(url, "bunkr_post"),
                "media": [],
            }

        intermediate_url = urljoin(url, first_anchor["href"])
        soup2 = self._request_soup(intermediate_url)

        p_tag = soup2.find("p", class_="mt-3 text-center")
        if not p_tag:
            self.log(self.translate("BUNKR_FINAL_CONTAINER_NOT_FOUND"))
            return {
                "folder_name": self.get_consistent_folder_name(url, "bunkr_post"),
                "media": [],
            }

        download_anchor = p_tag.find(
            "a",
            {
                "class": "btn btn-main btn-lg rounded-full px-6 font-semibold ic-download-01 ic-before before:text-lg"
            },
        )
        if not download_anchor or "href" not in download_anchor.attrs:
            self.log(self.translate("BUNKR_FINAL_DOWNLOAD_LINK_NOT_FOUND"))
            return {
                "folder_name": self.get_consistent_folder_name(url, "bunkr_post"),
                "media": [],
            }

        final_download_url = urljoin(intermediate_url, download_anchor["href"])
        folder_name = self.get_consistent_folder_name(url, "bunkr_post")

        return {
            "folder_name": folder_name,
            "media": [
                {
                    "media_url": final_download_url,
                    "title": "bunkr_post",
                    "post_id": None,
                    "published": "",
                }
            ],
        }

    def _resolve_post_or_profile(self, url):
        soup = self._request_soup(url)

        title_tag = soup.find("h1", {"class": "truncate"})
        if title_tag:
            base_folder_name = self.clean_filename(title_tag.text.strip())[:50]
        else:
            base_folder_name = "bunkr_profile"

        folder_name = self.get_consistent_folder_name(url, base_folder_name)

        media = []

        grid_div = soup.find(
            "div",
            {"class": "grid gap-4 grid-cols-repeat [--size:11rem] lg:[--size:14rem] grid-images"},
        )
        if grid_div:
            media.extend(self._resolve_profile_media(url, grid_div))
        else:
            media.extend(self._resolve_post_media(url, soup))

        return {
            "folder_name": folder_name,
            "media": media,
        }

    def _resolve_profile_media(self, profile_url, grid_div):
        media = []
        links = grid_div.find_all("a", {"class": "after:absolute after:z-10 after:inset-0"})

        for link in links:
            href = link.get("href")
            if not href:
                continue

            image_page_url = urljoin(profile_url, href)

            try:
                image_soup = self._request_soup(image_page_url)

                media_tag = image_soup.select_one(
                    "figure.relative img[class='w-full h-full absolute opacity-20 object-cover blur-sm z-10']"
                )
                if media_tag and media_tag.get("src"):
                    media_url = urljoin(image_page_url, media_tag["src"])
                    media.append({
                        "media_url": media_url,
                        "title": "bunkr_profile_item",
                        "post_id": None,
                        "published": "",
                    })

                video_tag = image_soup.select_one("video#player")
                if video_tag:
                    if video_tag.get("src"):
                        media_url = urljoin(image_page_url, video_tag["src"])
                        media.append({
                            "media_url": media_url,
                            "title": "bunkr_profile_item",
                            "post_id": None,
                            "published": "",
                        })
                    else:
                        source_tag = video_tag.find("source")
                        if source_tag and source_tag.get("src"):
                            media_url = urljoin(image_page_url, source_tag["src"])
                            media.append({
                                "media_url": media_url,
                                "title": "bunkr_profile_item",
                                "post_id": None,
                                "published": "",
                            })

            except Exception as e:
                self.log(
                    self.translate(
                        "BUNKR_FAILED_RESOLVING_PROFILE_MEDIA_PAGE",
                        url=image_page_url,
                        error=e,
                    )
                )

        return media

    def _resolve_post_media(self, post_url, soup):
        media = []

        media_divs = soup.find_all(
            "figure",
            {"class": "relative rounded-lg overflow-hidden flex justify-center items-center aspect-video bg-soft"},
        )
        for div in media_divs:
            for img_tag in div.find_all("img"):
                src = img_tag.get("src")
                if src:
                    media.append({
                        "media_url": urljoin(post_url, src),
                        "title": "bunkr_post",
                        "post_id": None,
                        "published": "",
                    })

        video_divs = soup.find_all("div", {"class": "flex w-full md:w-auto gap-4"})
        for video_div in video_divs:
            download_page_link = video_div.find(
                "a",
                {
                    "class": "btn btn-main btn-lg rounded-full px-6 font-semibold flex-1 ic-download-01 ic-before before:text-lg"
                },
            )
            if not download_page_link or "href" not in download_page_link.attrs:
                continue

            video_page_url = urljoin(post_url, download_page_link["href"])

            try:
                video_page_soup = self._request_soup(video_page_url)
                download_link = video_page_soup.find(
                    "a",
                    {
                        "class": "btn btn-main btn-lg rounded-full px-6 font-semibold ic-download-01 ic-before before:text-lg"
                    },
                )
                if download_link and download_link.get("href"):
                    media.append({
                        "media_url": urljoin(video_page_url, download_link["href"]),
                        "title": "bunkr_post",
                        "post_id": None,
                        "published": "",
                    })
            except Exception as e:
                self.log(
                    self.translate(
                        "BUNKR_FAILED_RESOLVING_VIDEO_PAGE",
                        url=video_page_url,
                        error=e,
                    )
                )

        return media