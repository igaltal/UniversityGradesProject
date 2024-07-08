# University Grades Project

This project includes a Selenium script to fetch grades from the university website and a Flask web application to display the grades and calculate the average.

## Folder Structure
UniversityGradesProject/
│
├── selenium_script/
│ ├── get_grades.py
│ └── requirements.txt
├── README.md
├── flask_app/
│ ├── app.py
│ ├── templates/
│ │ └── index.html
│ ├── static/
│ │ ├── css/
│ │ │ └── styles.css
│ │ └── js/
│ │ └── scripts.js
│ └── create_db.py
│
├── database/
│ └── grades.db
│

## How to Run

1. **Selenium Script**:
   - Navigate to the `selenium_script` directory.
   - Install the required packages:
     ```bash
     pip install -r requirements.txt
     ```
   - Run the Selenium script:
     ```bash
     python get_grades.py
     ```

2. **Flask Application**:
   - Navigate to the `flask_app` directory.
   - Initialize the database:
     ```bash
     python create_db.py
     ```
   - Run the Flask application:
     ```bash
     python app.py
     ```

3. **Access the Web Application**:
   - Open your browser and go to `http://127.0.0.1:5000` to view your grades and the average grade.

## Notes

- Ensure that you have the Chrome driver installed and properly set up for the Selenium script to work.
- Update the credentials in the Selenium script with your actual university username and password.
- Update the Telegram Bot token in the Selenium script to enable notifications.
