"""Authentication helpers for nhentai."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

PINK = "\033[38;2;255;192;203m"
RESET = "\033[0m"


def login_to_nhentai(driver, username, password):
    """Log into nhentai with *driver* and return the account name.

    The function keeps the manual CAPTCHA solving flow from the original
    scripts, but returns the detected username on success so callers can
    immediately use it for download directory management.  ``None`` is
    returned if authentication failed or timed out.
    """

    print(f"[{PINK}System{RESET}] Navigating to login page")
    driver.get("https://nhentai.net/login/")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "csrfmiddlewaretoken"))
        )

        print(f"[{PINK}System{RESET}] Entering credentials")
        driver.find_element(By.ID, "id_username_or_email").send_keys(username)
        driver.find_element(By.ID, "id_password").send_keys(password)

        print(
            f"[{PINK}System{RESET}] Please solve the CAPTCHA and click the Login button"
        )

        WebDriverWait(driver, 300).until(
            lambda d: d.current_url == "https://nhentai.net/"
        )

        print(f"[{PINK}System{RESET}] Detected redirect to homepage")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/users/"]'))
        )

        profile_link = driver.find_element(By.CSS_SELECTOR, 'a[href^="/users/"]')
        username_element = profile_link.find_element(By.CSS_SELECTOR, "span.username")
        logged_in_username = username_element.text.strip()

        if logged_in_username.lower() == username.lower():
            print(
                f"[{PINK}System{RESET}] Successfully logged in as "
                f"{logged_in_username}"
            )
        else:
            print(
                f"[{PINK}System{RESET}] Logged in as {logged_in_username} (input: {username})"
            )

        return logged_in_username

    except Exception as exc:  # pragma: no cover - best effort logging
        print(f"[{PINK}System{RESET}] Login error: {exc}")
        return None
