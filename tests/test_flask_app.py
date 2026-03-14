"""Unit tests for the Flask application (app.py).

The app uses a repository pattern and has login/dashboard/logout routes.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from university_grades.core import SqliteGradeRepository
from university_grades.web.app import app as flask_app


@pytest.fixture
def app_with_db(graded_db):
    """Flask app wired to a graded temp database."""
    repo = SqliteGradeRepository(graded_db)
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    flask_app.config["_repository"] = repo
    yield flask_app


@pytest.fixture
def client(app_with_db):
    return app_with_db.test_client()


def _login(client, username='testuser', password='testpass'):
    """Helper to log in via the login form."""
    return client.post('/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)


# ---------------------------------------------------------------------------
# Landing / redirect tests
# ---------------------------------------------------------------------------

class TestLandingRoute:

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_authenticated_redirects_to_dashboard(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
        response = client.get('/')
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

class TestLoginRoute:

    def test_get_login_page(self, client):
        response = client.get('/login')
        assert response.status_code == 200

    @patch("university_grades.web.app.scraper_status", {"running": False, "message": "", "last_result": None})
    def test_post_valid_credentials_redirects_to_dashboard(self, client):
        with patch("university_grades.web.app.threading"):
            response = client.post('/login', data={
                'username': 'user', 'password': 'pass'
            })
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']

    @patch("university_grades.web.app.scraper_status", {"running": False, "message": "", "last_result": None})
    def test_post_sets_session(self, client):
        with patch("university_grades.web.app.threading"):
            client.post('/login', data={
                'username': 'myuser', 'password': 'mypass'
            })
        with client.session_transaction() as sess:
            assert sess['logged_in'] is True
            assert sess['username'] == 'myuser'

    def test_post_empty_username_shows_error(self, client):
        response = _login(client, username='', password='pass')
        html = response.data.decode('utf-8')
        assert response.status_code == 200

    def test_post_empty_password_shows_error(self, client):
        response = _login(client, username='user', password='')
        html = response.data.decode('utf-8')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------

class TestLogoutRoute:

    def test_logout_clears_session(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'user'

        response = client.get('/logout')
        assert response.status_code == 302

        with client.session_transaction() as sess:
            assert 'logged_in' not in sess

    def test_logout_redirects_to_login(self, client):
        response = client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------

class TestDashboardRoute:

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_authenticated_shows_dashboard(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'testuser'
        response = client.get('/dashboard')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'testuser' in html

    def test_dashboard_contains_grades(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'testuser'
        response = client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert '90' in html
        assert '85' in html
        assert '78' in html

    def test_dashboard_contains_average(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'testuser'
        response = client.get('/dashboard')
        html = response.data.decode('utf-8')
        expected_avg = round((90 * 3 + 85 * 3 + 78 * 3) / 9, 2)
        assert str(expected_avg) in html

    def test_dashboard_contains_course_names(self, client):
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'testuser'
        response = client.get('/dashboard')
        html = response.data.decode('utf-8')
        assert 'Entrepreneurship' in html


class TestDashboardWithEmptyDB:

    @pytest.fixture
    def empty_client(self, temp_db):
        repo = SqliteGradeRepository(temp_db)
        flask_app.config["TESTING"] = True
        flask_app.config["SECRET_KEY"] = "test-secret"
        flask_app.config["_repository"] = repo
        yield flask_app.test_client()

    def test_dashboard_empty_db(self, empty_client):
        with empty_client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'testuser'
        response = empty_client.get('/dashboard')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '0.0' in html or '0' in html


# ---------------------------------------------------------------------------
# Scraper status API
# ---------------------------------------------------------------------------

class TestScraperStatusAPI:

    def test_returns_json(self, client):
        response = client.get('/scraper-status')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_contains_running_key(self, client):
        response = client.get('/scraper-status')
        data = response.get_json()
        assert 'running' in data
