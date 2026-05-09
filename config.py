"""
Configuration module for WikiBot.

This module loads environment variables and validates the bot token.
Ensure your .env file contains:
    BOT_TOKEN=your_telegram_bot_token_here
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN not found in environment variables. "
        "Please create a .env file with BOT_TOKEN=your_token"
    )

if len(BOT_TOKEN) < 10:
    raise ValueError("BOT_TOKEN seems invalid (too short). Check your .env file.")