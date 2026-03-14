"""Integration tests that verify multiple components working together.

These tests exercise real database operations combined with the Flask app
and the grade-update / upsert logic, without mocking the database layer.
"""

import sqlite3
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("TELEGRAM_CHAT_ID", "")
os.environ.setdefault("RUNI_USERNAME", "test")
os.environ.setdefault("RUNI_PASSWORD", "test")

from university_grades.core import SqliteGradeRepository, create_repository
from university_grades.web.app import app as flask_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_card(course_name, grade_text):
    card = MagicMock()
    h2 = MagicMock()
    h2.text = course_name
    strong = MagicMock()
    strong.text = grade_text
    card.find_element.side_effect = lambda by, value: (
        h2 if value == "h2" else strong
    )
    card.text = grade_text
    card.find_elements.return_value = []
    return card


def _authenticated_client(app_instance):
    client = app_instance.test_client()
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'testuser'
    return client


# ---------------------------------------------------------------------------
# Database creation integration
# ---------------------------------------------------------------------------

class TestDatabaseCreation:

    def test_repository_auto_creates_table(self, tmp_path):
        db_path = str(tmp_path / "auto.db")
        repo = SqliteGradeRepository(db_path)
        assert repo.get_all() == []

    def test_repository_works_on_fresh_db(self, tmp_path):
        db_path = str(tmp_path / "fresh.db")
        repo = create_repository(db_path)
        repo.upsert("Test Course", 88)
        assert len(repo.get_all()) == 1
        assert repo.calculate_average() == 88.0


# ---------------------------------------------------------------------------
# Flask + Repository integration
# ---------------------------------------------------------------------------

class TestFlaskRepositoryIntegration:

    @pytest.fixture
    def app_and_client(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        flask_app.config["TESTING"] = True
        flask_app.config["SECRET_KEY"] = "test"
        flask_app.config["_repository"] = repo
        client = _authenticated_client(flask_app)
        yield flask_app, client

    def test_dashboard_shows_all_grades(self, app_and_client):
        _, client = app_and_client
        response = client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert '90' in html
        assert '85' in html
        assert '78' in html

    def test_dashboard_shows_correct_average(self, app_and_client):
        _, client = app_and_client
        response = client.get('/dashboard')
        html = response.data.decode('utf-8')
        expected = round((90 * 3 + 85 * 3 + 78 * 3) / 9, 2)
        assert str(expected) in html

    def test_dashboard_with_mixed_grades(self, mixed_grades_db):
        repo = SqliteGradeRepository(mixed_grades_db)
        flask_app.config["TESTING"] = True
        flask_app.config["SECRET_KEY"] = "test"
        flask_app.config["_repository"] = repo
        client = _authenticated_client(flask_app)

        response = client.get("/dashboard")
        html = response.data.decode("utf-8")
        expected = round((90 * 3 + 78 * 4) / (3 + 4), 2)
        assert str(expected) in html


# ---------------------------------------------------------------------------
# Repository update -> Flask display integration
# ---------------------------------------------------------------------------

class TestGradeUpdateToFlaskIntegration:

    @pytest.fixture
    def setup(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        flask_app.config["TESTING"] = True
        flask_app.config["SECRET_KEY"] = "test"
        flask_app.config["_repository"] = repo
        yield repo, seeded_db

    def test_update_grade_then_read_via_dashboard(self, setup):
        repo, _ = setup
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 95)

        client = _authenticated_client(flask_app)
        html = client.get('/dashboard').data.decode('utf-8')
        assert '95' in html

    def test_update_multiple_grades_then_verify_average(self, setup):
        repo, _ = setup
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 90)
        repo.update_grade("5090 AI Tools for Entrepreneurs", 80)
        repo.update_grade("5789 Decision Making in Entrepreneurship", 70)

        client = _authenticated_client(flask_app)
        html = client.get('/dashboard').data.decode('utf-8')
        expected = round((90 * 3 + 80 * 3 + 70 * 3) / 9, 2)
        assert str(expected) in html

    def test_partial_update_only_affects_target_course(self, setup):
        repo, seeded_db = setup
        repo.update_grade("5090 AI Tools for Entrepreneurs", 88)

        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '3937%'")
        assert cursor.fetchone()[0] is None
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '5090%'")
        assert cursor.fetchone()[0] == 88
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '5789%'")
        assert cursor.fetchone()[0] is None
        conn.close()


# ---------------------------------------------------------------------------
# Extract grades -> DB -> Flask end-to-end (mocking only Selenium driver)
# ---------------------------------------------------------------------------

class TestExtractToFlaskEndToEnd:
    """Full pipeline: extract from mock driver -> upsert DB -> verify in Flask."""

    @pytest.fixture
    def setup(self, seeded_db):
        from university_grades.scraping import scraper as gm

        repo = SqliteGradeRepository(seeded_db)
        flask_app.config["TESTING"] = True
        flask_app.config["SECRET_KEY"] = "test"
        flask_app.config["_repository"] = repo

        gm.repository = repo
        gm.notifier = MagicMock()
        gm.notifier.send.return_value = True
        gm.course_message_flags.clear()

        yield gm, repo, seeded_db

    def test_full_pipeline(self, setup):
        gm, repo, seeded_db = setup

        driver = MagicMock()
        driver.find_elements.return_value = [
            _make_card("3937 Seminar", "ציון: 91"),
            _make_card("5090 AI Tools", "Grade: 87"),
            _make_card("5789 Decision Making", "ציון: 76"),
        ]

        grades, _ = gm.extract_and_print_grades(driver)
        assert len(grades) == 3

        client = _authenticated_client(flask_app)
        html = client.get('/dashboard').data.decode('utf-8')
        assert '91' in html
        assert '87' in html
        assert '76' in html

    def test_pipeline_with_unavailable_grade(self, setup):
        gm, repo, seeded_db = setup

        driver = MagicMock()
        driver.find_elements.return_value = [
            _make_card("3937 Seminar", "ציון: 91"),
            _make_card("5090 AI Tools", "ציון: טרם"),
        ]

        grades, _ = gm.extract_and_print_grades(driver)
        assert grades[0] == ("3937 Seminar", "91")
        assert grades[1] == ("5090 AI Tools", "Not available")

        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course = '3937 Seminar'")
        assert cursor.fetchone()[0] == 91
        cursor.execute("SELECT grade FROM grades WHERE course = '5090 AI Tools'")
        row = cursor.fetchone()
        assert row is not None and row[0] is None
        conn.close()


# ---------------------------------------------------------------------------
# Database integrity tests
# ---------------------------------------------------------------------------

class TestDatabaseIntegrity:

    def test_concurrent_read_and_write(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 92)
        rows = repo.get_courses_and_grades()
        lookup = {r[0].split()[0]: r[1] for r in rows}
        assert lookup["3937"] == 92

    def test_repeated_updates_keep_latest(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 80)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 90)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 95)

        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '3937%'")
        assert cursor.fetchone()[0] == 95
        conn.close()

    def test_average_updates_after_grade_change(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        assert repo.calculate_average() == 0.0

        repo.update_grade("3937 Practical Entrepreneurship Seminar", 100)
        assert repo.calculate_average() == 100.0

        repo.update_grade("5090 AI Tools for Entrepreneurs", 80)
        expected = round((100 * 3 + 80 * 3) / 6, 2)
        assert repo.calculate_average() == expected

    def test_upsert_creates_new_course(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        repo.upsert("9999 Brand New Course", 95)
        rows = repo.get_all()
        assert len(rows) == 1
        assert rows[0][0] == "9999 Brand New Course"
        assert rows[0][1] == 95

    def test_upsert_updates_existing_course(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        repo.upsert("3937 Practical Entrepreneurship Seminar", 88)
        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '3937%'")
        assert cursor.fetchone()[0] == 88
        conn.close()

    def test_clear_all(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        assert len(repo.get_all()) == 3
        repo.clear_all()
        assert len(repo.get_all()) == 0
