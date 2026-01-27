# utils/profile_mapping.py
from typing import Dict

def map_state_to_ru_profile(data: Dict) -> Dict:
    """
    Преобразует данные пользователя из состояния FSM в удобный вид для профиля.
    """

    # возраст
    try:
        age = int(data.get("age") or 0)
    except (TypeError, ValueError):
        age = 0

    # пол
    g = data.get("gender")
    sex = None
    if g in ("male", "m", "мужчина"):
        sex = "м"
    elif g in ("female", "f", "женщина"):
        sex = "ж"

    # транспорт
    t = data.get("transport_type") or data.get("transport")
    transport_map = {
        "public": "общественный транспорт",
        "taxi": "такси",
        "car": "своя машина",
        "driver": "водитель",
        # запасные варианты
        "transport_public": "общественный транспорт",
        "transport_car": "своя машина",
        "transport_taxi": "такси",
        "transport_driver": "водитель",
        "Езжу на такси": "такси",
        "Езжу с водителем": "водитель",
    }
    transport = transport_map.get(t, None)

    # жильё
    h = data.get("housing_type") or data.get("housing")
    housing_map = {
        "parents": "с_родителями",
        "dorm": "общежитие",
        "rent": "снимает",
        "own": "своя",
        # запасные
        "housing_parents": "с_родителями",
        "housing_dorm": "общежитие",
        "housing_rent": "снимает",
        "housing_own": "своя",
    }
    housing = housing_map.get(h, None)

    # семейное положение
    s = data.get("family_status") or data.get("status")
    status_map = {
        "single": "одинокий",
        "relationship": "в отношениях",
        "married": "женат / замужем",
        "divorced": "в разводе",
        # запасные
        "family_single": "одинокий",
        "family_relationship": "в отношениях",
        "family_married": "женат / замужем",
        "family_divorced": "в разводе",
    }
    status = status_map.get(s, None)

    # дети
    c = data.get("children_type") or data.get("children")
    if c in ("yes", "children_yes", "1", "true", True):
        kids = 1
    else:
        kids = 0

    # алименты
    a = data.get("alimony_type") or data.get("alimony")
    pays_alimony = a in ("yes", "alimony_yes", "1", "true", True)

    # ипотека (если когда-то появится)
    mortgage = bool(data.get("mortgage", False))

    # бюджет
    try:
        budget_val = int(data.get("budget")) if data.get("budget") is not None else None
    except (TypeError, ValueError):
        budget_val = None

    # уровень бюджета
    if budget_val is None:
        budget_level = None
    elif budget_val < 40000:
        budget_level = "низкий"
    elif budget_val > 150000:
        budget_level = "высокий"
    else:
        budget_level = "средний"

    # итоговая структура
    return {
        "age": age,
        "sex": sex,
        "transport": transport,
        "housing": housing,
        "status": status,
        "kids": kids,
        "pays_alimony": pays_alimony,
        "mortgage": mortgage,
        "budget_level": budget_level,
    }
