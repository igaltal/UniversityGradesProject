# Grade Tracker

Automated grade monitoring system for Reichman University.  
Log in through the web interface, choose your academic year and semester, and the system scrapes your grades from the university portal, stores them locally, and optionally sends Telegram notifications when new grades appear.

---

## Features

- **Web-based login** — enter your university credentials in the browser; no manual `.env` editing required.
- **Dynamic year & semester** — choose any academic year and semester from the login page; no hardcoded values.
- **Automated scraping** — Selenium logs into the portal, navigates to the grades page, and extracts every published grade.
- **Live scraper status** — the dashboard shows a real-time progress banner while the scraper runs.
- **Telegram notifications** — optional push messages when a new grade is detected. Configure directly from the login page or via `.env`.
- **Log-only mode** — when Telegram is not configured, notifications are written to the application log instead.
- **Grades dashboard** — clean, responsive web UI with color-coded grades, weighted average, and per-course status.
- **SQLite storage** — lightweight, zero-config database. Courses are auto-discovered from the portal (no hardcoded course list).
- **Design patterns** — Notifier abstraction (Strategy + Factory), GradeRepository abstraction (Adapter + Factory), centralized configuration (Singleton-style).

---

## Project Structure

```
UniversityGradesProject/
├── src/university_grades/
│   ├── __init__.py
│   ├── __main__.py             # python -m university_grades (web app)
│   ├── cli.py                  # CLI entry points (grade-tracker, grade-scraper)
│   ├── core/
│   │   ├── config.py           # Centralized configuration (env, XPaths, defaults)
│   │   ├── grade_repository.py # Repository abstraction (SqliteGradeRepository)
│   │   └── notifier.py         # Notifier abstraction (Telegram, Log)
│   ├── scraping/
│   │   └── scraper.py          # Selenium scraper logic
│   └── web/
│       ├── app.py              # Flask application (login, dashboard, scraper trigger)
│       ├── create_db.py        # Database initialization
│       ├── templates/          # login.html, index.html, dashboard.html
│       └── static/             # css/styles.css, js/scripts.js
├── scripts/                    # Development & debug utilities
│   ├── check_login_fields.py   # List login form fields
│   ├── debug_after_login.py    # Debug post-login flow
│   ├── find_elements.py        # XPath discovery on Runi portal
│   └── test_telegram.py        # Verify Telegram bot config
├── tests/                      # Test suite
├── database/
│   └── grades.db               # SQLite database (auto-created)
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/yourusername/UniversityGradesProject.git
cd UniversityGradesProject

python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -e .
```

Or with requirements only:

```bash
pip install -r requirements.txt
```

### 2. Initialize the database

```bash
python -m university_grades.web.create_db
```

### 3. Start the web app

```bash
grade-tracker
```

Or:

```bash
python -m university_grades
```

Open **http://127.0.0.1:5001** in your browser.

### 4. Log in and fetch grades

1. Enter your **Reichman University username and password** on the login page.
2. Select the **academic year** and **semester** you want to check.
3. (Optional) Toggle **Telegram notifications** and enter your bot token + chat ID.
4. Click **Sign In & Fetch Grades**.
5. The scraper launches in the background — a live status banner shows progress.
6. When scraping finishes the dashboard reloads with your grades.

> **Note:** Your credentials are used only for the current scraping session. They are not written to disk or stored in any file.

---

## How It Works

```
Browser ──► Flask (login form: credentials + year + semester + telegram)
                │
                ├─► Background thread: Selenium
                │       │
                │       ├─► University portal (login, navigate, select year/semester, extract)
                │       ├─► SQLite (upsert grades — auto-discover courses)
                │       └─► Telegram API or Logger (notification)
                │
                └─► Dashboard (read grades from SQLite, render HTML)
```

1. User submits credentials, year, semester, and optional Telegram config via the login page.
2. Flask starts a **background thread** that launches a Chrome browser with Selenium.
3. The browser logs into the university portal, navigates to the grades page, selects the chosen year and semester, and extracts every course card.
4. The database is cleared and repopulated — courses are **auto-discovered** from the portal (no hardcoded list).
5. Each grade is written to SQLite through the **GradeRepository** abstraction (`upsert`).
6. If a new grade is found, a notification is sent through the **Notifier** abstraction (Telegram or log).
7. The dashboard polls `/scraper-status` and auto-reloads when scraping completes.
8. **Periodic check:** While you stay logged in, a background task re-runs the scraper every 60 seconds (configurable via `GRADE_CHECK_INTERVAL`). If a new grade is published on the portal, the dashboard updates automatically.

---

## Architecture & Design Patterns

### Notifier — Strategy + Factory

```
Notifier (ABC)
├── TelegramNotifier    — sends via Telegram Bot API
└── LogNotifier         — writes to log (fallback)

create_notifier(config)                — factory from Config object
create_notifier(token=..., chat_id=...) — factory from explicit values
```

### GradeRepository — Adapter + Factory

```
GradeRepository (ABC)
└── SqliteGradeRepository   — wraps sqlite3 behind a clean interface
    ├── get_all()           — all grades
    ├── upsert(course, grade) — insert or update (auto-discover)
    ├── clear_all()         — wipe before fresh scrape
    └── calculate_average() — weighted average

create_repository(db_path)  — factory that returns the right implementation
```

### Config — Singleton-style

`Config` is a class with only class-level attributes and `@classmethod` methods. It is never instantiated — used as a single shared namespace for all settings, XPaths, and defaults.

---

## Standalone CLI Mode

Run the scraper without the web app, using credentials from `.env`:

```bash
grade-scraper
```

Or:

```bash
python -c "from university_grades.cli import main; main()"
```

This starts two threads:
- **Scraper loop** — checks grades every `CHECK_INTERVAL` seconds with retry logic. Uses `DEFAULT_YEAR` and `DEFAULT_SEMESTER` from `.env` or config defaults.
- **Telegram bot** — responds to `/start`, `/help`, `/grades` commands.

---

## Development Scripts

After `pip install -e .`, run from project root:

| Script | Description |
|--------|-------------|
| `python scripts/check_login_fields.py` | List login form fields on Runi portal |
| `python scripts/debug_after_login.py` | Debug post-login flow (requires `.env` credentials) |
| `python scripts/find_elements.py` | Inspect elements for XPath discovery |
| `python scripts/test_telegram.py` | Verify Telegram bot configuration |

---

## Configuration

All settings are loaded from environment variables (`.env` file or system env).

| Variable              | Default | Description                                    |
|-----------------------|---------|------------------------------------------------|
| `TELEGRAM_BOT_TOKEN`  | —       | Telegram bot token (optional)                  |
| `TELEGRAM_CHAT_ID`    | —       | Telegram chat ID (optional)                    |
| `RUNI_USERNAME`       | —       | University username (used in CLI mode)         |
| `RUNI_PASSWORD`       | —       | University password (used in CLI mode)         |
| `DEFAULT_YEAR`        | 2025    | Academic year for CLI mode                     |
| `DEFAULT_SEMESTER`    | 2       | Semester for CLI mode                          |
| `DATABASE_PATH`       | auto    | Path to SQLite file                            |
| `MAX_RETRY_ATTEMPTS`  | 3       | Max consecutive failures before stopping       |
| `RETRY_DELAY`         | 30      | Seconds between retries                        |
| `CHECK_INTERVAL`      | 300     | Seconds between grade checks (CLI mode)        |
| `WEBDRIVER_TIMEOUT`   | 20      | Selenium element wait timeout                  |
| `GRADE_CHECK_INTERVAL` | 60      | Seconds between automatic grade checks (web; when logged in) |
| `FLASK_SECRET_KEY`    | dev     | Flask session secret (set a real value in prod)|

---

## Database Schema

```sql
CREATE TABLE grades (
    course  TEXT PRIMARY KEY,
    grade   INTEGER,
    points  REAL DEFAULT 3.0
);
```

Courses are **auto-discovered** from the portal on each scrape. The `course` field is the primary key, and `upsert` handles both new and existing courses.

---

## Telegram Bot Commands

| Command   | Description                |
|-----------|----------------------------|
| `/start`  | Welcome message            |
| `/help`   | List available commands    |
| `/grades` | Show current grades        |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| App hangs on startup | If the project is in iCloud/Dropbox, `.env` read can be slow. Run with `DOTENV_SKIP=1 grade-tracker` and set credentials via shell: `export RUNI_USERNAME=... RUNI_PASSWORD=...` |
| `unable to open database file` | Remove `DATABASE_PATH` from `.env` if set (or use an absolute path). The default is `project_root/database/grades.db`. |
| `Missing required configuration` | Create `.env` from `.env.example` and fill in values. |
| `Unable to locate element` | University portal HTML changed — update XPaths in `src/university_grades/core/config.py`. |
| `Telegram 401 Unauthorized` | Regenerate bot token via @BotFather. |
| Scraper banner shows error | Check `grade_checker.log` for details; verify Chrome/ChromeDriver is installed. |

---

## Tech Stack

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Web framework | Flask                               |
| Scraping      | Selenium + ChromeDriver             |
| Database      | SQLite                              |
| Notifications | pyTelegramBotAPI                    |
| Config        | python-dotenv                       |
| Testing       | pytest                              |

---

## Future Improvements

- Multi-user support with per-user databases
- Grade history and trend charts
- Email notification strategy
- Docker containerization
- Headless browser mode for server deployment
- Scheduled scraping via cron or Celery

---

## License

This project is for educational purposes.
