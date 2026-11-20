import os
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

AVITO_LINK = "https://www.avito.ru/chelyabinsk/vakansii?experience=1"
RABOTA_LINK = "https://www.rabota.ru/vacancy/?query=&city=chelyabinsk&experience=noExperience"

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
        print(f"RSS {label} -> статус {r.status_code}, длина {len(r.text)}")
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            pub = item.findtext("pubDate", "")
            # Чистим описание от HTML
            import re
            desc_clean = re.sub(r"<[^>]+>", "", desc)[:250]
            items.append({"title": title, "link": link, "desc": desc_clean, "pub": pub})
        print(f"RSS {label} -> найдено {len(items)}")
        return items
    except Exception as e:
        print(f"Ошибка RSS {label}: {e}")
        return []

def job():
    all_vac = []
    seen = set()

    # 1. Челябинск, без опыта
    url1 = "https://hh.ru/search/vacancy/rss?area=104&experience=noExperience&order_by=publication_time"
    # 2. Удалёнка, без опыта
    url2 = "https://hh.ru/search/vacancy/rss?area=113&experience=noExperience&schedule=flexible&order_by=publication_time"
    # 3. Удалёнка по слову
    url3 = "https://hh.ru/search/vacancy/rss?area=113&experience=noExperience&text=" + quote("удаленно") + "&order_by=publication_time"

    for url, label in [(url1, "Челябинск"), (url2, "Удалёнка"), (url3, "Удалёнка по слову")]:
        for v in get_hh_rss(url, label):
            if v["link"] not in seen:
                seen.add(v["link"])
                all_vac.append(v)
        if len(all_vac) >= 5:
            break

    print(f"Итого собрано: {len(all_vac)}")

    if not all_vac:
        send_telegram("⚠️ Бот работает, но HH RSS пока ничего не вернул. Запусти ещё раз через 5 минут.")
        return

    send_telegram(f"🔥 <b>Новые вакансии без опыта: {len(all_vac[:5])} шт.</b>\n📍 Челябинск + удалёнка")
    for v in all_vac[:5]:
        msg = (
            f"💼 <b>{v['title']}</b>\n"
            f"{v['desc']}\n"
            f"🔗 <a href='{v['link']}'>Откликнуться на HH</a>"
        )
        send_telegram(msg)
        time.sleep(1)

    send_telegram(
        f"📋 <b>Ещё вакансии без опыта:</b>\n"
        f"🔗 <a href='{AVITO_LINK}'>Avito — Челябинск, без опыта</a>\n"
        f"🔗 <a href='{RABOTA_LINK}'>Работа.ру — Челябинск, без опыта</a>"
    )

if __name__ == "__main__":
    print("Бот запущен - RSS обход блокировки HH")
    job()
    print("Готово.")
