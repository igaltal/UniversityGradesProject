"""
Test Telegram bot configuration.
Run: python scripts/test_telegram.py (requires TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID in .env)
"""

import telebot
from university_grades.core import Config


def main():
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return
    print(f"Bot Token: {Config.TELEGRAM_BOT_TOKEN[:10]}...{Config.TELEGRAM_BOT_TOKEN[-5:]}")
    print(f"Chat ID: {Config.TELEGRAM_CHAT_ID}")

    bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)

    try:
        info = bot.get_me()
        print(f"\nBot: @{info.username}")
        bot.send_message(Config.TELEGRAM_CHAT_ID, "Test from Grade Tracker")
        print("Message sent! Check Telegram.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Check @BotFather and @userinfobot on Telegram.")


if __name__ == "__main__":
    main()
