"""Favorite handling powered by gallery-dl's nhentai extractor."""

from gallery_dl import exception, extractor

PINK = "\033[38;2;255;192;203m"
RESET = "\033[0m"


FAVORITES_URL = "https://nhentai.net/favorites/"


def get_favorites_codes():
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
        seen = set()
        codes = []

        for gallery_id in extr._pagination():  # type: ignore[attr-defined]
            if gallery_id not in seen:
                seen.add(gallery_id)
                codes.append(gallery_id)

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
