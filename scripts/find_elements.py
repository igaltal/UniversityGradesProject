"""
Debug script: find correct elements on Runi website for XPath discovery.
Run: python scripts/find_elements.py (from project root, after pip install -e .)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    try:
        print("\nOpening Runi website...")
        driver.get("https://my.runi.ac.il/my.policy")
        time.sleep(3)

        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        if "logout" in driver.current_url or "errorcode" in driver.current_url:
            print("\nDetected logout page, looking for continue link...")
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                if link.get_attribute("href") == "https://my.runi.ac.il/":
                    link.click()
                    time.sleep(3)
                    break

        print("\n=== Instructions ===")
        print("1. Browser is open — inspect elements to find XPaths")
        print("2. Right-click -> Inspect -> Copy -> Copy XPath")
        print("3. Update university_grades/core/config.py\n")

        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'כניסה')]")
        if elements:
            print(f"Found {len(elements)} elements with 'כניסה'")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {len(buttons)} buttons")
        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(links)} links")

        print("\n=== Browser stays open 2 minutes ===")
        time.sleep(120)
    except KeyboardInterrupt:
        print("\nClosing...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
