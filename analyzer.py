import os
import requests

print("--- Запуск скрипта анализа звонков ---")

# Шаг 1: Чтение секретов из окружения
telfin_app_id = os.getenv("TELFIN_APP_ID")
telfin_app_secret = os.getenv("TELFIN_APP_SECRET")

if not telfin_app_id or not telfin_app_secret:
    print("❌ Ошибка: Не найдены TELFIN_APP_ID или TELFIN_APP_SECRET.")
    exit(1)

print(f"Используем App ID: {telfin_app_id[:4]}...{telfin_app_id[-4:]}")

# Шаг 2: Авторизация в Телфин
print("Попытка авторизации в Телфин...")

session = requests.Session()

try:
    response = session.post(
        "https://apiproxy.telphin.ru/api/ver1.0/oauth/token",
        data={
            "client_id": telfin_app_id,
            "client_secret": telfin_app_secret,
            "grant_type": "client_credentials",
        },
        timeout=(10, 30)
    )

    # Шаг 3: Проверка результата
    if response.status_code == 200:
        try:
            response_data = response.json()
            token = response_data.get("access_token")
            if token:
                print(f"✅ Успешная авторизация! Получен токен: {token[:8]}...")
            else:
                print("❌ Ошибка: Токен не найден в ответе сервера")
        except ValueError as e:
            print(f"❌ Ошибка парсинга JSON ответа: {e}")
    else:
        print(f"❌ Ошибка авторизации в Телфин!")
        print(f"Статус-код: {response.status_code}")
        print(f"Ответ сервера: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Критическая ошибка сети: {e}")

finally:
    if 'session' in locals():
        session.close()

print("--- Скрипт завершил работу ---")
