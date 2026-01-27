from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from states.user_state import UserState
from utils.storage import update_user_data # <--- ВОТ ЭТОТ ИМПОРТ ДОЛЖЕН БЫТЬ
from utils.helpers import send_summary
from aiogram import F
from aiogram.types import CallbackQuery
from keyboards.keyboards import (
    transport_keyboard, housing_keyboard,
    family_status_keyboard, children_keyboard,
    alimony_keyboard, confirmation_only_keyboard,
    gender_keyboard,
)

router = Router()

def parse_budget_input(text: str) -> int:
    """
    Парсит ввод бюджета, удаляя пробелы, запятые и подчёркивания.
    Возвращает целое число или вызывает ValueError.
    """
    # Удаляем пробелы, запятые, подчёркивания
    cleaned = text.strip().replace(" ", "").replace(",", "").replace("_", "")
    return int(cleaned)



@router.message(UserState.waiting_for_nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    nickname = message.text
    # Сохраняем в FSM и сразу в базу
    await state.update_data(name=nickname)
    update_user_data(str(message.from_user.id), {"name": nickname})
    await state.set_state(UserState.waiting_for_age)
    await message.answer(f"👋 Приятно познакомиться, {nickname}!\n\n🎂 Введите ваш возраст:")

@router.message(UserState.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if not (1 <= age <= 120):
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число от 1 до 120.")
        return

    await state.update_data(age=age)
    update_user_data(str(message.from_user.id), {"age": age})
    await state.set_state(UserState.waiting_for_gender)
    await message.answer("👤 Выберите ваш пол:", reply_markup=gender_keyboard)

@router.message(UserState.waiting_for_budget)
async def process_budget(message: types.Message, state: FSMContext):
    try:
        budget = parse_budget_input(message.text)
        if budget <= 0:
            await message.answer("❌ Бюджет должен быть больше 0. Введите реальную сумму.")
            return
        # Сохраняем в FSM и в базу
        await state.update_data(budget=budget)
        update_user_data(str(message.from_user.id), {"budget": budget})
        await state.set_state(UserState.waiting_for_transport_choice)
        await message.answer("🚗 Какой вид транспорта вы используете?", reply_markup=transport_keyboard)
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\n\n"
            "📝 Формат: можно использовать пробелы, запятые или подчёркивания\n"
            "Примеры: 30000, 30 000, 30_000, 30,000"
        )
        return

@router.callback_query(UserState.waiting_for_gender, F.data.startswith("gender_"))
async def process_gender(cb: types.CallbackQuery, state: FSMContext):
    # gender_male / gender_female / gender_other → берём хвост после 'gender_'
    gender = cb.data.replace("gender_", "")
    await state.update_data(gender=gender)
    update_user_data(str(cb.from_user.id), {"gender": gender})

    # дальше — твоя следующая логика (например, спрашиваем бюджет)
    await state.set_state(UserState.waiting_for_budget)
    await cb.message.edit_text(
        "💰 Теперь введите ваш бюджет на месяц в рублях:\n\n"
        "📝 Формат: можно использовать пробелы, запятые или подчёркивания\n"
        "Примеры: 30000, 30 000, 30_000, 30,000"
    )
    await cb.answer()

@router.callback_query(UserState.waiting_for_transport_choice) 
async def process_transport_choice(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем тип транспорта из callback_data
    transport_type = callback_query.data.replace("transport_", "")

    await state.update_data(transport_type=transport_type)
    update_user_data(str(callback_query.from_user.id), {"transport_type": transport_type})

    await callback_query.message.edit_text(
        "🏠 Где вы живёте?", 
        reply_markup=housing_keyboard
    )
    await state.set_state(UserState.waiting_for_housing_choice)
    await callback_query.answer() # Снимаем "часики"


# 5. Обработка выбора жилья (Callback-обработка)
@router.callback_query(UserState.waiting_for_housing_choice)
async def process_housing_choice(callback_query: types.CallbackQuery, state: FSMContext):
    housing_type = callback_query.data.replace("housing_", "")

    await state.update_data(housing_type=housing_type)
    update_user_data(str(callback_query.from_user.id), {"housing_type": housing_type})

    await callback_query.message.edit_text(
        "❤️ Какое у вас семейное положение?", 
        reply_markup=family_status_keyboard
    )
    await state.set_state(UserState.waiting_for_family_status_choice)
    await callback_query.answer()


# 6. Обработка выбора семейного положения (Callback-обработка)
@router.callback_query(UserState.waiting_for_family_status_choice)
async def process_family_status_choice(callback_query: types.CallbackQuery, state: FSMContext):
    family_status = callback_query.data.replace("family_", "")

    await state.update_data(family_status=family_status)
    update_user_data(str(callback_query.from_user.id), {"family_status": family_status})

    await callback_query.message.edit_text(
        "👶 Есть ли у вас дети?", 
        reply_markup=children_keyboard
    )
    await state.set_state(UserState.waiting_for_children_choice)
    await callback_query.answer()


# 7. Обработка выбора детей (Callback-обработка)
@router.callback_query(UserState.waiting_for_children_choice)
async def process_children_choice(callback_query: types.CallbackQuery, state: FSMContext):
    children_type = callback_query.data.replace("children_", "")

    await state.update_data(children_type=children_type)
    update_user_data(str(callback_query.from_user.id), {"children_type": children_type})

    # Переходим к вводу суммы кредита
    await state.set_state(UserState.waiting_for_credit_amount)

    await callback_query.message.edit_text(
        "💳 Укажите ежемесячный платёж по кредиту/ипотеке в рублях.\n\n"
        "Если кредита нет, введите 0:"
    )
    await callback_query.answer()


# 8. Обработка суммы кредита (текстовый ввод)
@router.message(UserState.waiting_for_credit_amount)
async def process_credit_amount(message: types.Message, state: FSMContext):
    try:
        credit = int(message.text.strip())
        if credit < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число ≥ 0 (сумму в рублях):")
        return

    await state.update_data(credit_amount=credit)
    update_user_data(str(message.from_user.id), {"credit_amount": credit})
    
    # Переходим к вводу алиментов
    await state.set_state(UserState.waiting_for_alimony_amount)
    await message.answer(
        "👶 Укажите ежемесячную сумму алиментов в рублях.\n\n"
        "Если алиментов нет, введите 0:"
    )


# 9. Обработка суммы алиментов (текстовый ввод, последний шаг анкеты)
@router.message(UserState.waiting_for_alimony_amount)
async def process_alimony_amount(message: types.Message, state: FSMContext):
    try:
        alimony = int(message.text.strip())
        if alimony < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число ≥ 0 (сумму в рублях):")
        return

    await state.update_data(alimony_amount=alimony)
    update_user_data(str(message.from_user.id), {"alimony_amount": alimony})

    # Показываем сводку с кнопкой подтверждения
    await send_summary(message, state, reply_markup=confirmation_only_keyboard)
    await state.set_state(UserState.waiting_for_confirmation)


@router.callback_query(UserState.waiting_for_new_gender, F.data.startswith("gender_"))
async def process_new_gender(cb: CallbackQuery, state: FSMContext):
    value = cb.data.replace("gender_", "")
    await state.update_data(gender=value)
    update_user_data(str(cb.from_user.id), await state.get_data())
    await cb.message.answer("Пол успешно изменён.")
    await send_summary(cb.message, state, show_menu=True)
    await state.set_state(UserState.main_menu)
    await cb.answer()
