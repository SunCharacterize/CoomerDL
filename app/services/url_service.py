import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import ParseResult, parse_qs, urlparse


@dataclass
class ParsedDownloadUrl:
    parsed_url: ParseResult
    site_type: str
    host: str = ""
    is_profile: bool = False
    is_album: bool = False
    is_post: bool = False
    service: Optional[str] = None
    user: Optional[str] = None
    post: Optional[str] = None
    query: str = "0"
    offset: int = 0


class UrlService:
    def extract_ck_parameters(self, url: ParseResult) -> tuple[Optional[str], Optional[str], Optional[str]]:
        match = re.search(
            r"/(?P<service>[^/?]+)(/user/(?P<user>[^/?]+)(/post/(?P<post>[^/?]+))?)?",
            url.path
        )
        if match:
            service, user, post = match.group("service", "user", "post")
            return service, user, post
        return None, None, None

    def extract_ck_query(self, url: ParseResult) -> tuple[str, int]:
        query = parse_qs(url.query)
        q = query.get("q")[0] if query.get("q") and len(query.get("q")) > 0 else "0"
        o = query.get("o")[0] if query.get("o") and len(query.get("o")) > 0 else "0"
        return q, int(o) if str(o).isdigit() else 0

    def parse_download_url(self, raw_url: str) -> ParsedDownloadUrl:
        parsed = urlparse(raw_url)

        host = (parsed.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]

        if "erome.com" in raw_url:
            if "/a/" in raw_url:
                return ParsedDownloadUrl(
                    parsed_url=parsed,
                    site_type="erome",
                    host=host,
                    is_album=True,
                    is_profile=False,
                )
            return ParsedDownloadUrl(
                parsed_url=parsed,
                site_type="erome",
                host=host,
                is_profile=True,
                is_album=False,
            )

        if re.search(r"https?://([a-z0-9-]+\.)?bunkr\.[a-z]{2,}", raw_url):
            is_post = any(sub in raw_url for sub in ["/v/", "/i/", "/f/"])
            return ParsedDownloadUrl(
                parsed_url=parsed,
                site_type="bunkr",
                host=host,
                is_post=is_post,
                is_profile=not is_post,
            )

        if host in ["coomer.st", "kemono.cr", "pawchive.pw"]:
            service, user, post = self.extract_ck_parameters(parsed)
            query, offset = self.extract_ck_query(parsed)

            return ParsedDownloadUrl(
                parsed_url=parsed,
                site_type="coomer_kemono",
                host=host,
                is_post=post is not None,
                is_profile=post is None,
                service=service,
                user=user,
                post=post,
                query=query,
                offset=offset,
            )

        if "simpcity.cr" in raw_url:
            return ParsedDownloadUrl(
                parsed_url=parsed,
                site_type="simpcity",
                host=host,
                is_profile=True,
            )

        if "jpg5.su" in raw_url:
            return ParsedDownloadUrl(
                parsed_url=parsed,
                site_type="jpg5",
                host=host,
                is_profile=True,
            )

        if "coomerfans.com" in raw_url:
            is_post = "/p/" in raw_url
            is_profile = "/u/" in raw_url
            return ParsedDownloadUrl(
                parsed_url=parsed,
                site_type="coomerfans",
                host=host,
                is_post=is_post,
                is_profile=is_profile,
            )

        return ParsedDownloadUrl(
            parsed_url=parsed,
            site_type="unknown",
            host=host,
        )
