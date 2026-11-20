import os
import requests
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CRITERIA = {
    "text": "дизайнер карточек монтажер",
    "area": 113,
    "salary_from": 10000,
    "per_hour": 5,
}

RABOTA_RU_LINK = "https://www.rabota.ru/vacancy/?query=дизайнер"
AVITO_LINK = "https://www.avito.ru/ufa/vakansii?q=дизайнер"

sent_ids = set()

def get_hh_vacancies():
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": CRITERIA["text"],
        "area": CRITERIA["area"],
        "salary": CRITERIA["salary_from"],
        "currency": "RUR",
        "per_page": 20,
        "page": 0,
        "order_by": "publication_time",
        "search_field": "name",
    }
    headers = {"User-Agent": "MyVacancyBot/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        return r.json().get("items", [])
    except Exception as e:
        print(f"Ошибка HH: {e}")
        return []

def format_vacancy(v):
    name = v.get("name", "Без названия")
    salary = v.get("salary")
    if salary:
        sal_from = salary.get("from") or 0
        sal_to = salary.get("to") or 0
        if sal_from and sal_to:
            sal_text = f"{sal_from} - {sal_to} ₽"
        elif sal_from:
            sal_text = f"от {sal_from} ₽"
        elif sal_to:
            sal_text = f"до {sal_to} ₽"
        else:
            sal_text = "Зарплата не указана"
    else:
        sal_text = "Зарплата не указана"
    employer = v.get("employer", {}).get("name", "")
    area = v.get("area", {}).get("name", "")
    schedule = v.get("schedule", {}).get("name", "") if v.get("schedule") else ""
    link = v.get("alternate_url", "")
    published = v.get("published_at", "")[:10]
    return (
        f"💼 <b>{name}</b>\n"
        f"🏢 {employer} | 📍 {area}\n"
        f"💰 {sal_text} | 🕒 {schedule}\n"
        f"📅 Опубликовано: {published}\n"
        f"🔗 <a href='{link}'>Откликнуться на HH</a>"
    )

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")

def job():
    vacancies = get_hh_vacancies()
    fresh = []
    for v in vacancies:
        if v["id"] not in sent_ids:
            fresh.append(v)
            sent_ids.add(v["id"])
        if len(fresh) >= CRITERIA["per_hour"]:
            break
    if not fresh:
        print("Новых вакансий нет")
        return
    send_telegram(f"🔥 <b>Новые вакансии за час: {len(fresh)} шт.</b>\nПо запросу: <i>{CRITERIA['text']}</i>")
    for v in fresh:
        send_telegram(format_vacancy(v))
        time.sleep(1)
    send_telegram(
        f"📋 <b>Ещё проверь вручную:</b>\n"
        f"🔗 <a href='{RABOTA_RU_LINK}'>Работа.ру - свежие вакансии</a>\n"
        f"🔗 <a href='{AVITO_LINK}'>Avito - свежие вакансии</a>"
    )

if __name__ == "__main__":
    print("Бот запущен - разовый запуск.")
    job()
