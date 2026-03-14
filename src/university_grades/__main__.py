"""
Allow running: python -m university_grades
"""

from university_grades.web.app import app

if __name__ == "__main__":
    from pathlib import Path
    BASE_DIR = Path(__file__).parent.parent.parent
    db_path = BASE_DIR / "database" / "grades.db"
    print(f"Using database: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    app.run(debug=True, port=5001)
