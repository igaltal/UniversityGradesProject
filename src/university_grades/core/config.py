"""
Configuration Management for University Grades Project.
"""

import os
from pathlib import Path

# Skip dotenv if DOTENV_SKIP=1 (e.g. when .env is on slow iCloud sync)
if not os.getenv("DOTENV_SKIP"):
    try:
        from dotenv import load_dotenv
        _env_path = Path(__file__).parent.parent.parent.parent / ".env"
        if _env_path.exists():
            load_dotenv(_env_path)
        else:
            load_dotenv()
    except Exception:
        pass  # Continue without .env


class Config:
    """Configuration class that loads all settings from environment variables."""

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # Runi Credentials
    RUNI_USERNAME = os.getenv("RUNI_USERNAME")
    RUNI_PASSWORD = os.getenv("RUNI_PASSWORD")

    # Database
    BASE_DIR = Path(__file__).parent.parent.parent.parent
    _default_db = str(BASE_DIR / "database" / "grades.db")
    _db_from_env = os.getenv("DATABASE_PATH")
    if _db_from_env:
        _p = Path(_db_from_env)
        if _p.is_absolute():
            DATABASE_PATH = _db_from_env
        else:
            # Resolve relative paths from project root (strip leading ../ that escapes)
            norm = _db_from_env
            while norm.startswith("../") or norm.startswith("..\\"):
                norm = norm[3:]
            DATABASE_PATH = str((BASE_DIR / norm).resolve())
    else:
        DATABASE_PATH = _default_db

    # Web app: seconds between periodic grade checks (when logged in)
    GRADE_CHECK_INTERVAL = int(os.getenv("GRADE_CHECK_INTERVAL", "60"))

    # Selenium
    MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "30"))
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
    WEBDRIVER_TIMEOUT = int(os.getenv("WEBDRIVER_TIMEOUT", "20"))
    DEFAULT_YEAR = os.getenv("DEFAULT_YEAR", "2025")
    DEFAULT_SEMESTER = os.getenv("DEFAULT_SEMESTER", "2")

    # XPath Selectors
    XPATHS = {
        "login_button": "//button[@type='submit' or contains(@class, 'submit')]",
        "username_field": "input_1",
        "password_field": "input_2",
        "submit_button": "//button[@type='submit']",
        "student_info_station": "//img[@alt='תחנת מידע לסטודנט']",
        "grades_tab": "//button[@onclick=\"OpenMenuItem(1);\"]",
        "grades_list": "//button[contains(@class, 'menu-link')]//span[contains(text(), 'רשימת ציונים')]",
        "year_control": "//div[contains(@class, 'ts-control') and .//input[@id='R1C1-ts-control']]",
        "semester_control": "//div[contains(@class, 'ts-control') and .//input[@id='R1C2-ts-control']]",
        "submit_button_grades": "//button[contains(text(), 'ביצוע')]",
    }

    @classmethod
    def validate(cls):
        required = [
            ("RUNI_USERNAME", cls.RUNI_USERNAME),
            ("RUNI_PASSWORD", cls.RUNI_PASSWORD),
        ]
        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please create a .env file based on .env.example"
            )


try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Warning: {e}")
    print("CLI standalone mode requires RUNI_USERNAME and RUNI_PASSWORD in .env")
