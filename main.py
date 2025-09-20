"""CLI entry point that wires the original scripts up to gallery-dl."""

from __future__ import annotations

import getpass
from pathlib import Path

import requests
import undetected_chromedriver as uc

from modules.auth import login_to_nhentai
from modules.downloader import download_manga
from modules.favorites import get_favorites_codes

PINK = "\033[38;2;255;192;203m"
RESET = "\033[0m"


def main() -> None:
    username = input(f"{PINK}Username/Email: {RESET}").strip()
    password = getpass.getpass(f"{PINK}Password: {RESET}").strip()

    print()

    session = requests.Session()
    driver = None
    codes: list[str] = []
    logged_in_username: str | None = None

    try:
        driver = uc.Chrome(version_main=133)
        logged_in_username = login_to_nhentai(driver, username, password)

        if not logged_in_username:
            print(f"[{PINK}System{RESET}] Login failed. Exiting.")
            return

        user_agent = driver.execute_script("return navigator.userAgent;")
        session.headers.update({"User-Agent": user_agent})

        for cookie in driver.get_cookies():
            session.cookies.set(cookie["name"], cookie["value"])

        codes = get_favorites_codes(session)

    finally:
        if driver is not None:
            driver.quit()

    if not logged_in_username:
        return

    if not codes:
        print(f"[{PINK}System{RESET}] No favorites detected or access denied.")
        return

    downloads_dir = Path("Downloads")
    user_dir = downloads_dir / logged_in_username
    user_dir.mkdir(parents=True, exist_ok=True)

    for code in codes:
        download_manga(session, code, user_dir)


if __name__ == "__main__":
    main()
