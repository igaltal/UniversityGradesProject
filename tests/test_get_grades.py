"""Unit tests for the Selenium scraper module (get_grades.py).

selenium, telebot, and dotenv are not installed in the test environment.
conftest.py pre-mocks them so we can safely import get_grades.
"""

import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("TELEGRAM_CHAT_ID", "")
os.environ.setdefault("RUNI_USERNAME", "test")
os.environ.setdefault("RUNI_PASSWORD", "test")

from university_grades.core import LogNotifier, SqliteGradeRepository
from university_grades.scraping import scraper as gm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_card(course_name, grade_text):
    """Build a mock Selenium WebElement that looks like a course card."""
    card = MagicMock()
    h2 = MagicMock()
    h2.text = course_name
    strong = MagicMock()
    strong.text = grade_text
    card.find_element.side_effect = lambda by, value: (
        h2 if value == "h2" else strong
    )
    # card.text used by fallback extraction (all_text path)
    card.text = grade_text
    card.find_elements.return_value = []  # InRange divs - empty when no numeric grade
    return card


def _make_driver(cards):
    driver = MagicMock()
    driver.find_elements.return_value = cards
    return driver


# ---------------------------------------------------------------------------
# Tests for extract_and_print_grades()
# ---------------------------------------------------------------------------

class TestExtractAndPrintGrades:

    @pytest.fixture(autouse=True)
    def _setup(self, seeded_db):
        """Wire the module-level repository and notifier to a temp DB."""
        self.db_path = seeded_db
        self.repo = SqliteGradeRepository(seeded_db)
        self.mock_notifier = MagicMock()
        self.mock_notifier.send.return_value = True

        gm.repository = self.repo
        gm.notifier = self.mock_notifier
        gm.course_message_flags.clear()

    def test_extracts_grade_with_hebrew_prefix(self):
        driver = _make_driver([_make_card("3937 Seminar", "ציון: 90")])
        grades, _ = gm.extract_and_print_grades(driver)
        assert len(grades) == 1
        assert grades[0] == ("3937 Seminar", "90")

    def test_extracts_grade_with_english_prefix(self):
        driver = _make_driver([_make_card("5090 AI Tools", "Grade: 85")])
        grades, _ = gm.extract_and_print_grades(driver)
        assert len(grades) == 1
        assert grades[0] == ("5090 AI Tools", "85")

    def test_grade_not_yet_available(self):
        driver = _make_driver([_make_card("3937 Seminar", "ציון: טרם")])
        grades, _ = gm.extract_and_print_grades(driver)
        assert grades[0] == ("3937 Seminar", "Not available")

    def test_grade_passed_pass(self):
        driver = _make_driver([_make_card("1234 Accounting", "ציון: עבר")])
        grades, _ = gm.extract_and_print_grades(driver)
        assert grades[0] == ("1234 Accounting", "עבר")

    def test_skips_empty_course_name(self):
        driver = _make_driver([_make_card("", "ציון: 90")])
        grades, _ = gm.extract_and_print_grades(driver)
        assert grades == []

    def test_deduplicates_same_course_code_takes_highest(self):
        """When same course appears in multiple cards, keep the highest grade."""
        driver = _make_driver([
            _make_card("3937 Seminar A", "ציון: 85"),
            _make_card("3937 Seminar B", "ציון: 90"),
        ])
        grades, _ = gm.extract_and_print_grades(driver)
        assert len(grades) == 1
        assert grades[0][1] == "90"

    def test_multiple_distinct_courses(self):
        driver = _make_driver([
            _make_card("3937 Seminar", "ציון: 90"),
            _make_card("5090 AI Tools", "Grade: 85"),
            _make_card("5789 Decision Making", "ציון: 78"),
        ])
        grades, _ = gm.extract_and_print_grades(driver)
        assert len(grades) == 3

    def test_no_course_cards(self):
        driver = _make_driver([])
        grades, _ = gm.extract_and_print_grades(driver)
        assert grades == []

    def test_already_notified_course_not_sent_again(self):
        gm.course_message_flags["3937"] = True
        driver = _make_driver([_make_card("3937 Seminar", "ציון: 90")])
        gm.extract_and_print_grades(driver)
        self.mock_notifier.send.assert_not_called()

    def test_upserts_grade_into_database(self):
        driver = _make_driver([_make_card("3937 Seminar", "ציון: 91")])
        gm.extract_and_print_grades(driver)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course = '3937 Seminar'")
        row = cursor.fetchone()
        conn.close()
        assert row is not None and row[0] == 91

    def test_sends_notification_for_new_grade(self):
        driver = _make_driver([_make_card("3937 Seminar", "ציון: 90")])
        gm.extract_and_print_grades(driver)
        self.mock_notifier.send.assert_called_once()
        assert "3937 Seminar" in self.mock_notifier.send.call_args[0][0]

    def test_upserts_new_course_not_in_db(self):
        """A course scraped from the site that wasn't in the DB gets inserted."""
        driver = _make_driver([_make_card("9999 New Course", "ציון: 100")])
        gm.extract_and_print_grades(driver)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course = '9999 New Course'")
        row = cursor.fetchone()
        conn.close()
        assert row is not None and row[0] == 100
