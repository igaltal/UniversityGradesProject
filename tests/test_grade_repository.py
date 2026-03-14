"""Unit tests for GradeRepository (grade_repository.py)."""

import sqlite3
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from university_grades.core import SqliteGradeRepository, create_repository


class TestSqliteGradeRepositoryGetAll:

    def test_returns_all_courses(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        assert len(repo.get_all()) == 3

    def test_returns_course_grade_points_tuples(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        for course, grade, points in repo.get_all():
            assert isinstance(course, str)
            assert isinstance(grade, int)

    def test_empty_database(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        assert repo.get_all() == []

    def test_returns_none_grades(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        assert all(row[1] is None for row in repo.get_all())

    def test_auto_creates_table(self, tmp_path):
        db_path = str(tmp_path / "brand_new.db")
        repo = SqliteGradeRepository(db_path)
        assert repo.get_all() == []


class TestSqliteGradeRepositoryGetCoursesAndGrades:

    def test_returns_two_element_tuples(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        rows = repo.get_courses_and_grades()
        assert len(rows) == 3
        for row in rows:
            assert len(row) == 2

    def test_empty_db(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        assert repo.get_courses_and_grades() == []


class TestSqliteGradeRepositoryUpdateGrade:

    def test_updates_existing_course(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        assert repo.update_grade("3937 Practical Entrepreneurship Seminar", 92) is True

        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '3937%'")
        assert cursor.fetchone()[0] == 92
        conn.close()

    def test_does_not_affect_other_courses(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 92)

        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '5090%'")
        assert cursor.fetchone()[0] is None
        conn.close()

    def test_nonexistent_course_returns_false(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        assert repo.update_grade("9999 Nonexistent Course", 100) is False

    def test_overwrite_existing_grade(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 99)

        conn = sqlite3.connect(graded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '3937%'")
        assert cursor.fetchone()[0] == 99
        conn.close()

    def test_repeated_updates_keep_latest(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 80)
        repo.update_grade("3937 Practical Entrepreneurship Seminar", 95)

        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '3937%'")
        assert cursor.fetchone()[0] == 95
        conn.close()


class TestSqliteGradeRepositoryUpsert:

    def test_inserts_new_course(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        assert repo.upsert("9999 New Course", 88) is True
        rows = repo.get_all()
        assert len(rows) == 1
        assert rows[0][0] == "9999 New Course"
        assert rows[0][1] == 88

    def test_updates_existing_course(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        repo.upsert("3937 Practical Entrepreneurship Seminar", 95)

        conn = sqlite3.connect(seeded_db)
        cursor = conn.cursor()
        cursor.execute("SELECT grade FROM grades WHERE course LIKE '3937%'")
        assert cursor.fetchone()[0] == 95
        conn.close()

    def test_upsert_with_none_grade(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        repo.upsert("1234 Pending Course", None)
        rows = repo.get_all()
        assert rows[0][1] is None

    def test_default_points(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        repo.upsert("1234 Course", 80)
        rows = repo.get_all()
        assert rows[0][2] == 3.0


class TestSqliteGradeRepositoryClearAll:

    def test_clears_all_rows(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        assert len(repo.get_all()) == 3
        repo.clear_all()
        assert len(repo.get_all()) == 0

    def test_clear_empty_db_no_error(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        repo.clear_all()
        assert repo.get_all() == []


class TestSqliteGradeRepositoryCalculateAverage:

    def test_basic_equal_weights(self, graded_db):
        repo = SqliteGradeRepository(graded_db)
        expected = round((90 * 3 + 85 * 3 + 78 * 3) / 9, 2)
        assert repo.calculate_average() == expected

    def test_weighted_average(self, mixed_grades_db):
        repo = SqliteGradeRepository(mixed_grades_db)
        expected = round((90 * 3 + 78 * 4) / (3 + 4), 2)
        assert repo.calculate_average() == expected

    def test_all_none_grades(self, seeded_db):
        repo = SqliteGradeRepository(seeded_db)
        assert repo.calculate_average() == 0.0

    def test_empty_database(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        assert repo.calculate_average() == 0.0

    def test_single_course(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        repo.upsert("Test Course", 95)
        assert repo.calculate_average() == 95.0

    def test_average_excludes_passed_pass(self, temp_db):
        """עבר (grade -1) is excluded from average calculation."""
        repo = SqliteGradeRepository(temp_db)
        repo.upsert("Course A", 90)
        repo.upsert("Course B", -1)  # pass
        assert repo.calculate_average() == 90.0


class TestCreateRepository:

    def test_factory_returns_sqlite_repo(self, tmp_path):
        repo = create_repository(str(tmp_path / "f.db"))
        assert isinstance(repo, SqliteGradeRepository)

    def test_factory_repo_is_functional(self, graded_db):
        repo = create_repository(graded_db)
        assert len(repo.get_all()) == 3
