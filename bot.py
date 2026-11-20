import os
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote
import re

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

AVITO_LINK = "https://www.avito.ru/chelyabinsk/vakansii?q=оператор+пк&experience=1"
RABOTA_LINK = "https://www.rabota.ru/vacancy/?query=оператор+пк&city=chelyabinsk&experience=noExperience"

# Твои профессии
PROFESSIONS = [
    "оператор пк",
    "оператор чата",
    "чат поддержка",
    "специалист поддержки",
    "дизайнер инфографики",
    "дизайнер карточек",
    "модератор чата",
    "оператор колл центра",
]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        resp = requests.post(url, data=payload, timeout=15)
        print(f"Отправка в TG: {resp.status_code}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def get_hh_rss(url, label):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml"
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        print(f"RSS {label} -> статус {r.status_code}")
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
        print(f"RSS {label} -> найдено {len(items)}")
        return items
    except Exception as e:
        print(f"Ошибка RSS {label}: {e}")
        return []

def job():
    all_vac = []
    seen = set()

    # Проходим по каждой профессии: сначала Челябинск, потом удалёнка
    for prof in PROFESSIONS:
        # Челябинск, без опыта, по профессии
        url_chel = f"https://hh.ru/search/vacancy/rss?area=104&experience=noExperience&text={quote(prof)}&order_by=publication_time"
        for v in get_hh_rss(url_chel, f"{prof} - Челябинск"):
            if v["link"] not in seen:
                seen.add(v["link"])
                all_vac.append(v)

        # Удалёнка, без опыта, по профессии
        url_remote = f"https://hh.ru/search/vacancy/rss?area=113&experience=noExperience&schedule=flexible&text={quote(prof)}&order_by=publication_time"
        for v in get_hh_rss(url_remote, f"{prof} - Удалёнка"):
            if v["link"] not in seen:
                seen.add(v["link"])
                all_vac.append(v)

        if len(all_vac) >= 5:
            break

    print(f"Итого собрано: {len(all_vac)}")

    if not all_vac:
        send_telegram("⚠️ Бот работает, но по твоим профессиям сейчас ничего свежего. Запусти ещё раз через 1 час.")
        return

    send_telegram(f"🔥 <b>Вакансии по твоим профессиям: {len(all_vac[:5])} шт.</b>\n💻 Оператор ПК | 💬 Чат-поддержка | 🎨 Дизайнер инфографики\n📍 Челябинск + удалёнка, без опыта")
    for v in all_vac[:5]:
        msg = (
            f"💼 <b>{v['title']}</b>\n"
            f"{v['desc']}\n"
            f"🔗 <a href='{v['link']}'>Откликнуться на HH</a>"
        )
        send_telegram(msg)
        time.sleep(1)

    send_telegram(
        f"📋 <b>Ещё по твоим профессиям:</b>\n"
        f"🔗 <a href='{AVITO_LINK}'>Avito — Оператор ПК, Челябинск</a>\n"
        f"🔗 <a href='{RABOTA_LINK}'>Работа.ру — Оператор ПК, Челябинск</a>"
    )

if __name__ == "__main__":
    print("Бот запущен - по профессиям: оператор ПК, чат-поддержка, дизайнер")
    job()
    print("Готово.")
