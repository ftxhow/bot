# utils/budget.py
from typing import Dict

BASE: Dict[str, float] = {
    "Жильё": 25, "Транспорт": 10, "Питание": 20, "Коммуналка/связь": 7,
    "Здоровье": 5, "Кредиты": 8, "Сбережения": 15, "Досуг": 10,
    "Дети": 0, "Алименты": 0
}

def clamp_nonneg(d: Dict[str, float]) -> Dict[str, float]:
    for k, v in d.items():
        if k != "Алименты" and v < 0:
            d[k] = 0.0
    return d

def normalize_except_alimony(d: Dict[str, float]) -> Dict[str, float]:
    al = float(d.get("Алименты", 0.0))
    rest_keys = [k for k in d.keys() if k != "Алименты"]
    s = sum(float(d[k]) for k in rest_keys)
    if s <= 0:
        d["Досуг"] = max(0.0, 100.0 - al)
        s = sum(float(d[k]) for k in rest_keys)
    factor = (100.0 - al) / s if s > 0 else 1.0
    for k in rest_keys:
        d[k] = float(d[k]) * factor
    d["Алименты"] = al
    return d

def enforce_hard_constraints(profile: Dict, d: Dict[str, float]) -> Dict[str, float]:
    age = int(profile.get("age") or 0)
    housing = profile.get("housing")               # "с_родителями" | "общежитие" | "снимает" | "своя"
    transport = profile.get("transport")           # "общественный" | "такси" | "своя_машина" | "водитель"
    kids = int(profile.get("kids") or 0)
    mortgage = bool(profile.get("mortgage"))
    pays_alimony = bool(profile.get("pays_alimony"))

    # 1) <18: кредиты в 0, ипотеку игнорируем
    if age < 18:
        d["Кредиты"] = 0.0
        mortgage = False

    # 2) Жильё
    if housing == "с_родителями":
        d["Жильё"] = 0.0
        d["Коммуналка/связь"] = 0.0
    elif housing == "общежитие":
        d["Жильё"] = min(d["Жильё"], 8.0)
        d["Коммуналка/связь"] = min(d["Коммуналка/связь"], 3.0)
    elif housing == "снимает":
        d["Жильё"] = max(d["Жильё"], 20.0)
        d["Коммуналка/связь"] = max(d["Коммуналка/связь"], 6.0)
    elif housing == "своя":
        if not mortgage:
            d["Жильё"] = min(d["Жильё"], 15.0)
        else:
            d["Кредиты"] = max(d["Кредиты"], 10.0)

    # 3) Транспорт: пороги
    if transport == "общественный":
        d["Транспорт"] = min(d["Транспорт"], 8.0)
    elif transport == "такси":
        d["Транспорт"] = max(d["Транспорт"], 12.0)
    elif transport == "своя_машина":
        d["Транспорт"] = max(d["Транспорт"], 14.0)
    elif transport == "водитель":
        d["Транспорт"] = max(d["Транспорт"], 18.0)

    # 4) Дети: 0 → обнуляем «Дети»
    if kids == 0:
        d["Дети"] = 0.0

    # 5) Алименты: фиксированный процент
    if pays_alimony:
        if kids == 1:
            d["Алименты"] = 20.0
        elif kids == 2:
            d["Алименты"] = 33.0
        elif kids >= 3:
            d["Алименты"] = 50.0
        else:
            d["Алименты"] = max(d.get("Алименты", 0.0), 10.0)
    else:
        d["Алименты"] = 0.0

    return d

def apply_modifiers(profile: Dict) -> Dict[str, float]:
    """мягкие модификаторы + жёсткие правила + нормализация"""
    d = BASE.copy()

    age = int(profile.get("age") or 0)
    # Возраст (мягко)
    if 18 <= age <= 24:
        d["Досуг"] += 3; d["Сбережения"] -= 3
    elif 25 <= age <= 34:
        d["Кредиты"] += 2; d["Сбережения"] -= 2
    elif 35 <= age <= 44:
        if int(profile.get("kids") or 0) > 0: d["Дети"] += 3
        d["Досуг"] -= 2; d["Сбережения"] += 1
    elif 45 <= age <= 54:
        d["Здоровье"] += 2; d["Сбережения"] += 2; d["Досуг"] -= 2
    elif age >= 55:
        d["Здоровье"] += 3; d["Досуг"] -= 2; d["Транспорт"] -= 1

    # Пол (м/ж — небольшие поправки)
    sex = profile.get("sex")
    if sex == "м":
        d["Досуг"] += 1; d["Здоровье"] -= 1
    elif sex == "ж":
        d["Здоровье"] += 1; d["Досуг"] -= 1

    # Транспорт (мягко)
    t = profile.get("transport")
    if t == "такси":
        d["Транспорт"] += 4; d["Сбережения"] -= 2; d["Досуг"] -= 2
    elif t == "общественный":
        d["Транспорт"] -= 2; d["Сбережения"] += 1
    elif t == "своя_машина":
        d["Транспорт"] += 4; d["Сбережения"] -= 2
    elif t == "водитель":
        d["Транспорт"] += 7; d["Досуг"] -= 3; d["Сбережения"] -= 4

    # Жильё (мягко)
    h = profile.get("housing")
    if h == "с_родителями":
        d["Жильё"] -= 15; d["Коммуналка/связь"] -= 4; d["Сбережения"] += 8; d["Досуг"] += 4; d["Питание"] += 2
    elif h == "общежитие":
        d["Жильё"] -= 10; d["Коммуналка/связь"] -= 3; d["Сбережения"] += 5; d["Питание"] += 2; d["Досуг"] += 2
    elif h == "снимает":
        d["Жильё"] += 10; d["Коммуналка/связь"] += 2; d["Сбережения"] -= 6
    elif h == "своя":
        d["Жильё"] -= 3; d["Сбережения"] += 2
        if bool(profile.get("mortgage")):
            d["Кредиты"] += 8

    # Семейное положение
    s = profile.get("status")
    if s == "одинокий":
        d["Досуг"] += 2; d["Сбережения"] += 1
    elif s == "в_отношениях":
        d["Питание"] += 2; d["Досуг"] -= 1
    elif s == "женат_замужем":
        d["Питание"] += 2; d["Коммуналка/связь"] += 1; d["Сбережения"] -= 2
    elif s == "в_разводе":
        d["Сбережения"] -= 2; d["Досуг"] -= 1

    # Дети (мягко)
    k = int(profile.get("kids") or 0)
    if k == 1:
        d["Дети"] += 7; d["Досуг"] -= 3; d["Сбережения"] -= 2
    elif k == 2:
        d["Дети"] += 12; d["Досуг"] -= 5; d["Сбережения"] -= 3
    elif k == 3:
        d["Дети"] += 16; d["Досуг"] -= 6; d["Сбережения"] -= 4
    elif k > 3:
        d["Дети"] += 20; d["Досуг"] -= 8; d["Сбережения"] -= 5

    # Уровень бюджета
    bud = profile.get("budget_level")  # "низкий" | "средний" | "высокий" | None
    if bud == "низкий":
        d["Сбережения"] -= 3; d["Питание"] += 2
    elif bud == "высокий":
        d["Сбережения"] += 3; d["Досуг"] += 1

    # Жёсткие правила
    d = enforce_hard_constraints(profile, d)

    # Нормализация и округление
    d = clamp_nonneg(d)
    d = normalize_except_alimony(d)

    for k2 in d:
        d[k2] = round(d[k2], 1)
    diff = round(100.0 - sum(d.values()), 1)
    if abs(diff) >= 0.1:
        if "Досуг" in d:
            d["Досуг"] = round(d["Досуг"] + diff, 1)
        else:
            d["Сбережения"] = round(d["Сбережения"] + diff, 1)
    return d
