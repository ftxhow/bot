import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter, Command
from handlers.profile import parse_budget_input

from states.user_state import UserState
from utils.storage import load_users, update_user_data
from utils.transactions import parse_transactions, save_transactions, load_transactions
from utils.eco import generate_eco_tips
from utils.budget import apply_modifiers
from keyboards.keyboards import (
    main_menu_keyboard,
    change_data_keyboard,
    transport_keyboard,
    housing_keyboard,
    family_status_keyboard,
    children_keyboard,
    alimony_keyboard,
    gender_keyboard,
)
from datetime import datetime, timezone

router = Router()

# ==========================================================
# Вспомогательные функции
# ==========================================================

def format_profile(profile):
    """
    Форматирует профиль пользователя для вывода.
    ВНИМАНИЕ: Это базовый пример. Поместите более сложную логику
    в отдельный файл, как utils/profile_mapping.py.
    """
    lines = [f"🧑‍💼 Имя: {profile.get('name', 'Не указано')}",
             f"🎂 Возраст: {profile.get('age', 'Не указан')}",
             f"💰 Бюджет: {profile.get('budget', 'Не указан')} ₽",
             f"🚶 Транспорт: {profile.get('transport', 'Не указан')}",
             f"🏠 Жилье: {profile.get('housing', 'Не указано')}",
             f"❤️ Статус: {profile.get('status', 'Не указан')}",
             f"👶 Дети: {'Есть' if profile.get('kids') else 'Нет'}",
             f"✍️ Алименты: {'Есть' if profile.get('pays_alimony') else 'Нет'}"]
    return "\n".join(lines)

async def send_summary(message: types.Message, state: FSMContext, show_menu=False):
    """Отправляет сводку профиля пользователя."""
    data = await state.get_data()
    # map_state_to_ru_profile - эта функция должна быть в utils.profile_mapping,
    # она должна маппить данные из FSM в русский словарь.
    profile = data # Предполагаем, что данные уже в нужном формате

    # Чтобы не сломать код, я делаю базовое форматирование.
    # Если у тебя есть функция map_state_to_ru_profile, используй её.

    text = format_profile(profile)

    if show_menu:
        await message.answer(text, reply_markup=main_menu_keyboard)
    else:
        await message.answer(text)

def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


# ==========================================================
# Хендлеры главного меню
# ==========================================================

@router.callback_query(F.data == "show_my_data")
async def show_my_data_cb(cb: CallbackQuery, state: FSMContext):
    await send_summary(cb.message, state, show_menu=True)
    await state.set_state(UserState.main_menu)
    await cb.answer()

@router.callback_query(F.data == "change_data_start_from_menu")
async def change_data_start_from_menu_cb(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.change_data_menu)
    await cb.message.edit_text("Что хотите изменить?", reply_markup=change_data_keyboard)
    await cb.answer()

@router.callback_query(F.data == "add_tx_start")
async def add_tx_start_cb(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_transactions_input)
    await cb.message.answer(
        "Пришлите список операций в свободном формате.\n"
        "Примеры:\n"
        "• 130000 зп, -300 кофе\n"
        "• +2500 возврат\n\n"
        "Можно через запятую, точку с запятой или с новой строки.\n"
        "Знак «-» — расход, «+» — доход. Без знака: «зп/зарплата» → доход."
    )
    await cb.answer()

@router.callback_query(F.data == "show_plan")
async def show_plan_cb(cb: types.CallbackQuery, state: FSMContext):
    user_id = str(cb.from_user.id)
    users = load_users()
    raw = users.get(user_id) or (await state.get_data()) or {}

    await cb.answer()
    if not raw:
        await cb.message.answer("Профиль не найден. Нажмите /start и заполните данные.")
        return
    if apply_modifiers is None:
        await cb.message.answer("Модуль расчёта плана не подключён (utils/budget.py).")
        return

    def _val(key, *aliases, default=None):
        for k in (key, *aliases):
            if k in raw and raw[k] is not None:
                return raw[k]
        return default

    # Маппинг значений из базы к формату budget.py
    housing_map = {
        "parents": "с_родителями", "housing_parents": "с_родителями",
        "dorm": "общежитие", "housing_dorm": "общежитие",
        "rent": "снимает", "housing_rent": "снимает",
        "own": "своя", "housing_own": "своя",
    }
    transport_map = {
        "public": "общественный", "transport_public": "общественный",
        "taxi": "такси", "transport_taxi": "такси",
        "car": "своя_машина", "transport_car": "своя_машина",
        "driver": "водитель", "transport_driver": "водитель",
    }
    status_map = {
        "single": "одинокий", "family_single": "одинокий",
        "relationship": "в_отношениях", "family_relationship": "в_отношениях",
        "married": "женат_замужем", "family_married": "женат_замужем",
        "divorced": "в_разводе", "family_divorced": "в_разводе",
    }
    
    raw_housing = _val("housing", "housing_type", default="rent")
    raw_transport = _val("transport", "transport_type", default="public")
    raw_status = _val("status", "family_status", default="single")

    profile = {
        "age": int(_val("age", default=30)),
        "sex": _val("gender", "sex", default="м"),
        "transport": transport_map.get(raw_transport, raw_transport),
        "housing": housing_map.get(raw_housing, raw_housing),
        "mortgage": bool(_val("mortgage", default=False)),
        "status": status_map.get(raw_status, raw_status),
        "kids": 1 if str(_val("kids", "children", "children_type", default="0")).lower() in ("1", "yes", "да", "children_yes") else 0,
        "pays_alimony": False,  # Теперь используем фиксированную сумму
        "budget_level": "средний",
    }

    try:
        budget = float(raw.get("budget", 0))
    except (TypeError, ValueError):
        budget = 0.0

    if budget <= 0:
        await cb.message.answer("⚠️ Не удалось определить ваш бюджет. Укажите его в профиле.")
        return

    # Получаем фиксированные суммы кредита и алиментов
    try:
        credit_amount = float(_val("credit_amount", default=0))
    except (TypeError, ValueError):
        credit_amount = 0.0
    
    try:
        alimony_amount = float(_val("alimony_amount", default=0))
    except (TypeError, ValueError):
        alimony_amount = 0.0

    # Считаем оставшийся бюджет после обязательных платежей
    fixed_expenses = credit_amount + alimony_amount
    remaining_budget = budget - fixed_expenses

    if remaining_budget <= 0:
        await cb.message.answer(
            f"⚠️ Ваши обязательные платежи ({fixed_expenses:,.0f} ₽) превышают бюджет!\n\n"
            f"💳 Кредит: {credit_amount:,.0f} ₽\n"
            f"👶 Алименты: {alimony_amount:,.0f} ₽\n"
            f"💰 Бюджет: {budget:,.0f} ₽".replace(",", " "),
            reply_markup=main_menu_keyboard
        )
        return

    # Получаем план распределения (в процентах от оставшегося бюджета)
    plan = apply_modifiers(profile)
    
    # Убираем категории кредитов и алиментов из процентного плана (они фиксированные)
    plan.pop("Кредиты", None)
    plan.pop("Алименты", None)

    lines = []
    
    # Сначала показываем обязательные платежи
    if credit_amount > 0:
        pct = (credit_amount / budget) * 100
        lines.append(f"💳 Кредит/ипотека: {credit_amount:,.0f} ₽ ({pct:.1f}%) — ФИКС".replace(",", " "))
    
    if alimony_amount > 0:
        pct = (alimony_amount / budget) * 100
        lines.append(f"👶 Алименты: {alimony_amount:,.0f} ₽ ({pct:.1f}%) — ФИКС".replace(",", " "))
    
    if lines:
        lines.append("")  # Пустая строка-разделитель
    
    # Теперь распределяем оставшийся бюджет
    total_sum = fixed_expenses
    for k, v in plan.items():
        if v == 0:
            continue
        amount = round(remaining_budget * (v / 100))
        total_sum += amount
        lines.append(f"• {k}: {amount:,.0f} ₽ ({v:.1f}%)".replace(",", " "))

    # Показываем итог
    free_money = round(budget - total_sum)
    if free_money > 0:
        lines.append(f"\n💵 Свободные средства: {free_money:,.0f} ₽".replace(",", " "))

    await cb.message.answer(
        f"📅 План на месяц\n"
        f"💰 Бюджет: {budget:,.0f} ₽\n".replace(",", " ") +
        (f"📍 Распределяем после обязат. платежей: {remaining_budget:,.0f} ₽\n\n".replace(",", " ") if fixed_expenses > 0 else "\n") +
        "\n".join(lines),
        reply_markup=main_menu_keyboard
    )
    # Здесь нет вызова эко-советов.

@router.callback_query(F.data == "eco_tips")
async def eco_tips_cb(cb: CallbackQuery, state: FSMContext):
    try:
        user_id = str(cb.from_user.id)
        users = load_users()
        raw = users.get(user_id) or (await state.get_data()) or {}
        if not raw:
            await cb.answer("Профиль не найден. Нажмите /start и заполните данные.", show_alert=True)
            return

        def _get(*keys, default=None):
            for k in keys:
                if k in raw and raw[k] is not None:
                    return raw[k]
            return default

        # Определяем уровень бюджета
        try:
            budget_val = int(_get("budget", default=0))
        except (TypeError, ValueError):
            budget_val = 0
            
        if budget_val < 40000:
            budget_level = "низкий"
        elif budget_val > 150000:
            budget_level = "высокий"
        else:
            budget_level = "средний"

        # Собираем профиль под generate_eco_tips
        profile = {
            "age": int(_get("age", default=30)),
            "sex": (_get("sex", "gender", default="") or "").lower(),
            "transport": (_get("transport", "transport_type", default="") or "").lower(),
            "housing": (_get("housing", "housing_type", default="") or "").lower(),
            "status": (_get("status", "family_status", default="") or "").lower(),
            "kids": 1 if str(_get("kids", "children_type", "children", default="")).lower() in ("yes", "да", "true", "1", "children_yes") else 0,
            "pays_alimony": bool(str(_get("pays_alimony", "alimony_type", "alimony", default="")).lower() in ("yes", "да", "true", "1")),
            "budget_level": budget_level,
        }

        # Передаём user_id для уникальной рандомизации
        tips = generate_eco_tips(profile, user_id=user_id)
        text = "🌿 *Эко-советы для вас:*\n\n" + "\n\n".join(f"{t}" for t in tips)
        await cb.message.answer(text, parse_mode="Markdown", reply_markup=main_menu_keyboard)
        await state.set_state(UserState.main_menu)
        await cb.answer()

    except Exception:
        logging.exception("[eco_tips] handler failed")
        await cb.answer("Ошибка внутри обработчика эко-советов. Посмотрите логи.", show_alert=True)

# ==========================================================
# Хендлеры изменения данных
# ==========================================================

@router.callback_query(UserState.change_data_menu, F.data == "change_name")
async def change_name_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_name)
    await cb.answer()
    await cb.message.answer("Введите новое имя (2–64 символа):")

@router.callback_query(UserState.change_data_menu, F.data == "change_age")
async def change_age_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_age)
    await cb.answer()
    await cb.message.answer("Введите новый возраст (1–120):")

@router.callback_query(UserState.change_data_menu, F.data == "change_budget")
async def change_budget_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_budget)
    await cb.answer()
    await cb.message.answer(
        "💰 Введите новый бюджет в рублях:\n\n"
        "📝 Формат: можно использовать пробелы, запятые или подчёркивания\n"
        "Примеры: 30000, 30 000, 30_000, 30,000"
    )

@router.callback_query(UserState.change_data_menu, F.data == "change_transport")
async def change_transport_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_transport)
    await cb.answer()
    await cb.message.answer("Какой вид транспорта вы используете?", reply_markup=transport_keyboard)

@router.callback_query(UserState.change_data_menu, F.data == "change_housing")
async def change_housing_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_housing)
    await cb.answer()
    await cb.message.answer("Где вы живёте?", reply_markup=housing_keyboard)

@router.callback_query(UserState.change_data_menu, F.data == "change_family_status")
async def change_family_status_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_family_status)
    await cb.answer()
    await cb.message.answer("Какое у вас семейное положение?", reply_markup=family_status_keyboard)

@router.callback_query(UserState.change_data_menu, F.data == "change_children")
async def change_children_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_children)
    await cb.answer()
    await cb.message.answer("Есть ли дети?", reply_markup=children_keyboard)

@router.callback_query(UserState.change_data_menu, F.data == "change_credit")
async def change_credit_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_credit_amount)
    await cb.answer()
    await cb.message.answer(
        "💳 Введите ежемесячный платёж по кредиту/ипотеке в рублях.\n"
        "Если кредита нет, введите 0:"
    )

@router.callback_query(UserState.change_data_menu, F.data == "change_alimony")
async def change_alimony_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_alimony_amount)
    await cb.answer()
    await cb.message.answer(
        "👶 Введите ежемесячную сумму алиментов в рублях.\n"
        "Если алиментов нет, введите 0:"
    )

@router.callback_query(UserState.change_data_menu, F.data == "change_gender")
async def change_gender_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.waiting_for_new_gender)
    await cb.answer()
    await cb.message.answer("Выберите ваш пол:", reply_markup=gender_keyboard)

@router.callback_query(UserState.change_data_menu, F.data == "back_to_main_menu")
async def back_to_main_from_change(cb: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.main_menu)
    await cb.answer()
    await cb.message.edit_text("📝 Главное меню:", reply_markup=main_menu_keyboard)


# ==========================================================
# ОБРАБОТЧИКИ ВВОДА ПОЛЬЗОВАТЕЛЯ
# ==========================================================
# Обработчики ввода текста
@router.message(UserState.waiting_for_new_name)
async def process_new_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if not (2 <= len(new_name) <= 64):
        await message.answer("Имя должно быть 2–64 символа. Попробуйте ещё раз.")
        return
    await state.update_data(name=new_name)
    update_user_data(str(message.from_user.id), {"name": new_name})
    await message.answer("Имя успешно изменено.")
    await send_summary(message, state, show_menu=True)
    await state.set_state(UserState.main_menu)

@router.message(UserState.waiting_for_new_age)
async def process_new_age(message: types.Message, state: FSMContext):
    try:
        new_age = int(message.text.strip())
        if not (1 <= new_age <= 120):
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число от 1 до 120.")
        return
    await state.update_data(age=new_age)
    update_user_data(str(message.from_user.id), {"age": new_age})
    await message.answer("Возраст успешно изменён.")
    await send_summary(message, state, show_menu=True)
    await state.set_state(UserState.main_menu)

@router.message(UserState.waiting_for_new_budget)
async def process_new_budget(message: types.Message, state: FSMContext):
    try:
        new_budget = parse_budget_input(message.text)
        if new_budget <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Бюджет должен быть больше 0. Введите реальную сумму.\n\n"
            "📝 Формат: можно использовать пробелы, запятые или подчёркивания\n"
            "Примеры: 30000, 30 000, 30_000, 30,000"
        )
        return
    await state.update_data(budget=new_budget)
    update_user_data(str(message.from_user.id), {"budget": new_budget})
    await message.answer("Бюджет успешно изменён.")
    await send_summary(message, state, show_menu=True)
    await state.set_state(UserState.main_menu)


# Обработчики выбора с инлайн-клавиатур
@router.callback_query(StateFilter(UserState.waiting_for_new_gender), F.data.startswith("gender_"))
async def process_new_gender_callback(cb: CallbackQuery, state: FSMContext):
    value = cb.data.replace("gender_", "").strip()
    await state.update_data(gender=value)
    update_user_data(str(cb.from_user.id), {"gender": value})
    await cb.message.answer("Пол успешно изменён.")
    await send_summary(cb.message, state, show_menu=True)
    await state.set_state(UserState.main_menu)
    await cb.answer()

@router.callback_query(StateFilter(UserState.waiting_for_new_transport), F.data.startswith("transport_"))
async def process_new_transport_callback(cb: CallbackQuery, state: FSMContext):
    value = cb.data.replace("transport_", "").strip()
    await state.update_data(transport_type=value)
    update_user_data(str(cb.from_user.id), {"transport_type": value})
    await cb.message.answer("Транспорт успешно изменён.")
    await send_summary(cb.message, state, show_menu=True)
    await state.set_state(UserState.main_menu)
    await cb.answer()

@router.callback_query(StateFilter(UserState.waiting_for_new_housing), F.data.startswith("housing_"))
async def process_new_housing_callback(cb: CallbackQuery, state: FSMContext):
    value = cb.data.replace("housing_", "").strip()
    await state.update_data(housing_type=value)
    update_user_data(str(cb.from_user.id), {"housing_type": value})
    await cb.message.answer("Жильё успешно изменено.")
    await send_summary(cb.message, state, show_menu=True)
    await state.set_state(UserState.main_menu)
    await cb.answer()

@router.callback_query(StateFilter(UserState.waiting_for_new_family_status), F.data.startswith("family_"))
async def process_new_family_status_callback(cb: CallbackQuery, state: FSMContext):
    value = cb.data.replace("family_", "").strip()
    await state.update_data(family_status=value)
    update_user_data(str(cb.from_user.id), {"family_status": value})
    await cb.message.answer("Семейное положение успешно изменено.")
    await send_summary(cb.message, state, show_menu=True)
    await state.set_state(UserState.main_menu)
    await cb.answer()

@router.callback_query(StateFilter(UserState.waiting_for_new_children), F.data.startswith("children_"))
async def process_new_children_callback(cb: CallbackQuery, state: FSMContext):
    value = cb.data.replace("children_", "")
    await state.update_data(children_type=value)
    update_user_data(str(cb.from_user.id), {"children_type": value})
    await cb.message.answer("Данные о детях успешно изменены.")
    await send_summary(cb.message, state, show_menu=True)
    await state.set_state(UserState.main_menu)
    await cb.answer()

# Обработчики текстового ввода для кредита и алиментов
@router.message(UserState.waiting_for_new_credit_amount)
async def process_new_credit_amount(message: types.Message, state: FSMContext):
    try:
        credit = int(message.text.strip())
        if credit < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число ≥ 0:")
        return
    
    await state.update_data(credit_amount=credit)
    update_user_data(str(message.from_user.id), {"credit_amount": credit})
    await message.answer("💳 Сумма кредита успешно изменена.")
    await send_summary(message, state, show_menu=True)
    await state.set_state(UserState.main_menu)

@router.message(UserState.waiting_for_new_alimony_amount)
async def process_new_alimony_amount(message: types.Message, state: FSMContext):
    try:
        alimony = int(message.text.strip())
        if alimony < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число ≥ 0:")
        return
    
    await state.update_data(alimony_amount=alimony)
    update_user_data(str(message.from_user.id), {"alimony_amount": alimony})
    await message.answer("👶 Сумма алиментов успешно изменена.")
    await send_summary(message, state, show_menu=True)
    await state.set_state(UserState.main_menu)

# ==========================================================
# Обработчики транзакций и баланса
# ==========================================================

@router.message(UserState.waiting_for_transactions_input)
async def handle_transactions_input(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    txs = parse_transactions(message.text or "")
    if not txs:
        await message.answer(
            "🤔 Не нашёл сумм в сообщении.\n\n"
            "Примеры:\n"
            "• `500 кофе` — расход на кофе\n"
            "• `кофе 500` — тоже работает\n"
            "• `+50000 зп` — доход (зарплата)\n"
            "• `пятёрочка 2500, такси 350`",
            parse_mode="Markdown"
        )
        return
    
    save_transactions(user_id, txs)
    
    # Считаем итоги
    total_income = sum(t["amount"] for t in txs if t["amount"] > 0)
    total_expense = sum(-t["amount"] for t in txs if t["amount"] < 0)
    
    # Формируем красивый вывод
    lines = []
    for t in txs:
        emoji = "💰" if t["amount"] > 0 else "💸"
        sign = "+" if t["amount"] > 0 else ""
        cat = t.get("category") or "Прочее"
        note = t.get("note", "")
        
        if note and note != cat:
            lines.append(f"{emoji} {sign}{t['amount']:.0f} ₽ • {cat} • {note}")
        else:
            lines.append(f"{emoji} {sign}{t['amount']:.0f} ₽ • {cat}")
    
    # Формируем итоговую строку
    summary_parts = []
    if total_income > 0:
        summary_parts.append(f"💰 Доход: +{total_income:.0f} ₽")
    if total_expense > 0:
        summary_parts.append(f"💸 Расход: -{total_expense:.0f} ₽")
    
    summary = "\n".join(summary_parts) if summary_parts else ""
    
    await message.answer(
        "✅ Записал:\n" + "\n".join(lines) + 
        (f"\n\n{summary}" if summary else ""),
        reply_markup=main_menu_keyboard
    )
    await state.set_state(UserState.main_menu)

@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    user_id = str(message.from_user.id)
    txs = load_transactions(user_id)
    if not txs:
        await message.answer("Пока нет записей. Пришлите, например: `130000 зп, -300 кофе`", parse_mode="Markdown")
        return
    total_income = sum(t["amount"] for t in txs if t["amount"] > 0)
    total_expense = -sum(t["amount"] for t in txs if t["amount"] < 0)
    total_net = total_income - total_expense
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    txs_month = [t for t in txs if _parse_ts(t.get("ts", "")) >= month_start]
    month_income = sum(t["amount"] for t in txs_month if t["amount"] > 0)
    month_expense = -sum(t["amount"] for t in txs_month if t["amount"] < 0)
    month_net = month_income - month_expense
    by_cat = {}
    for t in txs_month:
        if t["amount"] < 0:
            cat = t.get("category") or "Прочее"
            by_cat[cat] = by_cat.get(cat, 0) + (-t["amount"])
    top = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:5]
    top_lines = "\n".join([f"• {c}: {v:.2f} RUB" for c, v in top]) if top else "• нет расходов"
    text = (
        "📊 *Баланс*\n"
        f"Всего: доход {total_income:.2f} RUB, расход {total_expense:.2f} RUB, итог {total_net:.2f} RUB\n\n"
        f"📆 *За месяц*: доход {month_income:.2f} RUB, расход {month_expense:.2f} RUB, итог {month_net:.2f} RUB\n"
        f"🏷 *Топ расходов за месяц:*\n{top_lines}"
    )
    await message.answer(text, parse_mode="Markdown")


# ==========================================================
# ФОЛЛБЭКИ И УНИВЕРСАЛЬНЫЙ ВВОД ОПЕРАЦИЙ
# ==========================================================

@router.message(F.text & ~F.text.startswith("/"))
async def universal_operations_input(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if current and current.startswith("UserState.waiting_for_new_"):
        return

    text = message.text or ""
    txs = parse_transactions(text)
    if not txs:
        if current == str(UserState.main_menu):
            await message.answer(
                "Не понял сообщение. Пожалуйста, используйте кнопки меню.",
                reply_markup=main_menu_keyboard
            )
        return

    user_id = str(message.from_user.id)
    save_transactions(user_id, txs)
    
    # Считаем итоги
    total_income = sum(t["amount"] for t in txs if t["amount"] > 0)
    total_expense = sum(-t["amount"] for t in txs if t["amount"] < 0)
    
    # Формируем красивый вывод
    lines = []
    for t in txs:
        emoji = "💰" if t["amount"] > 0 else "💸"
        sign = "+" if t["amount"] > 0 else ""
        cat = t.get("category") or "Прочее"
        note = t.get("note", "")
        
        if note and note != cat:
            lines.append(f"{emoji} {sign}{t['amount']:.0f} ₽ • {cat} • {note}")
        else:
            lines.append(f"{emoji} {sign}{t['amount']:.0f} ₽ • {cat}")
    
    # Формируем итоговую строку
    summary_parts = []
    if total_income > 0:
        summary_parts.append(f"💰 Доход: +{total_income:.0f} ₽")
    if total_expense > 0:
        summary_parts.append(f"💸 Расход: -{total_expense:.0f} ₽")
    
    summary = "\n".join(summary_parts) if summary_parts else ""
    
    await message.answer(
        "✅ Записал:\n" + "\n".join(lines) + 
        (f"\n\n{summary}" if summary else "") +
        "\n\n📊 Посмотреть баланс: /balance"
    )

@router.message()
async def global_unhandled_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None or current_state == UserState.main_menu:
        await message.answer("Извините, я вас не понял. Пожалуйста, используйте кнопки или введите /start.", reply_markup=main_menu_keyboard)
    else:
        await message.answer("Пожалуйста, следуйте инструкциям для текущего шага.")