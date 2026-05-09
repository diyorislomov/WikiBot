"""
WikiBot - A Telegram bot that fetches Wikipedia articles with multi-language support.

Features:
    - Search Wikipedia in multiple languages
    - Random article generation
    - Disambiguation handling
    - Persistent user language preferences
    - Comprehensive error handling and logging
"""

import asyncio
import logging
import html
import json
import os
from pathlib import Path

import wikipedia
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN

# ─── CONSTANTS ──────────────────────────────────────

MAX_RESULTS = 5
MAX_DISAMBIGUATION_OPTIONS = 8
MAX_SUMMARY_LENGTH = 3500
USER_DATA_FILE = "user_preferences.json"

# Supported languages and their display names
LANGUAGES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

# Translation dictionary for all messages
TRANSLATIONS = {
    "uz": {
        "welcome": "👋 <b>WikiBotga xush kelibsiz!</b>\n\nMavzuni yuboring yoki /wiki &lt;so'z&gt; yozing.\nTilni o'zgartirish: /lang",
        "usage": "❗ Foydalanish: <code>/wiki Toshkent</code>",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_set": "✅ Til o'rnatildi: {}",
        "loading": "Yuklanmoqda...",
        "random_loading": "Tasodifiy maqola yuklanmoqda...",
        "multiple": "🔍 <b>'{}'</b> bo'yicha bir nechta natija:\nKeraklisini tanlang:",
        "suggest": "🔍 <b>Buni nazarda tutdingizmi:</b>",
        "not_found": "❌ Hech narsa topilmadi. Boshqa so'z bilan urinib ko'ring.",
        "read_more": "🔗 To'liq maqolani o'qish",
        "random_btn": "🎲 Tasodifiy maqola",
        "change_lang": "🌐 Tilni o'zgartirish",
        "error": "❌ Xato: {}",
        "timeout_error": "❌ Vaqt tugadi. Wikipedia bilan ulanishda muammo.",
        "search_error": "❌ Qidirishda xatolik. Iltimos, boshqa so'z bilan urinib ko'ring.",
    },
    "ru": {
        "welcome": "👋 <b>Добро пожаловать в WikiBot!</b>\n\nОтправьте тему или напишите /wiki &lt;запрос&gt;.\nСменить язык: /lang",
        "usage": "❗ Использование: <code>/wiki Москва</code>",
        "choose_lang": "🌐 Выберите язык:",
        "lang_set": "✅ Язык установлен: {}",
        "loading": "Загрузка...",
        "random_loading": "Загрузка случайной статьи...",
        "multiple": "🔍 <b>По запросу '{}'</b> найдено несколько результатов:\nВыберите нужный:",
        "suggest": "🔍 <b>Возможно, вы имели в виду:</b>",
        "not_found": "❌ Ничего не найдено. Попробуйте другие слова.",
        "read_more": "🔗 Читать полную статью",
        "random_btn": "🎲 Случайная статья",
        "change_lang": "🌐 Сменить язык",
        "error": "❌ Ошибка: {}",
        "timeout_error": "❌ Истекло время ожидания. Проблема с подключением к Wikipedia.",
        "search_error": "❌ Ошибка при поиске. Пожалуйста, попробуйте другой поисковый запрос.",
    },
    "en": {
        "welcome": "👋 <b>Welcome to WikiBot!</b>\n\nSend a topic or type /wiki &lt;query&gt;.\nChange language: /lang",
        "usage": "❗ Usage: <code>/wiki Python</code>",
        "choose_lang": "🌐 Choose your language:",
        "lang_set": "✅ Language set: {}",
        "loading": "Loading...",
        "random_loading": "Loading random article...",
        "multiple": "🔍 <b>Multiple results for '{}':</b>\nChoose one:",
        "suggest": "🔍 <b>Did you mean:</b>",
        "not_found": "❌ Nothing found. Try different keywords.",
        "read_more": "🔗 Read full article",
        "random_btn": "🎲 Random article",
        "change_lang": "🌐 Change language",
        "error": "❌ Error: {}",
        "timeout_error": "❌ Connection timeout. Please try again later.",
        "search_error": "❌ Search error. Please try different keywords.",
    },
}

# ─── LOGGING SETUP ───────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wikibot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── BOT INITIALIZATION ──────────────────────────────

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ─── DATA PERSISTENCE ───────────────────────────────

class UserPreferences:
    """Manages persistent user preferences using JSON storage."""

    def __init__(self, filepath: str = USER_DATA_FILE):
        """
        Initialize user preferences manager.

        Args:
            filepath: Path to JSON file for storing user preferences
        """
        self.filepath = filepath
        self.data = self._load_data()

    def _load_data(self) -> dict:
        """Load user preferences from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Corrupted {self.filepath}, initializing fresh")
                return {}
        return {}

    def _save_data(self) -> None:
        """Save user preferences to JSON file."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"Failed to save user preferences: {e}")

    def get_lang(self, user_id: int) -> str:
        """
        Get user's preferred language.

        Args:
            user_id: Telegram user ID

        Returns:
            Language code ('uz', 'ru', 'en'). Defaults to 'uz'.
        """
        return self.data.get(str(user_id), {}).get("lang", "uz")

    def set_lang(self, user_id: int, lang: str) -> None:
        """
        Set user's preferred language.

        Args:
            user_id: Telegram user ID
            lang: Language code ('uz', 'ru', 'en')
        """
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            self.data[user_id_str] = {}
        self.data[user_id_str]["lang"] = lang
        self._save_data()
        logger.info(f"User {user_id} set language to {lang}")


# Initialize user preferences
user_prefs = UserPreferences()


# ─── TRANSLATION FUNCTIONS ──────────────────────────

def t(user_id: int, key: str) -> str:
    """
    Get translated text for a given key.

    Args:
        user_id: Telegram user ID
        key: Translation key

    Returns:
        Translated text in user's preferred language
    """
    lang = user_prefs.get_lang(user_id)
    return TRANSLATIONS.get(lang, TRANSLATIONS["uz"]).get(key, key)


# ─── UI BUILDERS ────────────────────────────────────

def lang_keyboard() -> InlineKeyboardMarkup:
    """
    Build inline keyboard with language options.

    Returns:
        InlineKeyboardMarkup with language buttons
    """
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
        for code, name in LANGUAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── MESSAGE HANDLERS ───────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} started bot")
    await message.answer(
        t(user_id, "welcome"),
        parse_mode="HTML"
    )


@dp.message(Command("lang"))
async def cmd_lang(message: types.Message):
    """Handle /lang command to change language."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} opened language menu")
    await message.answer(
        t(user_id, "choose_lang"),
        reply_markup=lang_keyboard(),
        parse_mode="HTML"
    )


@dp.message(Command("wiki"))
async def cmd_wiki(message: types.Message):
    """
    Handle /wiki command for Wikipedia search.

    Usage: /wiki <query>
    """
    user_id = message.from_user.id
    query = message.text.replace("/wiki", "").strip()

    if not query:
        logger.warning(f"User {user_id} sent empty /wiki command")
        await message.answer(t(user_id, "usage"), parse_mode="HTML")
        return

    logger.info(f"User {user_id} searched for: {query}")
    await search_wiki(message, query)


@dp.message()
async def text_search(message: types.Message):
    """Handle regular text messages as Wikipedia search queries."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} searched for: {message.text}")
    await search_wiki(message, message.text)


# ─── SEARCH LOGIC ───────────────────────────────────

async def search_wiki(message: types.Message, query: str):
    """
    Search Wikipedia and display results.

    Args:
        message: Telegram message object
        query: Search query
    """
    user_id = message.from_user.id
    lang = user_prefs.get_lang(user_id)

    try:
        wikipedia.set_lang(lang)
        page = wikipedia.page(query, auto_suggest=True)
        await send_article(message, page, user_id)

    except wikipedia.DisambiguationError as e:
        logger.info(f"Disambiguation needed for query: {query}")
        options = e.options[:MAX_DISAMBIGUATION_OPTIONS]
        buttons = [
            [InlineKeyboardButton(text=opt[:30], callback_data=f"page:{opt}")]
            for opt in options
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            t(user_id, "multiple").format(html.escape(query)),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except wikipedia.PageError:
        logger.info(f"Page not found for query: {query}, searching suggestions")
        results = wikipedia.search(query, results=MAX_RESULTS)

        if not results:
            logger.warning(f"No results found for query: {query}")
            await message.answer(t(user_id, "not_found"))
            return

        buttons = [
            [InlineKeyboardButton(text=r[:40], callback_data=f"page:{r}")]
            for r in results
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            t(user_id, "suggest"),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except wikipedia.exceptions.WikipediaException as e:
        logger.error(f"Wikipedia error for query '{query}': {str(e)}")
        await message.answer(
            t(user_id, "error").format(html.escape(str(e))),
            parse_mode="HTML"
        )


# ─── ARTICLE DISPLAY ────────────────────────────────

async def send_article(
        target: types.Message | types.CallbackQuery,
        page: wikipedia.WikipediaPage,
        user_id: int
):
    """
    Send Wikipedia article to user.

    Args:
        target: Message or CallbackQuery object
        page: Wikipedia page object
        user_id: Telegram user ID
    """
    title = html.escape(page.title)
    summary = html.escape(page.summary[:MAX_SUMMARY_LENGTH])

    if len(page.summary) > MAX_SUMMARY_LENGTH:
        summary += "..."

    text = (
        f"📖 <b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"🔗 <a href='{page.url}'>{t(user_id, 'read_more')}</a>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(user_id, "random_btn"), callback_data="random")],
        [InlineKeyboardButton(text=t(user_id, "change_lang"), callback_data="show_lang")]
    ])

    if isinstance(target, types.Message):
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ─── CALLBACK HANDLERS ───────────────────────────────

@dp.callback_query(F.data.startswith("lang:"))
async def on_lang_select(callback: types.CallbackQuery):
    """Handle language selection from inline keyboard."""
    user_id = callback.from_user.id
    lang_code = callback.data.replace("lang:", "")

    user_prefs.set_lang(user_id, lang_code)
    lang_name = LANGUAGES.get(lang_code, lang_code)

    await callback.answer()
    await callback.message.edit_text(
        t(user_id, "lang_set").format(lang_name),
        parse_mode="HTML"
    )
    logger.info(f"User {user_id} changed language to {lang_code}")


@dp.callback_query(F.data.startswith("page:"))
async def on_page_select(callback: types.CallbackQuery):
    """Handle page selection from search results."""
    user_id = callback.from_user.id
    title = callback.data.replace("page:", "")

    await callback.answer(t(user_id, "loading"))

    lang = user_prefs.get_lang(user_id)
    wikipedia.set_lang(lang)

    try:
        page = wikipedia.page(title, auto_suggest=False)
        await send_article(callback, page, user_id)
        logger.info(f"User {user_id} opened page: {title}")

    except wikipedia.exceptions.WikipediaException as e:
        logger.error(f"Error loading page '{title}': {str(e)}")
        await callback.message.edit_text(
            t(user_id, "error").format(html.escape(str(e))),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "random")
async def on_random(callback: types.CallbackQuery):
    """Handle random article generation."""
    user_id = callback.from_user.id
    await callback.answer(t(user_id, "random_loading"))

    lang = user_prefs.get_lang(user_id)
    wikipedia.set_lang(lang)

    try:
        random_page = wikipedia.random(pages=1)[0]
        page = wikipedia.page(random_page, auto_suggest=False)
        await send_article(callback, page, user_id)
        logger.info(f"User {user_id} opened random article: {random_page}")

    except wikipedia.exceptions.WikipediaException as e:
        logger.error(f"Error loading random article: {str(e)}")
        await callback.message.edit_text(
            t(user_id, "error").format(html.escape(str(e))),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "show_lang")
async def on_show_lang(callback: types.CallbackQuery):
    """Handle language selection button."""
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.edit_text(
        t(user_id, "choose_lang"),
        reply_markup=lang_keyboard(),
        parse_mode="HTML"
    )


# ─── MAIN ENTRY POINT ───────────────────────────────

async def main():
    """Start the bot."""
    logger.info("Starting WikiBot...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")