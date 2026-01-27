import threading
import logging
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import telebot
import datetime
import sqlite3
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('grade_checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot with config
bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)

# Track which grades have been notified
course_message_flags = {}


def get_grades():
    """Fetch grades from database"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT course, grade FROM grades')
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        logger.error(f"Database read error: {e}")
        return []


def update_grade(course, grade):
    """Update grade in database"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE grades SET grade = ? WHERE course = ?', (grade, course))
        conn.commit()
        conn.close()
        logger.info(f"Updated {course} to {grade}")
    except Exception as e:
        logger.error(f"Database update error for {course}: {e}")


def send_telegram_message(message):
    """Send message via Telegram with error handling"""
    try:
        bot.send_message(Config.TELEGRAM_CHAT_ID, message)
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def extract_and_print_grades(driver):
    """Extract grades from page and update database"""
    grades_found = []
    
    try:
        # Find all course cards
        course_cards = driver.find_elements(By.CLASS_NAME, "Box_ph")
        logger.info(f"Found {len(course_cards)} course cards")
        
        for card in course_cards:
            try:
                # Extract course name from h2
                course_name_elem = card.find_element(By.TAG_NAME, "h2")
                course_name = course_name_elem.text.strip()
                
                # Extract grade from strong tag
                grade_elem = card.find_element(By.TAG_NAME, "strong")
                grade_text = grade_elem.text.strip()
                
                logger.info(f"{course_name}: {grade_text}")
                
                # Parse grade value (check for Hebrew "Grade:" prefix)
                if "ציון:" in grade_text or "Grade:" in grade_text:
                    grade_value = grade_text.replace("ציון:", "").replace("Grade:", "").strip()
                    
                    # Check if grade is not yet available (Hebrew "not yet")
                    if grade_value != "טרם" and grade_value.lower() != "not yet":
                        # Update database
                        update_grade(course_name, grade_value)
                        
                        # Send notification
                        course_key = course_name.split()[0]  # Use course code as key
                        if course_key not in course_message_flags:
                            course_message_flags[course_key] = False
                        
                        if not course_message_flags[course_key]:
                            message = f"New grade for {course_name}: {grade_value}"
                            if send_telegram_message(message):
                                course_message_flags[course_key] = True
                        
                        grades_found.append((course_name, grade_value))
                    else:
                        grades_found.append((course_name, "Not available"))
                        
            except Exception as e:
                logger.warning(f"Could not extract grade from card: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to extract grades: {e}")
    
    return grades_found


def login_and_navigate(driver, wait):
    """Handle login and navigation to grades page"""
    try:
        # Open website
        driver.get("https://my.runi.ac.il/my.policy")
        logger.info(f"Loaded page: {driver.current_url}")
        time.sleep(3)
        
        # Check if we're on logout page and need to click continue
        if "logout" in driver.current_url or "errorcode" in driver.current_url:
            logger.info("Detected logout page, looking for continue link...")
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and href == "https://my.runi.ac.il/":
                    logger.info("Clicking continue link...")
                    link.click()
                    time.sleep(3)
                    logger.info(f"After continue: {driver.current_url}")
                    break

        original_window = driver.current_window_handle

        # Click login button
        logger.info("Looking for login button...")
        wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['login_button'])))
        driver.find_element(By.XPATH, Config.XPATHS['login_button']).click()
        logger.info("Clicked login button")
        time.sleep(1)
    except Exception as e:
        logger.error(f"Failed at login button step: {e}")
        raise

    try:
        # Enter credentials
        logger.info("Entering credentials...")
        driver.find_element(By.ID, Config.XPATHS['username_field']).send_keys(Config.RUNI_USERNAME)
        driver.find_element(By.ID, Config.XPATHS['password_field']).send_keys(Config.RUNI_PASSWORD)
        driver.find_element(By.XPATH, Config.XPATHS['submit_button']).click()
        logger.info("Submitted login form")
        time.sleep(10)
    except Exception as e:
        logger.error(f"Failed at credentials step: {e}")
        raise

    try:
        # Click on student info station
        logger.info("Looking for student info station...")
        original_window = driver.current_window_handle
        
        wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['student_info_station'])))
        info_station = driver.find_element(By.XPATH, Config.XPATHS['student_info_station'])
        info_station.find_element(By.XPATH, "./..").click()
        logger.info("Clicked student info station")
        time.sleep(5)
        
        # Check if new window/tab opened
        if len(driver.window_handles) > 1:
            logger.info(f"New window detected, switching... ({len(driver.window_handles)} windows)")
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    logger.info(f"Switched to new window: {driver.current_url}")
                    break
        
        # Check for iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            logger.info(f"Found {len(iframes)} iframes, switching to first one")
            driver.switch_to.frame(iframes[0])
            logger.info("Switched to iframe")
            
    except Exception as e:
        logger.error(f"Failed at student info station step: {e}")
        raise

    try:
        # Click on grades tab
        logger.info("Looking for grades tab...")
        logger.info(f"Current URL: {driver.current_url}")
        
        # Wait for page to load
        time.sleep(3)
        
        # Try to find all menu items first
        menu_items = driver.find_elements(By.CLASS_NAME, "menu-title")
        logger.info(f"Found {len(menu_items)} menu items")
        for item in menu_items[:5]:
            logger.info(f"Menu item: {item.text}")
        
        grades_tab = wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['grades_tab'])))
        grades_tab.click()
        logger.info("Clicked grades tab")
        time.sleep(2)
    except Exception as e:
        logger.error(f"Failed at grades tab step: {e}")
        raise

    try:
        # Click on grades list
        logger.info("Looking for grades list...")
        wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['grades_list'])))
        driver.find_element(By.XPATH, Config.XPATHS['grades_list']).click()
        logger.info("Clicked grades list")
        time.sleep(3)
    except Exception as e:
        logger.error(f"Failed at grades list step: {e}")
        raise

    try:
        # Select year 2025
        logger.info("Selecting year 2025...")
        year_control = wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['year_control'])))
        year_control.click()
        logger.info("Clicked year dropdown")
        time.sleep(1)
        
        # Wait for dropdown to open and find 2025 option
        year_2025 = wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['year_2025'])))
        year_2025.click()
        logger.info("Selected year 2025")
        time.sleep(1)
    except Exception as e:
        logger.error(f"Failed at year selection: {e}")
        logger.info("Trying alternative method...")
        try:
            # Try clicking on existing year display and then selecting
            year_item = driver.find_element(By.XPATH, "//div[@data-value='2026' and contains(@class, 'item')]")
            year_item.click()
            time.sleep(1)
            year_2025 = driver.find_element(By.XPATH, "//div[@data-value='2025']")
            year_2025.click()
            logger.info("Selected year 2025 via alternative method")
        except Exception as e2:
            logger.error(f"Alternative method also failed: {e2}")
            raise

    try:
        # Select semester 2
        logger.info("Selecting semester 2...")
        semester_control = wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['semester_control'])))
        semester_control.click()
        logger.info("Clicked semester dropdown")
        time.sleep(1)
        
        semester_2 = wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['semester_2'])))
        semester_2.click()
        logger.info("Selected semester 2")
        time.sleep(1)
    except Exception as e:
        logger.error(f"Failed at semester selection: {e}")
        raise

    try:
        # Click submit button
        logger.info("Clicking submit button...")
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, Config.XPATHS['submit_button_grades'])))
        submit_btn.click()
        logger.info("Clicked submit")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Failed at submit step: {e}")
        raise

    try:
        # Open semester 2 details if not already open
        logger.info("Opening semester 2 details...")
        details_elem = driver.find_element(By.XPATH, Config.XPATHS['semester_2_details'])
        if not details_elem.get_attribute("open"):
            summary_elem = details_elem.find_element(By.TAG_NAME, "summary")
            summary_elem.click()
            time.sleep(2)
        logger.info("Semester 2 details opened")
    except Exception as e:
        logger.error(f"Failed to open semester details: {e}")
        raise


def check_grades_once():
    """Single grade check attempt with proper error handling"""
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, Config.WEBDRIVER_TIMEOUT)
        
        logger.info("Starting grade check")
        login_and_navigate(driver, wait)
        
        grades = extract_and_print_grades(driver)
        
        if grades:
            logger.info(f"Successfully extracted {len(grades)} grades")
            for course_name, grade in grades:
                logger.info(f"{course_name}: {grade}")
        else:
            logger.warning("No grades found")
        
        logger.info("Grade check completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Grade check failed: {e}")
        send_telegram_message(f"Error occurred: {str(e)[:100]}")
        return False
        
    finally:
        if driver:
            driver.quit()


def run_selenium():
    """Main loop with retry logic and delays"""
    retry_count = 0
    
    while retry_count < Config.MAX_RETRY_ATTEMPTS:
        try:
            success = check_grades_once()
            
            if success:
                retry_count = 0
                logger.info(f"Waiting {Config.CHECK_INTERVAL} seconds until next check")
                time.sleep(Config.CHECK_INTERVAL)
            else:
                retry_count += 1
                if retry_count < Config.MAX_RETRY_ATTEMPTS:
                    logger.warning(f"Retry {retry_count}/{Config.MAX_RETRY_ATTEMPTS} in {Config.RETRY_DELAY} seconds")
                    time.sleep(Config.RETRY_DELAY)
                else:
                    logger.error("Max retries reached. Stopping.")
                    send_telegram_message("Grade checker stopped after max retries. Please check logs.")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            retry_count += 1
            time.sleep(Config.RETRY_DELAY)


def start_bot():
    """Initialize and start Telegram bot with error recovery"""
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        welcome_text = (
            "University Grades Bot\n\n"
            "Commands:\n"
            "/start - Show this message\n"
            "/help - Get help\n"
            "/grades - View current grades\n"
        )
        bot.reply_to(message, welcome_text)

    @bot.message_handler(commands=['grades'])
    def send_grades(message):
        grades = get_grades()
        if not grades:
            bot.reply_to(message, "No grades available")
            return
            
        grades_text = "Current grades:\n\n"
        for course, grade in grades:
            grade_display = grade if grade else "Not available"
            grades_text += f"{course}: {grade_display}\n"
        bot.reply_to(message, grades_text)

    @bot.message_handler(func=lambda message: True)
    def provide_info(message):
        info_text = (
            "This bot tracks your university grades and sends notifications "
            "when new grades are posted. Use /help for available commands."
        )
        bot.reply_to(message, info_text)

    logger.info("Starting Telegram bot")
    
    # Polling with error recovery
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Telegram bot error: {e}")
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
        
        selenium_thread = threading.Thread(target=run_selenium, daemon=True)
        bot_thread = threading.Thread(target=start_bot, daemon=True)

        selenium_thread.start()
        bot_thread.start()

        selenium_thread.join()
        bot_thread.join()
        
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        print("\nGrade checker stopped.")
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print("\nPlease create a .env file with your credentials.")
        print("See .env.example for template.")
