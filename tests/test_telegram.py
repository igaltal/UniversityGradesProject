"""
Test Telegram bot configuration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'selenium_script'))

import telebot
from config import Config

def test_telegram():
    print("Testing Telegram configuration...")
    print(f"Bot Token: {Config.TELEGRAM_BOT_TOKEN[:10]}...{Config.TELEGRAM_BOT_TOKEN[-5:]}")
    print(f"Chat ID: {Config.TELEGRAM_CHAT_ID}")
    
    bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)
    
    try:
        print("\nGetting bot info...")
        bot_info = bot.get_me()
        print(f"Bot name: {bot_info.username}")
        print(f"Bot ID: {bot_info.id}")
        print("Bot token is valid!")
        
        print(f"\nTrying to send test message to chat {Config.TELEGRAM_CHAT_ID}...")
        bot.send_message(Config.TELEGRAM_CHAT_ID, "Test message from grade checker")
        print("Message sent successfully!")
        print("\nCheck your Telegram to see if you received the message.")
        
    except telebot.apihelper.ApiTelegramException as e:
        print(f"\nTelegram API Error: {e}")
        print("\nPossible issues:")
        print("1. Chat ID is wrong - get it from @userinfobot")
        print("2. You haven't started a chat with the bot - send /start to your bot first")
        print("3. Bot token is invalid - create a new bot with @BotFather")
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    try:
        Config.validate()
        test_telegram()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please create .env file with your credentials")
