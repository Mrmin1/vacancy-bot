import os
import requests
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

RABOTA_RU_LINK = "https://www.rabota.ru/vacancy/?query=дизайнер"
AVITO_LINK = "https://www.avito.ru/ufa/vakansii?q=дизайнер"

def get_hh_vacancies(text):
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": text,
        "area": 113,
        "per_page": 20,
        "page": 0,
        "order_by": "publication_time",
    }
    headers = {"User-Agent": "MyVacancyBot/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        items = data.get("items", [])
        print(f"Запрос '{text}' -> найдено: {len(items)}")
        return items
    except Exception as e:
        print(f"Ошибка HH для '{text}': {e}")
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
    link = v.get("alternate_url", "")
    published = v.get("published_at", "")[:10]
    return (
        f"💼 <b>{name}</b>\n"
        f"🏢 {employer} | 📍 {area}\n"
        f"💰 {sal_text}\n"
        f"📅 {published}\n"
        f"🔗 <a href='{link}'>Откликнуться на HH</a>"
    )

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        resp = requests.post(url, data=payload, timeout=15)
        print(f"Отправка в TG: {resp.status_code}")
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")

def job():
    all_vac = []
    seen = set()
    # Пробуем 3 запроса по очереди, чтобы точно что-то нашлось
    for q in ["дизайнер карточек", "монтажер", "дизайнер"]:
        for v in get_hh_vacancies(q):
            if v["id"] not in seen:
                seen.add(v["id"])
                all_vac.append(v)
        if len(all_vac) >= 5:
            break

    print(f"Итого собрано вакансий: {len(all_vac)}")

    if not all_vac:
        send_telegram("⚠️ Бот работает, но HH сейчас ничего не вернул. Попробуй запустить ещё раз через 10 минут.")
        return

    send_telegram(f"🔥 <b>Новые вакансии: {len(all_vac[:5])} шт.</b>")
    for v in all_vac[:5]:
        send_telegram(format_vacancy(v))
        time.sleep(1)

    send_telegram(
        f"📋 <b>Ещё проверь:</b>\n"
        f"🔗 <a href='{RABOTA_RU_LINK}'>Работа.ру</a>\n"
        f"🔗 <a href='{AVITO_LINK}'>Avito</a>"
    )

if __name__ == "__main__":
    print("Бот запущен - разовый запуск.")
    job()
    print("Готово.")
