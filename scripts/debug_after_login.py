"""
Debug script: post-login flow inspection.
Run: python scripts/debug_after_login.py (requires RUNI_USERNAME, RUNI_PASSWORD in .env)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from university_grades.core import Config


def main():
    Config.validate()

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://my.runi.ac.il/my.policy")
        time.sleep(3)

        if "logout" in driver.current_url or "errorcode" in driver.current_url:
            for link in driver.find_elements(By.TAG_NAME, "a"):
                if link.get_attribute("href") == "https://my.runi.ac.il/":
                    link.click()
                    time.sleep(3)
                    break

        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, Config.XPATHS["login_button"]))
        )
        login_btn.click()
        time.sleep(1)

        driver.find_element(By.ID, Config.XPATHS["username_field"]).send_keys(
            Config.RUNI_USERNAME
        )
        driver.find_element(By.ID, Config.XPATHS["password_field"]).send_keys(
            Config.RUNI_PASSWORD
        )
        driver.find_element(By.XPATH, Config.XPATHS["submit_button"]).click()
        time.sleep(10)

        info_station = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, Config.XPATHS["student_info_station"])
            )
        )
        info_station.find_element(By.XPATH, "./..").click()
        time.sleep(5)

        print(f"\nWindows: {len(driver.window_handles)}")
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Iframes: {len(iframes)}")
        if iframes:
            driver.switch_to.frame(iframes[0])

        menu_items = driver.find_elements(By.CLASS_NAME, "menu-title")
        print(f"Menu items: {len(menu_items)}")
        for i, item in enumerate(menu_items[:10]):
            print(f"  {i+1}: {item.text}")

        print("\nBrowser stays open 2 minutes.")
        time.sleep(120)
    except (KeyboardInterrupt, Exception) as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
