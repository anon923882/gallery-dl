"""Download helpers that lean on gallery-dl for nhentai metadata."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests
from PIL import Image

from modules.colors import PINK, RESET

try:  # Prefer an installed gallery-dl first
    from gallery_dl import exception, extractor
    from gallery_dl.extractor.message import Message
except ModuleNotFoundError:  # Fall back to the bundled minimal subset
    from .vendor.gallery_dl import exception, extractor
    from .vendor.gallery_dl.extractor.message import Message

INVALID_CHARS = '<>:"/\\|?*'


def _sanitize_title(title: str, code: str) -> str:
    collapsed = " ".join(title.split())
    cleaned = "".join((c if c not in INVALID_CHARS else " ") for c in collapsed)
    safe = " ".join(cleaned.split()).strip()
    return safe or f"gallery-{code}"


def _update_extractor_session(extr, session: requests.Session) -> None:
    cookies = session.cookies.get_dict()
    if cookies:
        extr.session.cookies.update(cookies)

    user_agent = session.headers.get("User-Agent")
    if user_agent:
        extr.session.headers["User-Agent"] = user_agent


def _collect_gallery_data(extr) -> Tuple[Dict, List[Tuple[int, str, str]]]:
    metadata: Dict = {}
    images: List[Tuple[int, str, str]] = []

    for message in extr.items():
        if not message:
            continue

        msg_type = message[0]

        if msg_type == Message.Directory and len(message) >= 2:
            metadata = dict(message[1])

        elif msg_type == Message.Url and len(message) >= 3:
            url = message[1]
            data = dict(message[2]) if isinstance(message[2], dict) else {}
            num = int(data.get("num", len(images) + 1))
            extension = data.get("extension", "jpg")
            images.append((num, url, extension))

    images.sort(key=lambda item: item[0])
    return metadata, images


def download_image(session: requests.Session, img_url: str, filename: Path) -> None:
    response = session.get(img_url, stream=True)
    response.raise_for_status()

    with open(filename, "wb") as handle:
        for chunk in response.iter_content(1 << 14):
            if chunk:
                handle.write(chunk)


def _write_metadata_file(metadata: Dict, code: str, total_pages: int, target_dir: Path) -> None:
    primary_title = metadata.get("title_en") or metadata.get("title") or f"Gallery {code}"
    secondary_title = metadata.get("title_ja")

    def _format_section(title: str, values: Iterable[str]) -> List[str]:
        entries = [value for value in values if value]
        if not entries:
            entries = ["N/A"]
        return [f"{title}:"] + [f" - {entry}" for entry in entries] + [""]

    sections: List[str] = []
    sections.extend(["Title:", primary_title, ""])

    if secondary_title and secondary_title != primary_title:
        sections.extend([secondary_title, ""])

    sections.extend([f"Code: {code}", ""])

    sections.extend(_format_section("Parodies", metadata.get("parody", [])))
    sections.extend(_format_section("Characters", metadata.get("characters", [])))
    sections.extend(_format_section("Tags", metadata.get("tags", [])))
    sections.extend(_format_section("Artists", metadata.get("artist", [])))
    sections.extend(_format_section("Groups", metadata.get("group", [])))

    language = metadata.get("language")
    sections.extend(_format_section("Languages", [language] if language else []))

    category = metadata.get("type")
    sections.extend(_format_section("Categories", [category] if category else []))

    sections.extend(["Pages:", f" - {total_pages}", ""])

    scanlator = metadata.get("scanlator")
    if scanlator:
        sections.extend(["Scanlator:", f" - {scanlator}", ""])

    info_path = target_dir / "info.txt"
    info_path.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")


def _create_cover_image(manga_dir: Path, first_image: Path) -> None:
    cover_path = manga_dir / "cover.png"

    with Image.open(first_image) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(cover_path, "PNG")

    directory_file = manga_dir / ".directory"
    directory_file.write_text("[Desktop Entry]\nIcon=./cover.png\n", encoding="utf-8")

    try:
        # Optional: update desktop icon cache if available on the system
        import subprocess

        subprocess.run(
            ["xdg-desktop-icon", "install", "--novendor", str(directory_file)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def download_manga(session: requests.Session, code: str, base_dir=".") -> bool:
    """Download a nhentai gallery using gallery-dl's metadata helpers."""

    print(f"\n[{PINK}System{RESET}] Processing code: {code}")

    url = f"https://nhentai.net/g/{code}/"
    extr = extractor.find(url)
    if extr is None:
        print(f"[{PINK}System{RESET}] Unable to build gallery-dl extractor for code {code}")
        return False

    try:
        extr.initialize()
        _update_extractor_session(extr, session)

        metadata, images = _collect_gallery_data(extr)
        if not metadata or not images:
            print(f"[{PINK}System{RESET}] Failed to retrieve gallery data for code {code}")
            return False

    except exception.GalleryDLException as exc:
        print(f"[{PINK}System{RESET}] gallery-dl reported an error: {exc}")
        return False

    except Exception as exc:  # pragma: no cover - fallback logging
        print(f"[{PINK}System{RESET}] Unexpected error while downloading: {exc}")
        return False

    finally:
        try:
            extr.finalize()
        except Exception:
            pass

    gallery_title = metadata.get("title") or metadata.get("title_en") or f"Gallery {code}"
    safe_title = _sanitize_title(gallery_title, code)

    manga_dir = Path(base_dir) / safe_title

    if manga_dir.exists():
        print(f"[{PINK}System{RESET}] Manga '{safe_title}' already exists. Skipping.")
        return True

    manga_dir.mkdir(parents=True, exist_ok=True)
    print(f"[{PINK}System{RESET}] Created directory: {manga_dir}")

    download_targets = [
        (url, manga_dir / f"{num:03d}.{extension}")
        for num, url, extension in images
    ]

    total = len(download_targets)
    successes = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(download_image, session, url, path)
            for url, path in download_targets
        ]

        for index, future in enumerate(futures, 1):
            try:
                future.result()
                successes += 1
                print(
                    f"\r[{PINK}System{RESET}] Downloading: {index}/{total}",
                    end="",
                    flush=True,
                )
            except Exception as exc:
                print(
                    f"\n[{PINK}System{RESET}] Error downloading image {index} for {safe_title}: {exc}"
                )

    print()

    if successes:
        _write_metadata_file(metadata, code, total, manga_dir)

        first_image = download_targets[0][1]
        if first_image.exists():
            try:
                _create_cover_image(manga_dir, first_image)
                print(f"[{PINK}System{RESET}] Cover image set as folder icon")
            except Exception as exc:
                print(f"[{PINK}System{RESET}] Error creating cover: {exc}")

    print(f"[{PINK}System{RESET}] Completed: {safe_title}")
    return successes == total
