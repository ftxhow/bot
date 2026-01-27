from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.keyboards import main_menu_keyboard

def _fmt_user_data(data: dict) -> str:
    if not data:
        return "Пока данных нет. Пройдите анкету."
    
    # Словари для перевода значений
    GENDER_MAP = {
        "male": "Мужской", 
        "female": "Женский", 
        "other": "Другое",
        "м": "Мужской", 
        "ж": "Женский",
        "m": "Мужской",
        "f": "Женский",
        "мужчина": "Мужской",
        "женщина": "Женский",
    }
    TRANSPORT_MAP = {
        "public": "Общественный транспорт", 
        "transport_public": "Общественный транспорт",
        "taxi": "Такси", 
        "transport_taxi": "Такси",
        "car": "Своя машина", 
        "transport_car": "Своя машина",
        "driver": "Личный водитель", 
        "transport_driver": "Личный водитель",
        "общественный транспорт": "Общественный транспорт",
        "своя машина": "Своя машина",
        "личный водитель": "Личный водитель",
    }
    HOUSING_MAP = {
        "own": "Своё жильё", 
        "housing_own": "Своё жильё",
        "rent": "Аренда", 
        "housing_rent": "Аренда",
        "parents": "С родителями", 
        "housing_parents": "С родителями",
        "dorm": "Общежитие", 
        "housing_dorm": "Общежитие",
        "своё жильё": "Своё жильё",
        "аренда": "Аренда",
        "с родителями": "С родителями",
        "общежитие": "Общежитие",
    }
    FAMILY_MAP = {
        "single": "Холост/Не замужем", 
        "family_single": "Холост/Не замужем",
        "relationship": "В отношениях", 
        "family_relationship": "В отношениях",
        "married": "Женат/Замужем", 
        "family_married": "Женат/Замужем",
        "divorced": "В разводе", 
        "family_divorced": "В разводе",
        "одинокий": "Холост/Не замужем",
        "в отношениях": "В отношениях",
        "женат / замужем": "Женат/Замужем",
        "в разводе": "В разводе",
    }
    CHILDREN_MAP = {
        "yes": "Есть", 
        "children_yes": "Есть",
        "no": "Нет", 
        "children_no": "Нет",
        "да": "Есть",
        "нет": "Нет",
        "1": "Есть",
        "0": "Нет",
    }
    
    lines = []
    
    # Порядок полей с эмодзи
    fields = [
        ("name", "🧑‍💼 Имя"),
        ("nickname", "🧑‍💼 Ник"),
        ("age", "🎂 Возраст"),
        ("budget", "💰 Бюджет"),
        ("gender", "👤 Пол"),
        ("transport_type", "🚶 Транспорт"),
        ("housing_type", "🏠 Жильё"),
        ("family_status", "❤️ Статус"),
        ("children_type", "👶 Дети"),
        ("credit_amount", "💳 Кредит"),
        ("alimony_amount", "✍️ Алименты"),
    ]
    
    for key, title in fields:
        if key in data and data[key] is not None:
            val = data[key]
            
            # Переводим значения
            if key == "gender":
                val = GENDER_MAP.get(str(val).lower(), val)
            elif key == "transport_type":
                val = TRANSPORT_MAP.get(str(val).lower(), val)
            elif key == "housing_type":
                val = HOUSING_MAP.get(str(val).lower(), val)
            elif key == "family_status":
                val = FAMILY_MAP.get(str(val).lower(), val)
            elif key == "children_type":
                val = CHILDREN_MAP.get(str(val).lower(), val)
            # Форматируем суммы
            elif key in ("credit_amount", "alimony_amount", "budget") and isinstance(val, (int, float)):
                if val == 0 and key != "budget":
                    val = "Нет"
                else:
                    val = f"{val:,.0f} ₽".replace(",", " ")
            
            # Экранируем специальные символы Markdown
            val_str = str(val)
            # Не экранируем эмодзи в title, только значение
            lines.append(f"{title}: {val_str}")
    
    return "📋 Ваши данные:\n\n" + ("\n".join(lines) if lines else "—")

def _escape_markdown(text: str) -> str:
    """Экранирует специальные символы Markdown."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def send_summary(
    target: Message | CallbackQuery,
    state: FSMContext,
    show_menu: bool = False,
    reply_markup=None
):
    """
    Универсальная функция: принимает либо Message, либо CallbackQuery.
    Отправляет сводку данных пользователя. Если show_menu=True — добавляет главное меню.
    """
    # Нормализуем объект для отправки сообщений
    if isinstance(target, CallbackQuery):
        msg = target.message
    else:
        msg = target

    data = await state.get_data()
    text = _fmt_user_data(data)

    # Если явно передали reply_markup — используем его; иначе по флагу show_menu
    if reply_markup is not None:
        await msg.answer(text, reply_markup=reply_markup)
    elif show_menu:
        await msg.answer(text, reply_markup=main_menu_keyboard)
    else:
        await msg.answer(text)


