"""
Scraping layer - Selenium-based grade extraction from university portal.
"""

from .scraper import (
    extract_and_print_grades,
    login_and_navigate,
    check_grades_once,
    run_selenium,
    start_bot,
    run_web_scraper,
)

__all__ = [
    "extract_and_print_grades",
    "login_and_navigate",
    "check_grades_once",
    "run_selenium",
    "start_bot",
    "run_web_scraper",
]
