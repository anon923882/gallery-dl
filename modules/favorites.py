"""Favorite handling powered by gallery-dl's nhentai extractor."""

from __future__ import annotations

from typing import Iterable, List

try:  # Prefer an installed gallery-dl when available
    from gallery_dl import exception, extractor
    from gallery_dl.extractor.message import Message
except ModuleNotFoundError:  # Provide a bundled fallback for standalone use
    from .vendor.gallery_dl import exception, extractor
    from .vendor.gallery_dl.extractor.message import Message

PINK = "\033[38;2;255;192;203m"
RESET = "\033[0m"


FAVORITES_URL = "https://nhentai.net/favorites/"


def _update_extractor_session(extr, session) -> None:
    """Apply the caller's cookies and headers to a gallery-dl extractor."""

    cookies = session.cookies.get_dict()
    if cookies:
        extr.session.cookies.update(cookies)

    user_agent = session.headers.get("User-Agent")
    if user_agent:
        extr.session.headers["User-Agent"] = user_agent


def _iter_favorite_gallery_ids(extr) -> Iterable[str]:
    """Yield gallery ids exposed by a favorites extractor."""

    seen = set()

    for message in extr.items():
        if not message:
            continue

        msg_type = message[0]
        if msg_type == Message.Queue and len(message) >= 3:
            data = message[2] or {}
            gallery_id = data.get("gallery_id")

            if gallery_id is None:
                url = message[1]
                gallery_id = url.rstrip("/").split("/")[-1]

            gallery_id = str(gallery_id)

            if gallery_id and gallery_id not in seen:
                seen.add(gallery_id)
                yield gallery_id


def get_favorites_codes(session) -> List[str]:
    """Return the user's favorite gallery codes using gallery-dl."""

    print(f"[{PINK}System{RESET}] Retrieving favorite codes via gallery-dl")

    extr = extractor.find(FAVORITES_URL)
    if extr is None:
        print(
            f"[{PINK}System{RESET}] Unable to build gallery-dl extractor for favorites"
        )
        return []

    try:
        extr.initialize()
        _update_extractor_session(extr, session)

        codes = list(_iter_favorite_gallery_ids(extr))
        print(f"[{PINK}System{RESET}] Found {len(codes)} total favorites")
        return codes

    except exception.GalleryDLException as exc:
        print(f"[{PINK}System{RESET}] gallery-dl error while fetching favorites: {exc}")
        return []

    except Exception as exc:  # pragma: no cover - fallback logging
        print(f"[{PINK}System{RESET}] Unexpected error while fetching favorites: {exc}")
        return []

    finally:
        try:
            extr.finalize()
        except Exception:
            pass
