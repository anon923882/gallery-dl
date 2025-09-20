"""Download helpers that delegate to gallery-dl."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

from gallery_dl import config as gdl_config, exception, job

PINK = "\033[38;2;255;192;203m"
RESET = "\033[0m"


def configure_gallery_dl(base_directory: Path, cookies: Dict[str, str], user_agent: str) -> None:
    """Apply runtime gallery-dl configuration for nhentai downloads."""

    base_directory.mkdir(parents=True, exist_ok=True)
    cookie_jar = {name: value for name, value in cookies.items() if value}

    gdl_config.set(("output",), "mode", "null")
    gdl_config.set(("extractor",), "base-directory", str(base_directory))
    gdl_config.set(("extractor", "nhentai"), "cookies", cookie_jar)
    gdl_config.set(("extractor", "nhentai"), "user-agent", user_agent)
    gdl_config.set(("extractor", "nhentai"), "directory", ["{title} ({gallery_id})"])
    gdl_config.set(("extractor", "nhentai"), "filename", "{num:>03}.{extension}")

    logging.getLogger("gallery-dl").setLevel(logging.WARNING)
    logging.getLogger("download").setLevel(logging.WARNING)
    logging.getLogger("nhentai").setLevel(logging.WARNING)


def download_manga(code: str) -> bool:
    """Download a nhentai gallery using gallery-dl."""

    url = f"https://nhentai.net/g/{code}/"
    print(f"\n[{PINK}System{RESET}] Processing code: {code}")

    try:
        dl_job = job.DownloadJob(url)
        status = dl_job.run()
    except exception.GalleryDLException as exc:
        print(f"[{PINK}System{RESET}] gallery-dl reported an error: {exc}")
        return False
    except Exception as exc:  # pragma: no cover - fallback logging
        print(f"[{PINK}System{RESET}] Unexpected error while downloading: {exc}")
        return False

    if status == 0:
        print(f"[{PINK}System{RESET}] Completed code {code}")
        return True

    print(f"[{PINK}System{RESET}] gallery-dl returned status {status} for code {code}")
    return False
