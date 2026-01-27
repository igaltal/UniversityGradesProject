# University Grades Monitoring System

Automated grade tracking system using Selenium web scraping, SQLite database, Flask web interface, and Telegram notifications.

## Features

- Automated grade checking from university portal
- Real-time Telegram notifications for new grades
- Web dashboard for grade viewing
- SQLite database for grade history
- Secure credential management
- Comprehensive error handling and logging

## Project Structure

```
UniversityGradesProject/
├── database/
│   └── grades.db                # SQLite database
├── flask_app/
│   ├── app.py                   # Flask web application
│   ├── create_db.py             # Database initialization
│   ├── templates/
│   │   └── index.html           # Web interface
│   └── static/                  # CSS and JS files
├── selenium_script/
│   ├── get_grades.py            # Main scraping script
│   ├── config.py                # Configuration management
│   └── requirements.txt         # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git exclusions
├── SECURITY.md                  # Security documentation
└── README.md                    # This file
```

## Security Features

- Environment-based credential management
- No hardcoded secrets in source code
- Git protection against credential leaks
- Comprehensive logging
- See SECURITY.md for details

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/UniversityGradesProject.git
cd UniversityGradesProject
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- Get Telegram bot token from @BotFather
- Get your chat ID from @userinfobot
- Add your university credentials

### 5. Initialize Database

```bash
cd flask_app
python create_db.py
cd ..
```

### 6. Run Application

Terminal 1 - Web Interface:
```bash
cd flask_app
python app.py
```
Access at: http://127.0.0.1:5001

Terminal 2 - Grade Checker:
```bash
cd selenium_script
python get_grades.py
```

## Configuration Options

Edit `.env` to customize:

- `MAX_RETRY_ATTEMPTS`: Max retries before stopping (default: 3)
- `RETRY_DELAY`: Seconds between retries (default: 30)
- `CHECK_INTERVAL`: Seconds between grade checks (default: 300)
- `WEBDRIVER_TIMEOUT`: Selenium timeout (default: 20)

## Telegram Bot Commands

- `/start` - Show welcome message
- `/help` - Display available commands
- `/grades` - View current grades

## Technical Details

### Grade Checking Process

1. Selenium opens Chrome browser
2. Navigates to university portal
3. Logs in with credentials
4. Navigates to grades page
5. Extracts all grades using XPath
6. Updates database if grades changed
7. Sends Telegram notification for new grades
8. Waits configured interval before next check

### Error Handling

- Automatic retry on failure
- Maximum retry limit to prevent infinite loops
- Detailed logging to `grade_checker.log`
- Telegram notifications on errors

### Database Schema

```sql
CREATE TABLE grades (
    course TEXT,
    grade INTEGER,
    points INTEGER
);
```

## Troubleshooting

### Configuration Error

```
Missing required configuration: TELEGRAM_BOT_TOKEN
```
Solution: Create `.env` file from `.env.example` and fill in values

### XPath Not Found

```
Unable to locate element
```
Solution: University website structure changed. Update XPaths in `config.py`

### Telegram 401 Error

```
Unauthorized
```
Solution: Get new bot token from @BotFather

## Interview Presentation Notes

### Security Highlights

1. **Credential Protection**: No secrets in code or git
2. **Environment Isolation**: `.env` for configuration
3. **Git Security**: Comprehensive `.gitignore`
4. **Validation**: Config validation at startup
5. **Error Handling**: Graceful failure modes
6. **Logging**: Audit trail for operations

### Architecture Highlights

1. **Separation of Concerns**: Web app, scraper, and bot are independent
2. **Threading**: Concurrent bot and scraper operation
3. **Database**: Persistent storage with SQLite
4. **Configuration Management**: Centralized in `config.py`
5. **Error Recovery**: Retry logic with backoff

### Code Quality

1. **Logging**: Professional logging setup
2. **Error Handling**: Try-except blocks throughout
3. **Documentation**: Clear comments and docstrings
4. **Modularity**: Functions with single responsibilities
5. **Configuration**: Easy to modify without code changes

## Future Improvements

- Add email notifications
- Support multiple users
- Grade analytics and trends
- Mobile app integration
- Docker containerization
- Unit and integration tests

## License

This project is for educational purposes.
