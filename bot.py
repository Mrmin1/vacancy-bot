import os
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Категории - только Челябинск, area=104
CATEGORIES = {
    "op_pk": {
        "name": "💻 Оператор ПК",
        "queries": ["оператор пк", "оператор ввода данных", "оператор базы данных"]
    },
    "chat": {
        "name": "💬 Чат-поддержка",
        "queries": ["оператор чата", "чат поддержка", "специалист поддержки", "оператор поддержки"]
    },
    "design": {
        "name": "🎨 Дизайнер инфографики",
        "queries": ["дизайнер инфографики", "дизайнер карточек", "дизайнер маркетплейсов"]
    },
    "moder": {
        "name": "🛡️ Модератор",
        "queries": ["модератор чата", "модератор", "модератор сообщества"]
    },
    "call": {
        "name": "📞 Оператор колл-центра",
        "queries": ["оператор колл центра", "оператор call центра"]
    },
    "all_chel": {
        "name": "📍 Все свежие в Челябинске",
        "queries": [""]  # без текста - все вакансии Челябинска без опыта
    },
}

def get_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    for key, cat in CATEGORIES.items():
        markup.add(InlineKeyboardButton(cat["name"], callback_data=f"cat_{key}"))
    return markup

def get_hh_rss(query):
    # Только Челябинск! area=104, без опыта
    if query == "":
        url = "https://hh.ru/search/vacancy/rss?area=104&experience=noExperience&order_by=publication_time"
    else:
        url = f"https://hh.ru/search/vacancy/rss?area=104&experience=noExperience&text={quote(query)}&order_by=publication_time"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml"
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            desc_clean = re.sub(r"<[^>]+>", "", desc)[:250]
            items.append({"title": title, "link": link, "desc": desc_clean})
        return items
    except:
        return []

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n\nВыбери категорию — пришлю 5 свежих вакансий\n📍 Только Челябинск, без опыта:",
        reply_markup=get_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def handle_category(call):
    key = call.data.replace("cat_", "")
    cat = CATEGORIES.get(key)
    if not cat:
        return

    bot.answer_callback_query(call.id, f"Ищу: {cat['name']}...")
    bot.send_message(call.message.chat.id, f"🔎 Ищу: <b>{cat['name']}</b>\n📍 Только Челябинск, без опыта...", parse_mode="HTML")

    all_vac = []
    seen = set()
    for q in cat["queries"]:
        for v in get_hh_rss(q):
            if v["link"] not in seen:
                seen.add(v["link"])
                all_vac.append(v)
        if len(all_vac) >= 5:
            break

    if not all_vac:
        bot.send_message(call.message.chat.id, "😔 По этой категории сейчас ничего свежего в Челябинске. Попробуй другую категорию.", reply_markup=get_keyboard())
        return

    bot.send_message(call.message.chat.id, f"🔥 <b>Нашёл {len(all_vac[:5])} вакансий:</b>", parse_mode="HTML")
    for v in all_vac[:5]:
        msg = f"💼 <b>{v['title']}</b>\n{v['desc']}\n🔗 <a href='{v['link']}'>Откликнуться на HH</a>"
        bot.send_message(call.message.chat.id, msg, parse_mode="HTML", disable_web_page_preview=True)
        time.sleep(0.5)

    bot.send_message(
        call.message.chat.id,
        "Выбери ещё категорию:",
        reply_markup=get_keyboard()
    )

if __name__ == "__main__":
    print("Бот с кнопками запущен - только Челябинск")
    bot.infinity_polling()
