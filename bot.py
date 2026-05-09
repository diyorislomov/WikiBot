# src/bot.py
import asyncio
import logging
import html
import wikipedia
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN  # ← faqat shu yetarli!

# ... qolgan kod o'zgarishsiz ...

# ─── SOZLAMLAR ──────────────────────────────────────


# Mavjud tillar
LANGUAGES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

# Foydalanuvchi tillari (xotira)
user_langs = {}

# ─── TAYYORGARLIK ───────────────────────────────────
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_lang(user_id: int) -> str:
    return user_langs.get(user_id, "uz")


def set_lang(user_id: int, lang: str):
    user_langs[user_id] = lang


def t(user_id: int, key: str) -> str:
    """Tarjima funksiyasi"""
    lang = get_lang(user_id)
    texts = {
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
        },
    }
    return texts.get(lang, texts["uz"]).get(key, key)


def lang_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
        for code, name in LANGUAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── HANDLERLAR ─────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(t(message.from_user.id, "welcome"), parse_mode="HTML")


@dp.message(Command("lang"))
async def cmd_lang(message: types.Message):
    await message.answer(
        t(message.from_user.id, "choose_lang"),
        reply_markup=lang_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("lang:"))
async def on_lang_select(callback: types.CallbackQuery):
    lang_code = callback.data.replace("lang:", "")
    set_lang(callback.from_user.id, lang_code)
    lang_name = LANGUAGES.get(lang_code, lang_code)
    await callback.answer()
    await callback.message.edit_text(
        t(callback.from_user.id, "lang_set").format(lang_name),
        parse_mode="HTML"
    )


@dp.message(Command("wiki"))
async def cmd_wiki(message: types.Message):
    query = message.text.replace("/wiki", "").strip()
    if not query:
        await message.answer(t(message.from_user.id, "usage"), parse_mode="HTML")
        return
    await search_wiki(message, query)


@dp.message()
async def text_search(message: types.Message):
    await search_wiki(message, message.text)


async def search_wiki(message: types.Message, query: str):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    wikipedia.set_lang(lang)

    try:
        page = wikipedia.page(query, auto_suggest=True)
        await send_article(message, page)

    except wikipedia.DisambiguationError as e:
        options = e.options[:8]
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
        results = wikipedia.search(query, results=5)
        if not results:
            await message.answer(t(user_id, "not_found"))
            return

        buttons = [
            [InlineKeyboardButton(text=r[:40], callback_data=f"page:{r}")]
            for r in results
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(t(user_id, "suggest"), reply_markup=keyboard, parse_mode="HTML")


async def send_article(target, page: wikipedia.WikipediaPage):
    user_id = target.from_user.id if isinstance(target, types.CallbackQuery) else target.from_user.id

    title = html.escape(page.title)
    summary = html.escape(page.summary[:3500])
    if len(page.summary) > 3500:
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


@dp.callback_query(F.data.startswith("page:"))
async def on_page_select(callback: types.CallbackQuery):
    title = callback.data.replace("page:", "")
    await callback.answer(t(callback.from_user.id, "loading"))

    lang = get_lang(callback.from_user.id)
    wikipedia.set_lang(lang)

    try:
        page = wikipedia.page(title, auto_suggest=False)
        await send_article(callback, page)
    except Exception as e:
        await callback.message.edit_text(
            t(callback.from_user.id, "error").format(html.escape(str(e))),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "random")
async def on_random(callback: types.CallbackQuery):
    await callback.answer(t(callback.from_user.id, "random_loading"))

    lang = get_lang(callback.from_user.id)
    wikipedia.set_lang(lang)

    try:
        page = wikipedia.random(pages=1)[0]
        page_obj = wikipedia.page(page, auto_suggest=False)
        await send_article(callback, page_obj)
    except Exception as e:
        await callback.message.edit_text(
            t(callback.from_user.id, "error").format(html.escape(str(e))),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "show_lang")
async def on_show_lang(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        t(callback.from_user.id, "choose_lang"),
        reply_markup=lang_keyboard(),
        parse_mode="HTML"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())