import threading
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import telebot
import datetime
import sqlite3

# Telegram Bot Token
bot = telebot.TeleBot("7342533299:AAEqNG6pJFdW4nfS4I9moXJSR83wmuJEfV8")
chat_id = "7342533299" 

# Runi credentials
username = "igaltal.merom"
password = "*****"

# Message flags for grades by course
course_message_flags = {
    "logic": False,
    "operatingSystems": False,
    "advancedEnglish": False,
    "productDesign": False,
    "productManagement": False,
    "computationalLearning": False,
    "computationalModels": False,
    "introStatistics": False,
    "accountingForEntrepreneurs": False,
    "ventureCapital": False,
}

# Function to get grades from the database
# Description: Fetches grades from the SQLite database.
def get_grades():
    conn = sqlite3.connect('../database/grades.db')
    cursor = conn.cursor()
    cursor.execute('SELECT course, grade FROM grades')
    data = cursor.fetchall()
    conn.close()
    return data

# Function to update grades in the database
# Description: Updates the grade for a specific course in the SQLite database.
def update_grade(course, grade):
    try:
        conn = sqlite3.connect('../database/grades.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE grades SET grade = ? WHERE course = ?', (grade, course))
        conn.commit()
        conn.close()
        print(f"Grade for {course} updated to {grade}.")
    except Exception as e:
        print(f"Error updating grade for {course}: {e}")

# Function to print course details
# Description: Prints the course header and grade.
def print_course(course_header, course_grade):
    print(course_header)
    print(course_grade)
    print("-------------------------------\n")

# Function to extract and print grades
# Description: Extracts grades from the Runi website using Selenium, updates the SQLite database, and prints the grades.
def extract_and_print_grades(driver):
    courses = {
        "advancedEnglish": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[5]/strong",
        "operatingSystems": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[4]/strong",
        "productDesign": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[3]/strong",
        "productManagement": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[2]/strong",
        "computationalLearning": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[1]/strong",
        "computationalModels": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[6]/strong",
        "introStatistics": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[7]/strong",
        "accountingForEntrepreneurs": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[8]/strong",
        "ventureCapital": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[9]/strong",
        "logic": "/html/body/div[2]/div/div/div/div/main/article/div[5]/div/details/div/div[8]/div/div[10]/strong",
    }

    course_headers = []
    course_grades = []
    message_flags = []

    for course_name, xpath in courses.items():
        try:
            grade_element = driver.find_element(By.XPATH, xpath)
            grade = grade_element.text
            header = "Advanced English" if course_name == "advancedEnglish" else course_name
            print_course(header, grade)

            course_headers.append(header)
            course_grades.append(grade)
            message_flags.append(course_message_flags[course_name])

            # Only update if the grade is not "Not Available"
            if "ציון" in grade and "טרם" not in grade:
                grade_value = grade.replace("ציון: ", "").strip()
                update_grade(header, grade_value)

                # Send the grade update message
                if not course_message_flags[course_name]:
                    message = f"New Grade Available for {header}: {grade_value}"
                    bot.send_message(chat_id, message)
                    course_message_flags[course_name] = True
        except Exception as e:
            print(f"Error extracting grade for {course_name}: {e}")

    return course_headers, course_grades, message_flags

# Function to run Selenium for scraping
# Description: Continuously runs Selenium to check for new grades and handle web interactions.
def run_selenium():
    while True:
        try:
            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome()

            # Open the website
            driver.get("https://my.runi.ac.il/my.policy")
            time.sleep(1)

            wait = WebDriverWait(driver, 20)
            original_window = driver.current_window_handle
            assert len(driver.window_handles) == 1

            # Navigate through the website to log in and access grades
            driver.find_element(By.XPATH, "/html/body/div[1]/div/main/div[2]/div/div/div[3]/div/div/div/div/div/div/section/div[2]/div/div/div[1]/div/div/div[4]/div/a/span").click()
            time.sleep(1)
            driver.find_element(By.ID, "input_1").send_keys(username)
            driver.find_element(By.ID, "input_2").send_keys(password)
            driver.find_element(By.XPATH, "/html/body/div[1]/div/main/div/div/div/div[3]/div/div/div/div/div/div/section/div[2]/div/form/div/div[1]/div[2]/div/div[5]/div/button").click()
            time.sleep(10)

            # Wait for the element to be clickable
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div/div/div[2]/div[2]/div[2]/div/a")))
            driver.find_element(By.XPATH, "/html/body/div[4]/div/div/div[2]/div[2]/div[2]/div/a").click()
            time.sleep(3)
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/idc-menulinks/div/div[2]/div[2]/div[1]/a")))
            driver.find_element(By.XPATH, "/html/body/div[1]/div/div/idc-menulinks/div/div[2]/div[2]/div[1]/a").click()
            time.sleep(5)
            wait.until(EC.number_of_windows_to_be(2))
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='ציונים']")))
            driver.find_element(By.XPATH, "//span[text()='ציונים']").click()
            time.sleep(1)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='רשימת ציונים']")))
            driver.find_element(By.XPATH, "//span[text()='רשימת ציונים']").click()
            time.sleep(1)

            # Wait for the element to be clickable
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='1']")))
            driver.find_element(By.XPATH, "//span[text()='1']").click()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kt_body"]/span/span/span[1]/input')))
            driver.find_element(By.XPATH, '//*[@id="kt_body"]/span/span/span[1]/input').send_keys("2")
            driver.find_element(By.XPATH, '//*[@id="kt_body"]/span/span/span[1]/input').send_keys(Keys.RETURN)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="kt_content"]/div/div[2]/div/div/div/form/div[3]/a')))
            driver.find_element(By.XPATH, '//*[@id="kt_content"]/div/div[2]/div/div/div/form/div[3]/a').click()
            time.sleep(3)

            course_headers, course_grades, message_flags = extract_and_print_grades(driver)

            for i in range(len(course_headers)):
                if (course_grades[i] != "ציון: טרם ") and (message_flags[i] == False):
                    print(f"A new Grade in {course_headers[i]} has been submitted! your grade is {course_grades[i]}")
                    # Send message
                    bot.send_message(chat_id, f"A new Grade in {course_headers[i]} has been submitted! your grade is: {course_grades[i]}")
                    message_flags[i] = True
                elif message_flags[i] == False:
                    print(f"No new grade in {course_headers[i]}\n")
                    # bot.send_message(-1001916397859, f"No new grade in {course_headers[i]}\n")

            # Add a sleep interval before refreshing
            time.sleep(15)
            driver.refresh()

        except Exception as e:
            print(f"An exception caught: {e}, starting over.")
            current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                bot.send_message(chat_id, f"An exception caught, starting over at: {current_datetime}\n")
            except telebot.apihelper.ApiTelegramException as telegram_exception:
                print(f"Telegram API Exception: {telegram_exception}")
            driver.quit()
            continue

        driver.quit()

# Function to start the Telegram bot
# Description: Initializes and starts the Telegram bot, setting up command handlers for user interactions.
def start_bot():
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        welcome_message = (
            "Welcome to the Igal Tal University Grades Bot!\n"
            "This bot is designed to help you manage and track your university grades efficiently.\n\n"
            "Commands:\n"
            "/start - Display this welcome message\n"
            "/help - Get assistance on how to use this bot\n"
            "/grades - Get a list of your courses and grades\n"
            "\nYou can also send any message to receive more information about your grades and their management."
        )
        bot.reply_to(message, welcome_message)

    @bot.message_handler(commands=['grades'])
    def send_grades(message):
        grades = get_grades()
        grades_message = "Here are your courses and grades:\n\n"
        for course, grade in grades:
            grade_display = grade if grade is not None else "Not Available"
            grades_message += f"{course}: {grade_display}\n"
        bot.reply_to(message, grades_message)

    @bot.message_handler(func=lambda message: True)
    def provide_information(message):
        info_message = (
            "Thank you for your message. Our web application is designed to provide you with real-time updates "
            "on your university grades. You can use this bot to:\n"
            "- Receive notifications when new grades are available.\n"
            "- Get summaries of your grades and their averages.\n"
            "- Manage and track your academic progress conveniently.\n\n"
            "For detailed information, please visit our web application or use the /help command."
        )
        bot.reply_to(message, info_message)

    bot.polling()

if __name__ == "__main__":
    selenium_thread = threading.Thread(target=run_selenium)
    bot_thread = threading.Thread(target=start_bot)

    selenium_thread.start()
    bot_thread.start()

    selenium_thread.join()
    bot_thread.join()
