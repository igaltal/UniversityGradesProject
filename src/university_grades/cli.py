"""
CLI entry points.
"""

import logging
import threading
from pathlib import Path

from university_grades.core import Config
from university_grades.scraping import run_selenium, start_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("grade_checker.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry: run scraper + Telegram bot (standalone mode)."""
    try:
        Config.validate()
        logger.info("=" * 60)
        logger.info("University Grades Checker - Starting")
        logger.info("=" * 60)
        logger.info(f"Database path: {Config.DATABASE_PATH}")
        logger.info(f"Year: {Config.DEFAULT_YEAR}, Semester: {Config.DEFAULT_SEMESTER}")

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
        logger.info("Stopped by user")
        print("\nGrade checker stopped.")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print("\nPlease create a .env file with your credentials.")
        print("See .env.example for template.")


def run_web():
    """Run the Flask web application."""
    from university_grades.web.app import app

    BASE_DIR = Path(__file__).parent.parent.parent
    db_path = BASE_DIR / "database" / "grades.db"
    print(f"Using database: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    app.run(debug=True, port=5001)
