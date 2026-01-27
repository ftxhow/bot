import os

# Читаем токен из переменной окружения (Replit Secrets)
TOKEN = os.getenv("BOT_TOKEN")

# Если токен не найден, проверяем файл .env (для локальной разработки)
if not TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        TOKEN = os.getenv("BOT_TOKEN")
    except ImportError:
        pass

# Если всё ещё нет токена, выдаём ошибку
if not TOKEN:
    raise ValueError(
        "❌ Токен бота не найден!\n"
        "Для Replit: добавьте BOT_TOKEN в Secrets (🔒)\n"
        "Для локальной разработки: создайте файл .env с BOT_TOKEN=ваш_токен"
    )
