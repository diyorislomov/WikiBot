# WikiBot 🤖

A fast, multi-language Telegram bot that fetches Wikipedia articles on demand with intelligent disambiguation handling.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![aiogram](https://img.shields.io/badge/aiogram-3.3.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- 🌐 **Multi-language support** - Switch between Uzbek, Russian, and English
- 📖 **Instant Wikipedia search** - Get articles in seconds
- 🎲 **Random article generation** - Explore random Wikipedia topics
- 🔍 **Smart disambiguation** - Handles multiple results intelligently
- 💾 **Persistent preferences** - Your language choice is saved
- ⚡ **Async performance** - Built with asyncio for speed
- 📝 **Detailed logging** - Track all activity in wikibot.log

## Requirements

- **Python 3.8+**
- **pip** (Python package manager)
- A **Telegram Bot Token** from BotFather (@BotFather on Telegram)

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/diyorislomov/WikiBot.git
cd WikiBot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Bot Token
Create a `.env` file in the project root:
```bash
echo "BOT_TOKEN=your_telegram_bot_token_here" > .env
```

Replace `your_telegram_bot_token_here` with your actual bot token from BotFather.

**Important:** Never commit `.env` to GitHub. It's already in `.gitignore`.

### 4. Run the Bot
```bash
python bot.py
```

You should see:
```
INFO:__main__:Starting WikiBot...
```

## Usage

### Commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot introduction |
| `/wiki <query>` | Search Wikipedia for a topic (e.g., `/wiki Tashkent`) |
| `/lang` | Change your preferred language |

### Regular Messages
Simply send any text to search Wikipedia:
```
User: Python
Bot: Returns Wikipedia article about Python
```

### Buttons
- 🎲 **Random Article** - Explore a random Wikipedia page
- 🌐 **Change Language** - Switch between Uz/Ru/En

## Project Structure

```
WikiBot/
├── bot.py                    # Main bot logic with handlers
├── config.py                 # Environment configuration
├── requirements.txt          # Python dependencies
├── .env                      # Bot token (not committed)
├── .gitignore               # Git ignore rules
├── user_preferences.json    # Persistent user data (auto-created)
├── wikibot.log             # Activity log (auto-created)
└── README.md               # This file
```

## Key Features Explained

### 1. Multi-Language Support
The bot automatically switches between languages based on user preference:
- 🇺🇿 **Uzbek** (O'zbekcha)
- 🇷🇺 **Russian** (Русский)
- 🇬🇧 **English** (English)

### 2. Smart Search
The bot handles three search scenarios:
- **Exact match** - Returns the article directly
- **Disambiguation** - Shows multiple options
- **No exact match** - Suggests related articles

### 3. Data Persistence
User language preferences are saved in `user_preferences.json`:
```json
{
  "123456789": {
    "lang": "uz"
  }
}
```

This means preferences persist even after bot restart.

### 4. Comprehensive Logging
All activity is logged to `wikibot.log`:
- User searches
- Language changes
- Errors and exceptions
- Bot startup/shutdown

## Error Handling

The bot handles common errors gracefully:
- **Wikipedia timeout** - Retry message
- **Invalid search** - Suggest alternatives
- **Network errors** - User-friendly error messages

All errors are logged for debugging.

## Development

### Code Quality
- **Async/await** - Proper async programming with aiogram
- **Type hints** - Better code documentation
- **Docstrings** - Every function documented
- **Constants** - No magic numbers
- **Error handling** - Comprehensive exception handling

### How to Extend

Add a new command:
```python
@dp.message(Command("newcommand"))
async def cmd_new(message: types.Message):
    """Handle new command."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} used new command")
    await message.answer("Response text")
```

Add a new language:
```python
LANGUAGES["fr"] = "🇫🇷 Français"
TRANSLATIONS["fr"] = {
    "welcome": "Bienvenue...",
    # ... other translations
}
```

## Deployment Options

### Local (Development)
Run directly on your machine:
```bash
python bot.py
```

### Heroku
1. Create `Procfile`:
```
worker: python bot.py
```

2. Deploy:
```bash
git push heroku main
```

### DigitalOcean Droplet
1. SSH into droplet
2. Clone repository
3. Install Python and dependencies
4. Run with systemd or supervisor for persistence

### Docker
Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

Run:
```bash
docker build -t wikibot .
docker run wikibot
```

## Performance

- **Response time** - Usually <1 second per query
- **Memory usage** - ~50-100MB at startup
- **Concurrency** - Handles multiple users simultaneously
- **Wikipedia API** - Rate-limited to prevent abuse

## Troubleshooting

### Bot doesn't start
```
❌ BOT_TOKEN not found
```
**Solution:** Create `.env` file with your token

### Invalid token error
**Solution:** Verify token from BotFather (@BotFather on Telegram)

### "Nothing found" for valid search
**Solution:** Try a different language or check Wikipedia directly

### Permissions denied error
**Solution:** Ensure you have write permissions to the project directory

## Contributing

Found a bug? Have a feature idea?
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Diyorbek Islomov** - [@diyorislomov](https://github.com/diyorislomov)

Connect with me:
- 🤖 Telegram Bot: [@yourwikipediabot](https://t.me/yourwikipediabot)
- 🤖 Telegram: [@DiyorIslomov](https://t.me/DiyorIslomov)
- 💻 GitHub: [diyorislomov](https://github.com/diyorislomov)

## Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram bot framework
- [Wikipedia-API](https://github.com/goldsmith/Wikipedia) - Wikipedia access
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment management

## Support

If you encounter any issues:
1. Check the `wikibot.log` file for error details
2. Verify `.env` configuration
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Open an issue on GitHub with error details

---

**Made with ❤️ by Diyorbek Islomov**
