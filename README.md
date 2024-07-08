# University Grades Project

This project automates the process of retrieving and notifying university grades using a combination of Selenium for web scraping, SQLite for database management, and a Telegram bot for notifications.

## Project Structure

UniversityGradesProject/
├── database
│ └── grades.db
├── flask_app
│ ├── app.py
│ ├── create_db.py
│ ├── static
│ ├── templates
│ │ └── index.html
│ └── venv
├── selenium_script
│ ├── get_grades.py
│ ├── get.py
├── requirements.txt
└── venv


## Setup Instructions

1. **Clone the Repository**

   git clone https://github.com/yourusername/UniversityGradesProject.git
   cd UniversityGradesProject

2. **Create Virtual Environment**

    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. **install requirements**

    pip install -r requirements.txt

4. **Set Up the Database**

    Navigate to the flask_app directory and run the create_db.py script to set up the SQLite database:

    cd flask_app
    python create_db.py

5. **Run the Flask Application**

    In the flask_app directory, run the Flask application:

    python app.py
    The application will be accessible at http://127.0.0.1:5001.

6. **Run the Selenium Script**

    Open another terminal, navigate to the selenium_script directory, and run the get_grades.py script:

    cd selenium_script
    python get_grades.py


## File Descriptions

### `flask_app/create_db.py`

This script initializes the SQLite database. It ensures the database directory exists, drops the existing `grades` table if it exists, creates a new `grades` table, and inserts initial data.

### `flask_app/app.py`

This is the main Flask application. It defines routes and functions to retrieve grades from the database, calculate the average grade, and render the grades on an HTML page.

### `templates/index.html`

The HTML template for displaying grades and the average grade.

### `selenium_script/get_grades.py`

This script uses Selenium to scrape grades from the Runi website and update the SQLite database. It also sends notifications to a Telegram bot when new grades are available.
