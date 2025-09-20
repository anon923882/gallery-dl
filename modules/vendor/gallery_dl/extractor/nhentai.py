"""Lightweight nhentai extractors derived from gallery-dl."""

from __future__ import annotations

import random
import re
from typing import Dict, Iterable, Iterator, List, Tuple

import requests

from .. import exception
from . import message
from .base import BaseExtractor

__all__ = [
    "NhentaiGalleryExtractor",
    "NhentaiFavoriteExtractor",
]


class _BaseNhentaiExtractor(BaseExtractor):
    root = "https://nhentai.net"

    def _ensure_session(self) -> requests.Session:
        if self.session is None:
            self.session = requests.Session()
        return self.session


class NhentaiGalleryExtractor(_BaseNhentaiExtractor):
    """Extractor for nhentai gallery metadata and images."""

    pattern = re.compile(r"(?:https?://)?nhentai\.net/g/(\d+)/")

    def __init__(self, match: re.Match[str]):
        super().__init__(match)
        self.gallery_id = match.group(1)
        self._metadata: Dict[str, object] | None = None
        self._images: List[Tuple[str, Dict[str, object]]] | None = None

    def initialize(self) -> None:
        self._ensure_session()

    def finalize(self) -> None:  # pragma: no cover - nothing to clean up
        pass

    def _fetch_gallery(self) -> Tuple[Dict[str, object], List[Tuple[str, Dict[str, object]]]]:
        session = self._ensure_session()
        api_url = f"{self.root}/api/gallery/{self.gallery_id}"
        response = session.get(api_url)
        if response.status_code != 200:
            raise exception.HttpError(response.status_code, f"nhentai API returned {response.status_code}")

        data = response.json()
        title = data.get("title", {})
        title_en = title.get("english") or ""
        title_ja = title.get("japanese") or ""

        tags = data.get("tags", [])
        tag_map: Dict[str, List[str]] = {}
        for tag in tags:
            tag_map.setdefault(tag.get("type", ""), []).append(tag.get("name", ""))

        language = ""
        for entry in tag_map.get("language", []):
            if entry != "translated":
                language = entry.capitalize()
                break

        metadata: Dict[str, object] = {
            "title": title_en or title_ja,
            "title_en": title_en,
            "title_ja": title_ja,
            "gallery_id": data.get("id"),
            "media_id": int(data.get("media_id", 0)),
            "date": data.get("upload_date"),
            "scanlator": data.get("scanlator"),
            "artist": tag_map.get("artist", []),
            "group": tag_map.get("group", []),
            "parody": tag_map.get("parody", []),
            "characters": tag_map.get("character", []),
            "tags": tag_map.get("tag", []),
            "type": (tag_map.get("category", [""]) or [""])[0],
            "lang": language.lower()[:2] if language else "",
            "language": language,
        }

        media_id = data.get("media_id")
        if not media_id:
            raise exception.GalleryDLException("Gallery metadata missing media_id")

        images: List[Tuple[str, Dict[str, object]]] = []
        extension_map = {"j": "jpg", "p": "png", "g": "gif", "w": "webp", "a": "avif"}
        for index, image in enumerate(data.get("images", {}).get("pages", []), 1):
            extension = extension_map.get(image.get("t"), "jpg")
            url = f"https://i{random.randint(1,4)}.nhentai.net/galleries/{media_id}/{index}.{extension}"
            images.append((url, {"num": index, "extension": extension}))

        return metadata, images

    def items(self) -> Iterator[Tuple[int, object, object]]:
        if self._metadata is None or self._images is None:
            self._metadata, self._images = self._fetch_gallery()

        yield message.Message.Directory, self._metadata
        for url, extra in self._images:
            yield message.Message.Url, url, extra


class NhentaiFavoriteExtractor(_BaseNhentaiExtractor):
    """Extractor for iterating nhentai favorite gallery ids."""

    pattern = re.compile(r"(?:https?://)?nhentai\.net(/favorites/?)(?:\?([^#]+))?$")

    def initialize(self) -> None:
        self._ensure_session()

    def finalize(self) -> None:  # pragma: no cover - nothing to clean up
        pass

    def _iter_gallery_ids(self) -> Iterable[str]:
        session = self._ensure_session()
        page = 1
        while True:
            response = session.get(f"{self.root}/favorites/", params={"page": page})
            if response.status_code == 404:
                return
            if response.status_code != 200:
                raise exception.HttpError(response.status_code, "Unable to load favorites page")

            html = response.text
            if "You must be logged in" in html:
                raise exception.GalleryDLException("Authentication required to access favorites")

            ids = set(re.findall(r'data-id="(\d+)"', html))
            if not ids:
                ids.update(re.findall(r"/g/(\d+)/", html))

            if not ids:
                return

            for gallery_id in sorted(ids):
                yield gallery_id

            if 'class="next"' not in html:
                return
            page += 1

    def items(self) -> Iterator[Tuple[int, object, object]]:
        for gallery_id in self._iter_gallery_ids():
            url = f"{self.root}/g/{gallery_id}/"
            yield message.Message.Queue, url, {"gallery_id": int(gallery_id)}
