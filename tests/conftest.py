import sys
import os
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Pre-mock packages that may not be installed in test env
for _mod in [
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.support",
    "selenium.webdriver.support.expected_conditions",
    "selenium.webdriver.support.ui",
    "selenium.webdriver.common",
    "selenium.webdriver.common.by",
    "selenium.webdriver.common.keys",
    "telebot",
    "dotenv",
]:
    sys.modules.setdefault(_mod, MagicMock())


def _create_grades_table(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS grades (
            course TEXT PRIMARY KEY,
            grade  INTEGER,
            points REAL DEFAULT 3.0
        )
    """
    )
    conn.commit()
    conn.close()


@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_grades.db")
    _create_grades_table(db_path)
    return db_path


@pytest.fixture
def seeded_db(temp_db):
    conn = sqlite3.connect(temp_db)
    conn.executemany(
        "INSERT INTO grades (course, grade, points) VALUES (?, ?, ?)",
        [
            ("3937 Practical Entrepreneurship Seminar", None, 3),
            ("5090 AI Tools for Entrepreneurs", None, 3),
            ("5789 Decision Making in Entrepreneurship", None, 3),
        ],
    )
    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def graded_db(temp_db):
    conn = sqlite3.connect(temp_db)
    conn.executemany(
        "INSERT INTO grades (course, grade, points) VALUES (?, ?, ?)",
        [
            ("3937 Practical Entrepreneurship Seminar", 90, 3),
            ("5090 AI Tools for Entrepreneurs", 85, 3),
            ("5789 Decision Making in Entrepreneurship", 78, 3),
        ],
    )
    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def mixed_grades_db(temp_db):
    conn = sqlite3.connect(temp_db)
    conn.executemany(
        "INSERT INTO grades (course, grade, points) VALUES (?, ?, ?)",
        [
            ("3937 Practical Entrepreneurship Seminar", 90, 3),
            ("5090 AI Tools for Entrepreneurs", None, 3),
            ("5789 Decision Making in Entrepreneurship", 78, 4),
        ],
    )
    conn.commit()
    conn.close()
    return temp_db
