import json
import os
from typing import Dict, Any
import logging

DATA_FILE = "data/users.json"

def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

def load_users() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users_data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_dir(DATA_FILE)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

def get_user_data(user_id: str) -> Dict[str, Any]:
    return load_users().get(user_id, {})

def update_user_data(user_id: str, new_data: Dict[str, Any]) -> None:
    """
    Обновляет данные пользователя с МЕРДЖЕМ (не перезатирая существующие ключи).
    Пример: было {"age": 25, "gender": "male"}, пришло {"budget": 50000} →
            станет {"age": 25, "gender": "male", "budget": 50000}
    """
    all_users = load_users()
    current = all_users.get(user_id, {})
    if not isinstance(current, dict):
        current = {}

    # Убираем None-значения, чтобы не затирать данные пустыми полями
    clean_data = {k: v for k, v in (new_data or {}).items() if v is not None}

    # Обновляем только нужные поля
    current.update(clean_data)

    all_users[user_id] = current
    save_users(all_users)

    # Для отладки (необязательно, но помогает понять что сохраняется)
    logging.info(f"✅ Данные пользователя {user_id} обновлены: {clean_data}")
