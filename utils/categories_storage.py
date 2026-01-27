# utils/categories_storage.py
import json
import os

CATEGORIES_FILE = "data/categories.json"


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


def _load():
    if not os.path.exists(CATEGORIES_FILE):
        return {}
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _save(data: dict):
    _ensure_dir()
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def update_category_balance(user_id: str, category: str, amount: float):
    """
    Обновляет (добавляет/уменьшает) сумму по категории.
    Пример: update_category_balance('123', 'Питание', -300)
    """
    data = _load()
    if user_id not in data:
        data[user_id] = {}
    data[user_id][category] = round(data[user_id].get(category, 0) + amount, 2)
    _save(data)


def get_user_categories(user_id: str):
    """Возвращает словарь категорий и сумм для конкретного пользователя"""
    data = _load()
    return data.get(user_id, {})
