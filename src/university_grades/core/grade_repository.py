"""
GradeRepository abstraction — Adapter + Factory pattern.
"""

from abc import ABC, abstractmethod
import sqlite3
import logging

logger = logging.getLogger(__name__)


class GradeRepository(ABC):
    """Abstract base class for grade storage."""

    @abstractmethod
    def get_all(self) -> list:
        """Return all grades as list of (course, grade, points)."""
        pass

    @abstractmethod
    def get_courses_and_grades(self) -> list:
        """Return list of (course, grade)."""
        pass

    @abstractmethod
    def update_grade(self, course: str, grade) -> bool:
        """Update grade for a course (matched by course code)."""
        pass

    @abstractmethod
    def upsert(self, course: str, grade) -> bool:
        """Insert or update a course."""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Remove all rows."""
        pass

    @abstractmethod
    def calculate_average(self) -> float:
        """Return weighted average."""
        pass


class SqliteGradeRepository(GradeRepository):
    """Concrete repository backed by SQLite."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._ensure_table()

    def _connect(self):
        return sqlite3.connect(self._db_path)

    def _ensure_table(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='grades'"
            )
            row = cursor.fetchone()

            if row is None:
                conn.execute(
                    """
                    CREATE TABLE grades (
                        course TEXT PRIMARY KEY,
                        grade  INTEGER,
                        points REAL DEFAULT 3.0
                    )
                """
                )
            elif "PRIMARY KEY" not in (row[0] or "").upper():
                logger.info("Migrating grades table to add PRIMARY KEY...")
                conn.execute("ALTER TABLE grades RENAME TO grades_old")
                conn.execute(
                    """
                    CREATE TABLE grades (
                        course TEXT PRIMARY KEY,
                        grade  INTEGER,
                        points REAL DEFAULT 3.0
                    )
                """
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO grades (course, grade, points)
                    SELECT course, grade, COALESCE(points, 3.0) FROM grades_old
                """
                )
                conn.execute("DROP TABLE grades_old")
                logger.info("Migration complete.")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Could not ensure grades table: {e}")

    def get_all(self) -> list:
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT course, grade, points FROM grades")
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            logger.error(f"Database read error: {e}")
            return []

    def get_courses_and_grades(self) -> list:
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT course, grade FROM grades")
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            logger.error(f"Database read error: {e}")
            return []

    def update_grade(self, course: str, grade) -> bool:
        try:
            course_code = course.split()[0] if course.split() else course
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE grades SET grade = ? WHERE course LIKE ?",
                (grade, f"{course_code}%"),
            )
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            if rows_affected > 0:
                logger.info(f"Updated course {course_code} to grade {grade}")
                return True
            logger.warning(f"No course found with code {course_code}")
            return False
        except Exception as e:
            logger.error(f"Database update error for {course}: {e}")
            return False

    def upsert(self, course: str, grade) -> bool:
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO grades (course, grade, points)
                VALUES (?, ?, 3.0)
                ON CONFLICT(course) DO UPDATE SET grade = excluded.grade
                """,
                (course, grade),
            )
            conn.commit()
            conn.close()
            logger.info(f"Upserted {course} → {grade}")
            return True
        except Exception as e:
            logger.error(f"Upsert error for {course}: {e}")
            return False

    def clear_all(self) -> None:
        try:
            conn = self._connect()
            conn.execute("DELETE FROM grades")
            conn.commit()
            conn.close()
            logger.info("Cleared all grades from database")
        except Exception as e:
            logger.error(f"Clear error: {e}")

    def calculate_average(self) -> float:
        grades = self.get_all()
        # Only include numeric grades (0-100); exclude None and "עבר" (stored as -1)
        numeric_grades = [
            row for row in grades
            if row[1] is not None and isinstance(row[1], (int, float))
            and 0 <= row[1] <= 100
        ]
        total_points = sum(row[2] for row in numeric_grades)
        weighted_sum = sum(row[1] * row[2] for row in numeric_grades)
        if total_points == 0:
            return 0.0
        return round(weighted_sum / total_points, 2)


def create_repository(db_path: str) -> GradeRepository:
    """Factory for GradeRepository."""
    logger.info(f"Using SqliteGradeRepository (path: {db_path})")
    return SqliteGradeRepository(db_path)
