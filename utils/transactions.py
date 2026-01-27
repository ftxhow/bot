import json
import os
from datetime import datetime, timezone
from typing import Dict, List
from utils.categories_storage import update_category_balance

TX_FILE = "data/transactions.json"


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


def _load_all() -> Dict[str, List[dict]]:
    _ensure_dir()
    if not os.path.exists(TX_FILE):
        return {}
    try:
        with open(TX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _save_all(all_data: Dict[str, List[dict]]) -> None:
    _ensure_dir()
    with open(TX_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


def load_transactions(user_id: str) -> List[dict]:
    """Вернёт список транзакций конкретного пользователя из общего файла."""
    all_data = _load_all()
    return all_data.get(user_id, [])

def save_transactions(user_id: str, txs: List[dict]) -> None:
    """
    Сохраняет новые транзакции, ДОБАВЛЯЯ их к уже существующим.
    """
    all_data = _load_all()
    existing = all_data.get(user_id, [])
    # добавляем новые транзакции к старым
    existing.extend(txs)
    all_data[user_id] = existing
    _save_all(all_data)


def add_transaction(user_id: str, amount: float, description: str, category: str | None = None) -> None:
    """
    Добавляет 1 транзакцию пользователю и обновляет агрегаты по категориям.
    amount > 0 — доход, amount < 0 — расход.
    """
    all_data = _load_all()
    user_list = all_data.setdefault(user_id, [])

    tx = {
        "amount": float(amount),
        "desc": description,
        "category": category,
        "ts": datetime.now(timezone.utc).isoformat()
    }
    user_list.append(tx)
    _save_all(all_data)

    if category:
        update_category_balance(user_id, category, float(amount))


def add_transactions_batch(user_id: str, txs: List[dict], update_categories: bool = False) -> None:
    """
    Добавляет сразу несколько транзакций (например, из парсера свободного ввода).
    Если update_categories=True — обновит categories.json по каждой.
    Ожидаемый формат элементов txs: {"amount": float, "note": str|None, "category": str|None, "currency": "...", "ts": "...?"}
    (ts можно не задавать — проставим текущий)
    """
    all_data = _load_all()
    user_list = all_data.setdefault(user_id, [])

    now_iso = datetime.now(timezone.utc).isoformat()
    for t in txs:
        tx = {
            "amount": float(t["amount"]),
            "desc": t.get("note") or "",
            "category": t.get("category"),
            "ts": t.get("ts") or now_iso,
        }
        user_list.append(tx)
        if update_categories and tx["category"]:
            update_category_balance(user_id, tx["category"], float(tx["amount"]))

    _save_all(all_data)

def parse_transactions(text: str):
    """
    Парсит ввод пользователя и возвращает список транзакций.
    Поддерживает форматы:
    - '500 кофе' или '-500 кофе' 
    - 'кофе 500' или 'кофе -500'
    - 'купил кофе за 500'
    - '+130000 зп' (доход)
    """
    import re
    if not text:
        return []

    # Расширенный маппинг ключевых слов → категории
    CATEGORY_KEYWORDS = {
        # Питание
        "Питание": [
            "еда", "продукты", "магазин", "супермаркет", "пятёрочка", "пятерочка",
            "магнит", "перекрёсток", "перекресток", "ашан", "лента", "дикси",
            "кофе", "кафе", "ресторан", "обед", "завтрак", "ужин", "фастфуд",
            "макдональдс", "макдак", "бургер", "пицца", "суши", "роллы",
            "доставка еды", "яндекс еда", "delivery", "столовая", "буфет",
            "хлеб", "молоко", "мясо", "овощи", "фрукты", "вода", "напитки",
            "пиво", "вино", "алкоголь", "бар", "паб", "шаурма", "шашлык"
        ],
        # Транспорт
        "Транспорт": [
            "такси", "яндекс такси", "uber", "убер", "ситимобил", "метро",
            "автобус", "троллейбус", "трамвай", "маршрутка", "электричка",
            "поезд", "ржд", "бензин", "заправка", "азс", "топливо", "газ",
            "парковка", "мойка", "автомойка", "сто", "ремонт авто", "шиномонтаж",
            "каршеринг", "делимобиль", "яндекс драйв", "самокат", "велосипед"
        ],
        # Жильё
        "Жильё": [
            "аренда", "квартира", "съём", "съем", "жильё", "жилье", "ипотека",
            "коммуналка", "жкх", "электричество", "свет", "газ", "вода",
            "отопление", "капремонт", "интернет", "wifi", "ростелеком",
            "мтс", "билайн", "мегафон", "теле2", "связь", "телефон"
        ],
        # Одежда и обувь
        "Одежда": [
            "одежда", "обувь", "футболка", "джинсы", "куртка", "пальто",
            "платье", "юбка", "кроссовки", "ботинки", "сапоги", "шапка",
            "zara", "hm", "h&m", "uniqlo", "reserved", "gloria jeans",
            "спортмастер", "декатлон", "wildberries", "вб", "ozon", "озон"
        ],
        # Здоровье
        "Здоровье": [
            "аптека", "лекарство", "таблетки", "витамины", "врач", "доктор",
            "клиника", "больница", "стоматолог", "зубы", "анализы", "узи",
            "мрт", "рентген", "массаж", "терапевт", "операция", "медицина"
        ],
        # Красота
        "Красота": [
            "парикмахерская", "салон", "стрижка", "маникюр", "педикюр",
            "косметика", "крем", "шампунь", "косметолог", "спа", "солярий",
            "брови", "ресницы", "эпиляция", "барбершоп"
        ],
        # Развлечения
        "Досуг": [
            "кино", "театр", "концерт", "музей", "выставка", "клуб",
            "игра", "steam", "playstation", "xbox", "подписка", "netflix",
            "spotify", "яндекс музыка", "кинопоиск", "развлечения", "отдых",
            "парк", "аттракцион", "боулинг", "бильярд", "караоке", "квест"
        ],
        # Спорт
        "Спорт": [
            "спортзал", "фитнес", "тренажёрка", "тренажерка", "абонемент",
            "бассейн", "йога", "пилатес", "бокс", "теннис", "футбол"
        ],
        # Образование
        "Образование": [
            "курсы", "обучение", "книга", "книги", "учебник", "репетитор",
            "школа", "университет", "вуз", "колледж", "тренинг", "вебинар"
        ],
        # Подарки
        "Подарки": [
            "подарок", "подарки", "цветы", "букет", "сюрприз", "праздник",
            "день рождения", "др", "юбилей", "свадьба", "новый год"
        ],
        # Дети
        "Дети": [
            "детский", "ребёнок", "ребенок", "дети", "игрушка", "игрушки",
            "детский сад", "садик", "школа", "кружок", "секция", "няня"
        ],
        # Доход
        "Доход": [
            "зп", "зарплата", "аванс", "премия", "бонус", "фриланс",
            "подработка", "перевод", "возврат", "кэшбэк", "cashback",
            "дивиденды", "проценты", "доход", "получил", "заработал"
        ],
        # Переводы
        "Переводы": [
            "перевод", "сбп", "тинькофф", "сбер", "сбербанк", "альфа",
            "втб", "долг", "вернул", "одолжил", "занял"
        ],
    }

    # Создаём обратный маппинг: слово → категория
    word_to_category = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            word_to_category[keyword.lower()] = category

    results = []
    
    # Разделяем по запятой, точке с запятой или новой строке
    parts = re.split(r'[,;\n]+', text)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Ищем сумму в любом месте строки
        amount_match = re.search(r'([+-]?\d+(?:[.,]\d+)?)', part)
        if not amount_match:
            continue
        
        amount_str = amount_match.group(1).replace(',', '.')
        amount = float(amount_str)
        
        # Убираем сумму из текста, чтобы получить описание
        note = re.sub(r'[+-]?\d+(?:[.,]\d+)?', '', part).strip()
        note = re.sub(r'\s+', ' ', note)  # Убираем лишние пробелы
        
        # Очищаем от служебных слов
        for word in ['за', 'на', 'руб', 'рублей', 'р', '₽']:
            note = re.sub(rf'\b{word}\b', '', note, flags=re.IGNORECASE)
        note = note.strip()
        
        # Определяем категорию по ключевым словам
        category = None
        note_lower = note.lower()
        
        # Сначала пробуем найти полное совпадение
        for keyword, cat in word_to_category.items():
            if keyword in note_lower:
                category = cat
                break
        
        # Если категория "Доход", считаем сумму положительной
        if category == "Доход" and amount < 0:
            amount = abs(amount)
        
        # Если сумма положительная и нет знака, а категория не "Доход" - считаем расходом
        if amount > 0 and not amount_str.startswith('+'):
            if category != "Доход" and category != "Переводы":
                # Проверяем, есть ли ключевые слова дохода
                is_income = any(kw in note_lower for kw in word_to_category if word_to_category.get(kw) == "Доход")
                if not is_income:
                    amount = -amount
        
        # Если ничего не распознали, ставим "Прочее"
        if not category:
            category = "Прочее"
        
        results.append({
            "amount": amount,
            "note": note if note else category,
            "category": category,
            "currency": "RUB",
            "ts": datetime.now(timezone.utc).isoformat()
        })

    return results