"""Shared base class for lightweight extractors."""

from __future__ import annotations

import re
from typing import Pattern


class BaseExtractor:
    """Provide pattern handling and a placeholder session attribute."""

    pattern: Pattern[str]

    def __init__(self, match: re.Match[str]):
        self.match = match
        self.url = match.group(0)
        self.session = None

    def initialize(self) -> None:  # pragma: no cover - subclasses may override
        pass

    def finalize(self) -> None:  # pragma: no cover - subclasses may override
        pass

    def items(self):  # pragma: no cover - interface stub
        raise NotImplementedError
