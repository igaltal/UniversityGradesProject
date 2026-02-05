from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_grades():
    conn = sqlite3.connect('../database/grades.db')
    cursor = conn.cursor()
    cursor.execute('SELECT course, grade, points FROM grades')
    data = cursor.fetchall()
    conn.close()
    return data

def calculate_average(grades):
    total_points = sum([grade[2] for grade in grades if grade[1] is not None])
    total_grades = sum([grade[1] * grade[2] for grade in grades if grade[1] is not None])
    average = total_grades / total_points if total_points > 0 else 0
    return round(average, 2)

@app.route('/')
def index():
    grades = get_grades()
    average = calculate_average(grades)
    return render_template('index.html', grades=grades, average=average)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
