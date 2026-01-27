"""
Debug what happens after clicking student info station
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'selenium_script'))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from config import Config

def debug_login():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        print("Opening website...")
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
        
        # Click login button
        print("Clicking login button...")
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' or contains(@class, 'submit')]")))
        login_btn.click()
        time.sleep(1)
        
        # Enter credentials
        print("Entering credentials...")
        driver.find_element(By.ID, "input_1").send_keys(Config.RUNI_USERNAME)
        driver.find_element(By.ID, "input_2").send_keys(Config.RUNI_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        print("Submitted login")
        time.sleep(10)
        
        # Click student info station
        print("Clicking student info station...")
        original_window = driver.current_window_handle
        info_station = wait.until(EC.element_to_be_clickable((By.XPATH, "//img[@alt='תחנת מידע לסטודנט']")))
        info_station.find_element(By.XPATH, "./..").click()
        print("Clicked!")
        time.sleep(5)
        
        # Debug info
        print(f"\n=== After clicking student info station ===")
        print(f"Windows: {len(driver.window_handles)}")
        print(f"Current URL: {driver.current_url}")
        
        # Check for new windows
        if len(driver.window_handles) > 1:
            print("Multiple windows detected:")
            for i, handle in enumerate(driver.window_handles):
                driver.switch_to.window(handle)
                print(f"  Window {i}: {driver.current_url}")
            # Stay on the new window
            driver.switch_to.window(driver.window_handles[-1])
            print(f"Switched to last window: {driver.current_url}")
        
        # Check for iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\nIframes found: {len(iframes)}")
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute("src")
            name = iframe.get_attribute("name")
            print(f"  Iframe {i}: src={src}, name={name}")
        
        # If iframe exists, switch to it
        if iframes:
            print(f"\nSwitching to first iframe...")
            driver.switch_to.frame(iframes[0])
            print(f"Switched! URL: {driver.current_url}")
        
        # Find all buttons
        print(f"\n=== Buttons on page ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {len(buttons)} buttons")
        for i, btn in enumerate(buttons[:10]):
            text = btn.text.strip()
            classes = btn.get_attribute("class")
            if text or "menu" in classes.lower():
                print(f"  Button {i+1}: '{text}' class='{classes}'")
        
        # Find menu items
        print(f"\n=== Menu items ===")
        menu_items = driver.find_elements(By.CLASS_NAME, "menu-title")
        print(f"Found {len(menu_items)} menu-title elements")
        for i, item in enumerate(menu_items[:10]):
            print(f"  Menu {i+1}: '{item.text}'")
        
        print("\n=== Browser will stay open for 2 minutes ===")
        print("Inspect the page to find the correct selectors")
        time.sleep(120)
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    try:
        Config.validate()
        debug_login()
    except ValueError as e:
        print(f"Config error: {e}")
