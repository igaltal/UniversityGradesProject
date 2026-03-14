"""
Debug script: list login form fields on Runi portal.
Run: python scripts/check_login_fields.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://my.runi.ac.il/my.policy")
        time.sleep(3)

        if "logout" in driver.current_url or "errorcode" in driver.current_url:
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                if link.get_attribute("href") == "https://my.runi.ac.il/":
                    link.click()
                    time.sleep(3)
                    break

        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'כניסה')]"))
        )
        login_btn.click()
        time.sleep(5)

        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"\nFound {len(inputs)} input fields:")
        for i, inp in enumerate(inputs):
            print(
                f"  {i+1}: id={inp.get_attribute('id')} "
                f"name={inp.get_attribute('name')} "
                f"type={inp.get_attribute('type')}"
            )

        print("\nBrowser stays open 2 minutes.")
        time.sleep(120)
    except (KeyboardInterrupt, Exception) as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
