"""Unit tests for the Notifier classes (notifier.py).

telebot is not installed in the test environment, so we mock it at import time.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.modules.setdefault("telebot", MagicMock())

from university_grades.core import LogNotifier, TelegramNotifier, create_notifier, Notifier


class TestLogNotifier:

    def test_send_returns_true(self):
        n = LogNotifier()
        assert n.send("hello") is True

    def test_implements_notifier_interface(self):
        assert isinstance(LogNotifier(), Notifier)


class TestTelegramNotifier:

    def test_send_calls_bot(self):
        n = TelegramNotifier("fake-token", "12345")
        n._bot = MagicMock()
        result = n.send("test message")
        assert result is True
        n._bot.send_message.assert_called_once_with("12345", "test message")

    def test_send_returns_false_on_error(self):
        n = TelegramNotifier("fake-token", "12345")
        n._bot = MagicMock()
        n._bot.send_message.side_effect = Exception("Network error")
        assert n.send("test") is False

    def test_bot_property(self):
        n = TelegramNotifier("fake-token", "12345")
        assert n.bot is not None

    def test_implements_notifier_interface(self):
        assert isinstance(TelegramNotifier("t", "c"), Notifier)


class TestCreateNotifier:

    def test_returns_telegram_when_configured(self):
        config = MagicMock()
        config.TELEGRAM_BOT_TOKEN = "token"
        config.TELEGRAM_CHAT_ID = "123"
        n = create_notifier(config)
        assert isinstance(n, TelegramNotifier)

    def test_returns_log_when_token_missing(self):
        config = MagicMock()
        config.TELEGRAM_BOT_TOKEN = None
        config.TELEGRAM_CHAT_ID = "123"
        n = create_notifier(config)
        assert isinstance(n, LogNotifier)

    def test_returns_log_when_chat_id_missing(self):
        config = MagicMock()
        config.TELEGRAM_BOT_TOKEN = "token"
        config.TELEGRAM_CHAT_ID = None
        n = create_notifier(config)
        assert isinstance(n, LogNotifier)

    def test_returns_log_when_both_missing(self):
        config = MagicMock()
        config.TELEGRAM_BOT_TOKEN = None
        config.TELEGRAM_CHAT_ID = None
        n = create_notifier(config)
        assert isinstance(n, LogNotifier)
