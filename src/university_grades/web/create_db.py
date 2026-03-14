"""
Database initialization script.
Run: python -m university_grades.web.create_db
"""

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "grades.db"

os.makedirs(DATABASE_DIR, exist_ok=True)

conn = sqlite3.connect(str(DATABASE_PATH))
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

print(f"Database ready at {DATABASE_PATH}")


if __name__ == "__main__":
    pass  # Already executed above
