"""
Flask web application for Grade Tracker.
"""

import os
import threading
import logging
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from university_grades.core import create_repository, Config
from university_grades.scraping import run_web_scraper

logger = logging.getLogger(__name__)

scraper_status = {"running": False, "last_result": None, "message": None}

# Stored credentials for periodic checks (set on login, cleared on logout)
_active_credentials = {}
_credentials_lock = threading.Lock()
_periodic_thread = None
_periodic_started = False


def _periodic_scraper_loop():
    """Background loop: re-run scraper every GRADE_CHECK_INTERVAL when logged in."""
    interval = Config.GRADE_CHECK_INTERVAL
    while True:
        threading.Event().wait(interval)
        with _credentials_lock:
            creds = dict(_active_credentials) if _active_credentials else None
        if not creds or scraper_status["running"]:
            continue
        repo = create_repository(Config.DATABASE_PATH)
        logger.info("Periodic check: fetching grades from portal...")
        run_web_scraper(
            creds["username"],
            creds["password"],
            creds["year"],
            creds["semester"],
            repo,
            scraper_status,
            telegram_token=creds.get("telegram_token"),
            telegram_chat_id=creds.get("telegram_chat_id"),
        )


def create_app(repository=None):
    """Application factory. Pass repository= for testing."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
        static_url_path="/static",
    )
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-in-production")

    repository = repository or create_repository(Config.DATABASE_PATH)
    app.config["_repository"] = repository

    global _periodic_thread, _periodic_started
    if not _periodic_started:
        _periodic_thread = threading.Thread(
            target=_periodic_scraper_loop,
            daemon=True,
        )
        _periodic_thread.start()
        _periodic_started = True

    @app.route("/")
    def landing():
        if session.get("logged_in"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            year = request.form.get("year", "2025")
            semester = request.form.get("semester", "2")
            telegram_token = None
            telegram_chat_id = None
            if request.form.get("enable_telegram"):
                telegram_token = request.form.get("telegram_token", "").strip() or None
                telegram_chat_id = (
                    request.form.get("telegram_chat_id", "").strip() or None
                )

            if not username or not password:
                flash("Please enter both username and password.", "error")
                return render_template("login.html")

            session["logged_in"] = True
            session["username"] = username
            session["year"] = year
            session["semester"] = semester
            session["telegram_enabled"] = bool(telegram_token and telegram_chat_id)

            with _credentials_lock:
                _active_credentials.clear()
                _active_credentials.update({
                    "username": username,
                    "password": password,
                    "year": year,
                    "semester": semester,
                    "telegram_token": telegram_token,
                    "telegram_chat_id": telegram_chat_id,
                })

            repo = app.config["_repository"]
            if not scraper_status["running"]:
                t = threading.Thread(
                    target=run_web_scraper,
                    args=(username, password, year, semester, repo),
                    kwargs={
                        "status_dict": scraper_status,
                        "telegram_token": telegram_token,
                        "telegram_chat_id": telegram_chat_id,
                    },
                    daemon=True,
                )
                t.start()

            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard():
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        repo = app.config["_repository"]
        grades = repo.get_all()
        average = repo.calculate_average()
        return render_template(
            "dashboard.html",
            grades=grades,
            average=average,
            username=session.get("username", ""),
            year=session.get("year", ""),
            semester=session.get("semester", ""),
            telegram_enabled=session.get("telegram_enabled", False),
            scraper=scraper_status,
        )

    @app.route("/scraper-status")
    def scraper_status_api():
        from flask import jsonify
        return jsonify(scraper_status)

    @app.route("/logout")
    def logout():
        with _credentials_lock:
            _active_credentials.clear()
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    return app


app = create_app()
