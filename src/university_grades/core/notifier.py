"""
Notifier abstraction — Strategy + Factory pattern.
"""

from abc import ABC, abstractmethod
import logging
import telebot

logger = logging.getLogger(__name__)


class Notifier(ABC):
    """Abstract base class for notifications."""

    @abstractmethod
    def send(self, message: str) -> bool:
        """Send a notification. Returns True on success."""
        pass


class TelegramNotifier(Notifier):
    """Sends notifications via Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str):
        self._bot = telebot.TeleBot(bot_token)
        self._chat_id = chat_id

    @property
    def bot(self):
        return self._bot

    def send(self, message: str) -> bool:
        try:
            self._bot.send_message(self._chat_id, message)
            return True
        except Exception as e:
            logger.warning(f"Telegram notification skipped: {e}")
            return False


class LogNotifier(Notifier):
    """Writes notifications to the log."""

    def send(self, message: str) -> bool:
        logger.info(f"[LogNotifier] {message}")
        return True


def create_notifier(config=None, *, token=None, chat_id=None) -> Notifier:
    """Returns TelegramNotifier when credentials exist, else LogNotifier."""
    bot_token = token or (config.TELEGRAM_BOT_TOKEN if config else None)
    bot_chat_id = chat_id or (config.TELEGRAM_CHAT_ID if config else None)

    if bot_token and bot_chat_id:
        logger.info("Using TelegramNotifier")
        return TelegramNotifier(bot_token, bot_chat_id)

    logger.info("Telegram not configured — using LogNotifier")
    return LogNotifier()
