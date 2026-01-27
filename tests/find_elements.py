"""
Debug script to help find the correct elements on Runi website
This script opens the website and waits so you can inspect elements
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'selenium_script'))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def find_elements():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("\nOpening Runi website...")
        driver.get("https://my.runi.ac.il/my.policy")
        print("Waiting for page to load...")
        time.sleep(3)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Check if we're on logout page and need to click continue
        if "logout" in driver.current_url or "errorcode" in driver.current_url:
            print("\nDetected logout page, looking for continue link...")
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and href == "https://my.runi.ac.il/":
                        print(f"Found continue link, clicking...")
                        link.click()
                        time.sleep(3)
                        print(f"New URL: {driver.current_url}")
                        print(f"New title: {driver.title}")
                        break
            except Exception as e:
                print(f"Could not click continue: {e}")
        
        print("\n=== Instructions ===")
        print("1. The browser is now open")
        print("2. Look for the login button on the page")
        print("3. Right-click on it -> Inspect")
        print("4. In the inspector, right-click the element -> Copy -> Copy XPath")
        print("5. Update config.py with the new XPath")
        print("\nCommon element searches:")
        
        # Try to find login button by different methods
        print("\n--- Searching for login elements ---")
        
        # Try by text
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'כניסה')]")
            if elements:
                print(f"Found {len(elements)} elements with text 'כניסה'")
                for i, elem in enumerate(elements[:3]):
                    print(f"  Element {i+1}: tag={elem.tag_name}")
        except Exception as e:
            print(f"No elements with 'כניסה': {e}")
        
        # Try by common button patterns
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"\nFound {len(buttons)} buttons on page")
            for i, btn in enumerate(buttons[:5]):
                try:
                    text = btn.text.strip()
                    if text:
                        print(f"  Button {i+1}: '{text}'")
                except:
                    pass
        except Exception as e:
            print(f"Could not find buttons: {e}")
        
        # Try by links
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"\nFound {len(links)} links on page")
            for i, link in enumerate(links[:10]):
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href")
                    if text:
                        print(f"  Link {i+1}: '{text}' -> {href}")
                except:
                    pass
        except Exception as e:
            print(f"Could not find links: {e}")
        
        print("\n=== Browser will stay open for 2 minutes ===")
        print("Use this time to inspect elements and find the correct XPath")
        print("Press Ctrl+C to close earlier\n")
        
        time.sleep(120)
        
    except KeyboardInterrupt:
        print("\nClosing browser...")
    finally:
        driver.quit()
        print("Done!")

if __name__ == "__main__":
    try:
        find_elements()
    except KeyboardInterrupt:
        print("\nStopped by user")
