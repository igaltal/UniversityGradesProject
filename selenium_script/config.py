"""
Configuration Management for University Grades Project
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try loading from parent directory
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)


class Config:
    """Configuration class that loads all settings from environment variables"""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Runi Credentials
    RUNI_USERNAME = os.getenv('RUNI_USERNAME')
    RUNI_PASSWORD = os.getenv('RUNI_PASSWORD')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', '../database/grades.db')
    
    # Selenium Configuration
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '30'))
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))
    WEBDRIVER_TIMEOUT = int(os.getenv('WEBDRIVER_TIMEOUT', '20'))
    
    # XPath Selectors - Centralized for easy maintenance
    XPATHS = {
        'login_button': "//button[@type='submit' or contains(@class, 'submit')]",
        'username_field': "input_1",
        'password_field': "input_2",
        'submit_button': "//button[@type='submit']",
        'student_info_station': "//img[@alt='תחנת מידע לסטודנט']",
        'grades_tab': "//button[@onclick=\"OpenMenuItem(1);\"]",
        'grades_list': "//button[contains(@class, 'menu-link')]//span[contains(text(), 'רשימת ציונים')]",
        'year_control': "//div[contains(@class, 'ts-control') and .//input[@id='R1C1-ts-control']]",
        'year_2025': "//div[@data-value='2025' and contains(@class, 'option')]",
        'semester_control': "//div[contains(@class, 'ts-control') and .//input[@id='R1C2-ts-control']]",
        'semester_2': "//div[@data-value='2' and contains(@class, 'option')]",
        'submit_button_grades': "//button[contains(text(), 'ביצוע')]",
        'semester_2_details': "//details[@id='de_2']",
    }
    
    # Course codes for 2025
    COURSE_CODES = {
        "3937": "Practical Entrepreneurship Seminar - Acceleration",
        "5090": "AI Tools for Entrepreneurs", 
        "5789": "Decision Making in Entrepreneurship",
    }
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration values are present
        Raises ValueError if any required config is missing
        """
        required_configs = [
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
            ('TELEGRAM_CHAT_ID', cls.TELEGRAM_CHAT_ID),
            ('RUNI_USERNAME', cls.RUNI_USERNAME),
            ('RUNI_PASSWORD', cls.RUNI_PASSWORD),
        ]
        
        missing_configs = [name for name, value in required_configs if not value]
        
        if missing_configs:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_configs)}. "
                f"Please create a .env file based on .env.example"
            )
    
    @classmethod
    def get_course_name(cls, course_code):
        """Get the course name for a course code"""
        return cls.COURSE_CODES.get(course_code, course_code)


# Validate configuration on module import
try:
    Config.validate()
except ValueError as e:
    print(f"⚠️  Configuration Error: {e}")
    print("Please create a .env file with your credentials based on .env.example")
