"""
Check what input fields exist on the login page
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'selenium_script'))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def check_fields():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        print("Opening Runi website...")
        driver.get("https://my.runi.ac.il/my.policy")
        time.sleep(3)
        
        # Handle logout page
        if "logout" in driver.current_url or "errorcode" in driver.current_url:
            print("Clicking continue link...")
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and href == "https://my.runi.ac.il/":
                    link.click()
                    time.sleep(3)
                    break
        
        print(f"Current URL: {driver.current_url}")
        
        # Show all buttons first
        print("\n=== Buttons on page ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {len(buttons)} buttons")
        for i, btn in enumerate(buttons):
            text = btn.text.strip()
            btn_id = btn.get_attribute("id")
            btn_class = btn.get_attribute("class")
            print(f"Button {i+1}: text='{text}' id='{btn_id}' class='{btn_class}'")
        
        # Click login button
        print("\nLooking for login button...")
        try:
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'כניסה')]")))
            print("Found and clicking login button...")
            login_btn.click()
            time.sleep(5)
        except Exception as e:
            print(f"Could not find login button with text 'כניסה': {e}")
            print("\nTrying alternative methods...")
            
            # Try to find any button with specific classes or attributes
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if 'כניסה' in btn.text or 'login' in btn.get_attribute("class").lower():
                    print(f"Trying button: {btn.text}")
                    btn.click()
                    time.sleep(5)
                    break
        
        print(f"\nAfter login click URL: {driver.current_url}")
        
        # Find all input fields
        print("\n=== All input fields on page ===")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input fields:")
        
        for i, inp in enumerate(inputs):
            field_id = inp.get_attribute("id")
            field_name = inp.get_attribute("name")
            field_type = inp.get_attribute("type")
            field_placeholder = inp.get_attribute("placeholder")
            field_class = inp.get_attribute("class")
            
            print(f"\nInput {i+1}:")
            print(f"  ID: {field_id}")
            print(f"  Name: {field_name}")
            print(f"  Type: {field_type}")
            print(f"  Placeholder: {field_placeholder}")
            print(f"  Class: {field_class}")
        
        print("\n=== Browser will stay open for 2 minutes ===")
        print("Check the page and note the field IDs")
        time.sleep(120)
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_fields()
