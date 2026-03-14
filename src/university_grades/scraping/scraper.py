"""
Selenium-based grade scraper for Reichman University portal.
"""

import re
import threading
import logging
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from university_grades.core import (
    Config,
    create_repository,
    create_notifier,
    TelegramNotifier,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("grade_checker.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

notifier = create_notifier(Config)
repository = create_repository(Config.DATABASE_PATH)
course_message_flags = {}

# Sentinel for pass/fail grades (e.g. "עבר") - excluded from average, displayed as "עבר"
GRADE_PASSED = -1


def _extract_grade_from_card(card):
    """Extract grade from a single card. Returns grade_int or None or GRADE_PASSED.
    When the card has multiple grade values (e.g. sub-assessments), returns the highest.
    """
    found_עבר = False
    numeric_grades = []

    try:
        grade_text = card.find_element(By.TAG_NAME, "strong").text.strip()
        if "ציון:" in grade_text or "Grade:" in grade_text:
            raw = (
                grade_text.replace("ציון:", "")
                .replace("Grade:", "")
                .strip()
            )
            if raw.isdigit():
                numeric_grades.append(int(raw))
            elif isinstance(raw, str) and ("עבר" in raw or raw.strip() == "עבר"):
                found_עבר = True
    except Exception:
        pass

    try:
        in_range_divs = card.find_elements(By.CLASS_NAME, "InRange")
        for div in in_range_divs:
            text = div.text.strip()
            if text.isdigit():
                numeric_grades.append(int(text))
            elif isinstance(text, str) and ("עבר" in text or text.strip() == "עבר"):
                found_עבר = True
    except Exception:
        pass

    try:
        all_text = card.text
        if isinstance(all_text, str):
            if "עבר" in all_text:
                found_עבר = True
            else:
                numbers = re.findall(r"\b(\d{2,3})\b", all_text)
                for n in numbers:
                    val = int(n)
                    if 0 <= val <= 100:
                        numeric_grades.append(val)
    except Exception:
        pass

    if numeric_grades:
        return max(numeric_grades)
    if found_עבר:
        return GRADE_PASSED
    return None


def extract_and_print_grades(driver, repo=None, notif=None):
    """Extract grades from page and upsert into database.
    When a course has multiple grade entries, keeps the highest numeric grade.
    """
    repo = repo or repository
    notif = notif or notifier

    # Collect all (course_code, course_name, grade) from every card
    course_grades = {}  # course_code -> (course_name, best_grade)

    try:
        course_cards = driver.find_elements(By.CLASS_NAME, "Box_ph")
        logger.info(f"Found {len(course_cards)} course cards")

        for card_index, card in enumerate(course_cards):
            try:
                course_name = card.find_element(By.TAG_NAME, "h2").text.strip()
                if not course_name:
                    continue

                course_code = (
                    course_name.split()[0] if course_name.split() else course_name
                )
                grade_int = _extract_grade_from_card(card)

                # Keep the highest grade per course
                if course_code not in course_grades:
                    course_grades[course_code] = (course_name, grade_int)
                else:
                    prev_name, prev_grade = course_grades[course_code]
                    # Take max: numeric > "עבר" > None
                    if grade_int is None:
                        pass  # keep previous
                    elif grade_int == GRADE_PASSED:
                        if prev_grade is None:
                            course_grades[course_code] = (course_name, grade_int)
                        # else keep prev (numeric beats עבר for "highest")
                    elif prev_grade is None or prev_grade == GRADE_PASSED:
                        course_grades[course_code] = (course_name, grade_int)
                    else:
                        course_grades[course_code] = (
                            course_name,
                            max(prev_grade, grade_int),
                        )

            except Exception as e:
                logger.warning(f"Could not extract grade from card {card_index}: {e}")

        # Upsert best grade per course
        grades_found = []
        new_grades_count = 0

        for course_code, (course_name, grade_int) in course_grades.items():
            repo.upsert(course_name, grade_int)

            if grade_int is not None and grade_int != GRADE_PASSED:
                if course_code not in course_message_flags:
                    course_message_flags[course_code] = False
                if not course_message_flags[course_code]:
                    if notif.send(f"New grade for {course_name}: {grade_int}"):
                        course_message_flags[course_code] = True
                        new_grades_count += 1

            if grade_int == GRADE_PASSED:
                grades_found.append((course_name, "עבר"))
            elif grade_int is not None:
                grades_found.append((course_name, str(grade_int)))
            else:
                grades_found.append((course_name, "Not available"))

    except Exception as e:
        logger.error(f"Failed to extract grades: {e}")
        grades_found = []
        new_grades_count = 0

    return grades_found, new_grades_count


def login_and_navigate(
    driver, wait, year=None, semester=None, username=None, password=None
):
    """Handle login and navigation to grades page."""
    year = year or Config.DEFAULT_YEAR
    semester = semester or Config.DEFAULT_SEMESTER
    username = username or Config.RUNI_USERNAME
    password = password or Config.RUNI_PASSWORD
    year_xpath = f"//div[@data-value='{year}' and contains(@class, 'option')]"
    semester_xpath = (
        f"//div[@data-value='{semester}' and contains(@class, 'option')]"
    )
    semester_details_xpath = f"//details[@id='de_{semester}']"

    driver.get("https://my.runi.ac.il/my.policy")
    time.sleep(3)

    if "logout" in driver.current_url or "errorcode" in driver.current_url:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            if link.get_attribute("href") == "https://my.runi.ac.il/":
                link.click()
                time.sleep(3)
                break

    wait.until(
        EC.element_to_be_clickable((By.XPATH, Config.XPATHS["login_button"]))
    )
    driver.find_element(By.XPATH, Config.XPATHS["login_button"]).click()
    time.sleep(1)

    driver.find_element(By.ID, Config.XPATHS["username_field"]).send_keys(
        username
    )
    driver.find_element(By.ID, Config.XPATHS["password_field"]).send_keys(
        password
    )
    driver.find_element(By.XPATH, Config.XPATHS["submit_button"]).click()
    time.sleep(10)

    # Dismiss system message modal if present (הודעות מערכת - "מאשר/ת" button)
    try:
        from selenium.webdriver.support.ui import WebDriverWait
        modal_wait = WebDriverWait(driver, 5)
        modal_btn = modal_wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@class, 'close_modal_btn') and contains(text(), 'מאשר')]")
            )
        )
        modal_btn.click()
        time.sleep(2)
        logger.info("Dismissed system message modal")
    except Exception:
        pass  # Modal may not appear

    windows_before = driver.window_handles
    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, Config.XPATHS["student_info_station"])
        )
    )
    info_station = driver.find_element(
        By.XPATH, Config.XPATHS["student_info_station"]
    )
    info_station.find_element(By.XPATH, "./..").click()
    time.sleep(5)

    windows_after = driver.window_handles
    if len(windows_after) > len(windows_before):
        new_window = [w for w in windows_after if w not in windows_before][0]
        driver.switch_to.window(new_window)
        time.sleep(2)

    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        driver.switch_to.frame(iframes[0])
        time.sleep(1)

    time.sleep(3)
    grades_tab = wait.until(
        EC.element_to_be_clickable((By.XPATH, Config.XPATHS["grades_tab"]))
    )
    grades_tab.click()
    time.sleep(2)

    wait.until(
        EC.element_to_be_clickable((By.XPATH, Config.XPATHS["grades_list"]))
    )
    driver.find_element(By.XPATH, Config.XPATHS["grades_list"]).click()
    time.sleep(3)

    year_control = wait.until(
        EC.element_to_be_clickable((By.XPATH, Config.XPATHS["year_control"]))
    )
    year_control.click()
    time.sleep(1)
    wait.until(
        EC.element_to_be_clickable((By.XPATH, year_xpath))
    ).click()
    time.sleep(1)

    semester_control = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, Config.XPATHS["semester_control"])
        )
    )
    semester_control.click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, semester_xpath))).click()
    time.sleep(1)

    submit_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, Config.XPATHS["submit_button_grades"])
        )
    )
    submit_btn.click()
    time.sleep(5)

    try:
        details_elem = driver.find_element(By.XPATH, semester_details_xpath)
        if not details_elem.get_attribute("open"):
            details_elem.find_element(By.TAG_NAME, "summary").click()
            time.sleep(2)
    except Exception:
        pass


def run_web_scraper(
    username,
    password,
    year,
    semester,
    repository,
    status_dict,
    telegram_token=None,
    telegram_chat_id=None,
):
    """
    Run a single scrape from the web app (background thread).
    Uses dynamic credentials. Updates status_dict with progress.
    """
    from university_grades.core import create_notifier

    status_dict["running"] = True
    status_dict["last_result"] = None
    status_dict["message"] = "Initializing..."
    notifier = create_notifier(token=telegram_token, chat_id=telegram_chat_id)

    driver = None
    try:
        from selenium.webdriver.support import expected_conditions as EC

        status_dict["message"] = "Connecting to university portal..."
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, Config.WEBDRIVER_TIMEOUT)

        status_dict["message"] = "Logging in..."
        login_and_navigate(
            driver, wait,
            year=year, semester=semester,
            username=username, password=password,
        )

        status_dict["message"] = "Extracting grades..."
        repository.clear_all()
        grades, new_grades_count = extract_and_print_grades(
            driver, repo=repository, notif=notifier
        )

        seen = len(grades)
        graded = sum(1 for _, g in grades if g != "Not available")

        status_dict["last_result"] = "success"
        if new_grades_count > 0:
            status_dict["message"] = (
                f"Done — {new_grades_count} new grade(s) published. "
                f"Found {seen} course(s), {graded} graded."
            )
        else:
            status_dict["message"] = (
                f"Check complete — no new grade was published. "
                f"Found {seen} course(s), {graded} graded."
            )
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        status_dict["last_result"] = "error"
        status_dict["message"] = f"Scraping failed: {str(e)[:120]}"
    finally:
        if driver:
            driver.quit()
        status_dict["running"] = False


def check_grades_once(year=None, semester=None, repo=None, notif=None):
    """Single grade check attempt."""
    repo = repo or repository
    notif = notif or notifier
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, Config.WEBDRIVER_TIMEOUT)

        repo.clear_all()
        login_and_navigate(driver, wait, year=year, semester=semester)
        grades, _ = extract_and_print_grades(driver, repo=repo, notif=notif)

        if grades:
            logger.info(f"Successfully extracted {len(grades)} grades")
        else:
            logger.warning("No grades found")

        return True
    except Exception as e:
        logger.error(f"Grade check failed: {e}")
        notif.send(f"Error occurred: {str(e)[:100]}")
        return False
    finally:
        if driver:
            driver.quit()


def run_selenium(year=None, semester=None, repo=None, notif=None):
    """Main loop with retry logic."""
    repo = repo or repository
    notif = notif or notifier
    retry_count = 0

    while retry_count < Config.MAX_RETRY_ATTEMPTS:
        try:
            success = check_grades_once(
                year=year,
                semester=semester,
                repo=repo,
                notif=notif,
            )
            if success:
                retry_count = 0
                time.sleep(Config.CHECK_INTERVAL)
            else:
                retry_count += 1
                if retry_count < Config.MAX_RETRY_ATTEMPTS:
                    time.sleep(Config.RETRY_DELAY)
                else:
                    notif.send(
                        "Grade checker stopped after max retries. Please check logs."
                    )
                    break
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            retry_count += 1
            time.sleep(Config.RETRY_DELAY)


def start_bot(repo=None):
    """Start Telegram bot (only when Telegram is configured)."""
    if not isinstance(notifier, TelegramNotifier):
        logger.info("Telegram not configured — bot thread disabled.")
        return

    repo = repo or repository
    bot = notifier.bot

    @bot.message_handler(commands=["start", "help"])
    def send_welcome(message):
        bot.reply_to(
            message,
            "University Grades Bot\n\n"
            "Commands:\n/start - Show this\n/help - Help\n/grades - View grades",
        )

    @bot.message_handler(commands=["grades"])
    def send_grades(message):
        grades = repo.get_courses_and_grades()
        if not grades:
            bot.reply_to(message, "No grades available")
            return
        text = "Current grades:\n\n"
        for course, grade in grades:
            display = "עבר" if grade == -1 else (grade or "Not available")
            text += f"{course}: {display}\n"
        bot.reply_to(message, text)

    @bot.message_handler(func=lambda m: True)
    def provide_info(message):
        bot.reply_to(
            message,
            "This bot tracks university grades. Use /help for commands.",
        )

    try:
        bot.get_me()
    except Exception as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        return

    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Telegram bot error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    try:
        Config.validate()
        year = Config.DEFAULT_YEAR
        semester = Config.DEFAULT_SEMESTER

        selenium_thread = threading.Thread(
            target=run_selenium,
            kwargs={"year": year, "semester": semester},
            daemon=True,
        )
        bot_thread = threading.Thread(target=start_bot, daemon=True)

        selenium_thread.start()
        bot_thread.start()
        selenium_thread.join()
        bot_thread.join()
    except KeyboardInterrupt:
        print("\nGrade checker stopped.")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
