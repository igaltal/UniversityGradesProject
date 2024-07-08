#/Users/igaltal/Desktop/UniversityGradesProject/flask_app/create_db.py
import sqlite3
import os

# Ensure the database directory exists
os.makedirs('../database', exist_ok=True)

# Connect to the database
conn = sqlite3.connect('../database/grades.db')
cursor = conn.cursor()

# Drop the existing table if it exists (for clean re-creation)
cursor.execute('DROP TABLE IF EXISTS grades')

# Create the grades table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS grades (
        course TEXT,
        grade INTEGER,
        points INTEGER
    )
''')

# Insert initial data only if the table is empty
cursor.execute('SELECT COUNT(*) FROM grades')
if cursor.fetchone()[0] == 0:
    courses = [
        ("Logic and Set Theory", None, 5),
        ("Operating Systems", None, 4),
        ("Advanced English", None, 0),
        ("Product Design", None, 3),
        ("Product Management", None, 3),
        ("Computational Learning", None, 4),
        ("Computational Models", None, 4),
        ("Intro to Statistics", None, 4),
        ("Accounting for Entrepreneurs", None, 1),
        ("Venture Capital", None, 3),
    ]
    cursor.executemany('INSERT INTO grades (course, grade, points) VALUES (?, ?, ?)', courses)

# Commit the changes and close the connection
conn.commit()
conn.close()
