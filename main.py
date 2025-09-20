"""CLI entry point that wires the original scripts up to gallery-dl."""

from __future__ import annotations

import getpass
from pathlib import Path
from typing import Optional

import requests
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager

from modules.auth import login_to_nhentai
from modules.colors import PINK, RESET
from modules.downloader import download_manga
from modules.favorites import get_favorites_codes


def _create_browser(headless: bool = False) -> uc.Chrome:
    """Instantiate an undetected Chrome driver managed by webdriver-manager."""

    options = uc.ChromeOptions()
    if headless:
        # ``--headless=new`` keeps the modern headless mode for recent Chrome
        options.add_argument("--headless=new")

    driver_path = ChromeDriverManager().install()

    return uc.Chrome(
        options=options,
        driver_executable_path=driver_path,
    )


def main() -> None:
    username = input(f"{PINK}Username/Email: {RESET}").strip()
    password = getpass.getpass(f"{PINK}Password: {RESET}").strip()

    print()

    session = requests.Session()
    driver: Optional[uc.Chrome] = None
    codes: list[str] = []
    logged_in_username: Optional[str] = None

    try:
        driver = _create_browser()
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
