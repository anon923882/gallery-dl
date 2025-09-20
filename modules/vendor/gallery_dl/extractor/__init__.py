"""Minimal extractor registry covering nhentai lookups."""

from __future__ import annotations

import re
from typing import Iterable, Optional, Pattern, Type

from .base import BaseExtractor
from .nhentai import NhentaiFavoriteExtractor, NhentaiGalleryExtractor

ExtractorType = Type[BaseExtractor]


def _compile(pattern: Pattern[str] | str) -> Pattern[str]:
    if isinstance(pattern, str):
        return re.compile(pattern)
    return pattern


def _iter_extractors() -> Iterable[ExtractorType]:
    yield NhentaiGalleryExtractor
    yield NhentaiFavoriteExtractor


def find(url: str) -> Optional[BaseExtractor]:
    """Return an extractor instance matching *url* or ``None``."""

    for extractor_cls in _iter_extractors():
        compiled = _compile(extractor_cls.pattern)
        extractor_cls.pattern = compiled
        match = compiled.match(url)
        if match:
            extractor = extractor_cls(match)
            extractor.initialize()
            return extractor
    return None


__all__ = ["find", "BaseExtractor", "NhentaiGalleryExtractor", "NhentaiFavoriteExtractor"]
