"""Utility helpers for consistent terminal colors across platforms."""

from __future__ import annotations

import os
import sys

_RAW_PINK = "\033[38;2;255;192;203m"
_RAW_RESET = "\033[0m"


def _supports_ansi() -> bool:
    """Return True when the current terminal supports ANSI color codes."""

    if os.environ.get("NO_COLOR"):
        return False

    if not sys.stdout.isatty():
        return False

    if os.name == "nt":  # pragma: no cover - platform-specific behaviour
        try:
            import colorama

            colorama.just_fix_windows_console()
            return True
        except Exception:
            return False

    return True


if _supports_ansi():
    PINK = _RAW_PINK
    RESET = _RAW_RESET
else:
    PINK = ""
    RESET = ""

__all__ = ["PINK", "RESET"]
