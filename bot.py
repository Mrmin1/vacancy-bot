import os
import requests
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Челябинск - area 104 в HH
# Ссылки с фильтрами: Челябинск + без опыта
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

def get_hh(params, label):
    url = "https://api.hh.ru/vacancies"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        print(f"HH {label} -> статус {r.status_code}")
        items = r.json().get("items", [])
        print(f"HH {label} -> найдено {len(items)}")
        return items
    except Exception as e:
        print(f"Ошибка HH {label}: {e}")
        return []

def format_vac(v):
    name = v.get("name", "Без названия")
    salary = v.get("salary")
    if salary:
        s_from = salary.get("from") or ""
        s_to = salary.get("to") or ""
        currency = salary.get("currency", "RUR")
        if s_from and s_to:
            sal = f"{s_from}-{s_to} ₽"
        elif s_from:
            sal = f"от {s_from} ₽"
        elif s_to:
            sal = f"до {s_to} ₽"
        else:
            sal = "не указана"
    else:
        sal = "не указана"
    employer = v.get("employer", {}).get("name", "")
    area = v.get("area", {}).get("name", "")
    exp = v.get("experience", {}).get("name", "")
    schedule = v.get("schedule", {}).get("name", "")
    link = v.get("alternate_url", "")
    return (
        f"💼 <b>{name}</b>\n"
        f"🏢 {employer} | 📍 {area}\n"
        f"💰 {sal}\n"
        f"🧑‍💻 Опыт: {exp} | ⏰ {schedule}\n"
        f"🔗 <a href='{link}'>Откликнуться на HH</a>"
    )

def job():
    all_vac = []
    seen = set()

    # 1. Челябинск, без опыта, все свежие
    params_chel = {
        "area": 104,
        "experience": "noExperience",
        "per_page": 20,
        "page": 0,
        "order_by": "publication_time"
    }
    # 2. Удалёнка, без опыта, по всей России
    params_remote = {
        "area": 113,
        "experience": "noExperience",
        "schedule": "flexible",
        "per_page": 20,
        "page": 0,
        "order_by": "publication_time"
    }
    # 3. Удалёнка, без опыта, прямо по слову remote
    params_remote2 = {
        "area": 113,
        "experience": "noExperience",
        "text": "удаленно",
        "per_page": 20,
        "page": 0,
        "order_by": "publication_time"
    }

    for params, label in [
        (params_chel, "Челябинск без опыта"),
        (params_remote, "Удалёнка без опыта"),
        (params_remote2, "Удалёнка по слову"),
    ]:
        for v in get_hh(params, label):
            if v["id"] not in seen:
                seen.add(v["id"])
                all_vac.append(v)
        if len(all_vac) >= 5:
            break

    print(f"Итого собрано: {len(all_vac)}")

    if not all_vac:
        send_telegram("⚠️ Бот работает, но HH пока ничего не вернул. Запусти ещё раз через 5 минут.")
        return

    send_telegram(f"🔥 <b>Новые вакансии без опыта: {len(all_vac[:5])} шт.</b>\n📍 Челябинск + удалёнка")
    for v in all_vac[:5]:
        send_telegram(format_vac(v))
        time.sleep(1)

    send_telegram(
        f"📋 <b>Ещё вакансии без опыта:</b>\n"
        f"🔗 <a href='{AVITO_LINK}'>Avito — Челябинск, без опыта</a>\n"
        f"🔗 <a href='{RABOTA_LINK}'>Работа.ру — Челябинск, без опыта</a>"
    )

if __name__ == "__main__":
    print("Бот запущен - Челябинск + удалёнка, без опыта")
    job()
    print("Готово.")
