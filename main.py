"""CLI entry point that wires the original scripts up to gallery-dl."""

from __future__ import annotations

import getpass
from pathlib import Path

import undetected_chromedriver as uc

from modules.auth import login_to_nhentai
from modules.downloader import configure_gallery_dl, download_manga
from modules.favorites import get_favorites_codes

PINK = "\033[38;2;255;192;203m"
RESET = "\033[0m"


def collect_cookies(driver) -> dict[str, str]:
    """Convert Selenium cookies to a plain dictionary."""

    cookies = {}
    for cookie in driver.get_cookies():
        cookies[cookie["name"]] = cookie["value"]
    return cookies


def main() -> None:
    username = input(f"{PINK}Username/Email: {RESET}").strip()
    password = getpass.getpass(f"{PINK}Password: {RESET}").strip()

    print()

    driver = None
    codes: list[str] = []

    try:
        driver = uc.Chrome(version_main=133)
        logged_in_username = login_to_nhentai(driver, username, password)

        if not logged_in_username:
            print(f"[{PINK}System{RESET}] Login failed. Exiting.")
            return

        user_agent = driver.execute_script("return navigator.userAgent;")
        cookies = collect_cookies(driver)

        downloads_dir = Path("Downloads")
        user_dir = downloads_dir / logged_in_username
        configure_gallery_dl(user_dir, cookies, user_agent)

        codes = get_favorites_codes()

    finally:
        if driver is not None:
            driver.quit()

    if not codes:
        print(f"[{PINK}System{RESET}] No favorites detected or access denied.")
        return

    for code in codes:
        download_manga(code)


if __name__ == "__main__":
    main()
