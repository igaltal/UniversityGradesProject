"""Unit tests for the Config class (config.py).

dotenv may not be installed in the test environment — conftest already mocks it.
The 'config' module in sys.modules may be a MagicMock (set by other test files),
so we force-remove it before importing the real module.
"""

import os
import types
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.modules.setdefault("dotenv", MagicMock())


def _reload_config(**env_overrides):
    """Reload the config module with the given environment variables."""
    defaults = {
        "TELEGRAM_BOT_TOKEN": "fake-token",
        "TELEGRAM_CHAT_ID": "12345",
        "RUNI_USERNAME": "user",
        "RUNI_PASSWORD": "pass",
    }
    defaults.update(env_overrides)

    mod_name = "university_grades.core.config"
    with patch.dict(os.environ, defaults, clear=False):
        existing = sys.modules.get(mod_name)
        if existing is not None and not isinstance(existing, types.ModuleType):
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            existing = None

        if existing is not None:
            importlib.reload(existing)
        else:
            import university_grades.core.config  # noqa: F401

        return getattr(sys.modules[mod_name], "Config")


class TestConfigValidation:
    """validate() requires RUNI_USERNAME and RUNI_PASSWORD.
    Telegram credentials are optional (the app falls back to LogNotifier)."""

    def test_valid_config_passes(self):
        cfg = _reload_config()
        cfg.validate()

    def test_missing_username_raises(self):
        cfg = _reload_config(RUNI_USERNAME='')
        with pytest.raises(ValueError, match='RUNI_USERNAME'):
            cfg.validate()

    def test_missing_password_raises(self):
        cfg = _reload_config(RUNI_PASSWORD='')
        with pytest.raises(ValueError, match='RUNI_PASSWORD'):
            cfg.validate()

    def test_both_runi_credentials_missing(self):
        cfg = _reload_config(RUNI_USERNAME='', RUNI_PASSWORD='')
        with pytest.raises(ValueError) as exc_info:
            cfg.validate()
        assert 'RUNI_USERNAME' in str(exc_info.value)
        assert 'RUNI_PASSWORD' in str(exc_info.value)

    def test_telegram_not_required(self):
        """Telegram credentials are optional — validate() should not raise."""
        cfg = _reload_config(TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='')
        cfg.validate()


class TestConfigDefaults:

    def test_default_retry_attempts(self):
        cfg = _reload_config()
        assert cfg.MAX_RETRY_ATTEMPTS == 3

    def test_default_check_interval(self):
        cfg = _reload_config()
        assert cfg.CHECK_INTERVAL == 300

    def test_default_webdriver_timeout(self):
        cfg = _reload_config()
        assert cfg.WEBDRIVER_TIMEOUT == 20

    def test_default_retry_delay(self):
        cfg = _reload_config()
        assert cfg.RETRY_DELAY == 30

    def test_custom_check_interval(self):
        cfg = _reload_config(CHECK_INTERVAL='600')
        assert cfg.CHECK_INTERVAL == 600

    def test_xpaths_dict_has_required_keys(self):
        cfg = _reload_config()
        assert isinstance(cfg.XPATHS, dict)
        required_keys = [
            'login_button', 'username_field', 'password_field',
            'submit_button', 'grades_tab', 'grades_list',
        ]
        for key in required_keys:
            assert key in cfg.XPATHS, f"Missing XPath key: {key}"

    def test_database_path_is_string(self):
        cfg = _reload_config()
        assert isinstance(cfg.DATABASE_PATH, str)

    def test_telegram_attributes_exist(self):
        cfg = _reload_config()
        assert hasattr(cfg, 'TELEGRAM_BOT_TOKEN')
        assert hasattr(cfg, 'TELEGRAM_CHAT_ID')

    def test_runi_credentials_loaded(self):
        cfg = _reload_config(RUNI_USERNAME='myuser', RUNI_PASSWORD='mypass')
        assert cfg.RUNI_USERNAME == 'myuser'
        assert cfg.RUNI_PASSWORD == 'mypass'
