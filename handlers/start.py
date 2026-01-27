from os import name
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from states.user_state import UserState
from utils.helpers import send_summary
from utils.storage import load_users
from aiogram.types import CallbackQuery
from keyboards.keyboards import (
    transport_keyboard, housing_keyboard,
    family_status_keyboard, children_keyboard,
    alimony_keyboard,
    confirmation_only_keyboard,
    start_inline_keyboard
)

router = Router()

WELCOME_TEXT = """👋 Здравствуйте! Давайте познакомимся.

━━━━━━━━━━━━━━━━━━
Для вашей конфиденциальности и в соответствии с ФЗ-152 "О персональных данных" (ст. 3) прошу:

• Не использовать реальное имя (Иван, Анна и т.д.).
• Выбрать нейтральный никнейм - он не должен позволять идентифицировать вас.

━━━━━━━━━━━━━━━━━━
👍🏻 Примеры подходящих ников:
Mars_Explorer  Quantum_Learner  Чайка_88

👎🏻 Примеры НЕподходящих:
ИванПетров  Anna_Sidorova_1995  Ирина227

Пожалуйста, напишите — как к вам обращаться?
"""

# 1) /start — показываем WELCOME и сразу ждём ник
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users = load_users()            # читаем JSON
    existing = users.get(user_id)   # данные пользователя или None

    # Сбрасываем прежнее состояние диалога, чтобы начать "чисто"
    await state.clear()

    if existing:
        # ✅ Пользователь уже есть — подтягиваем данные в FSM и показываем меню
        await state.update_data(**existing)
        await state.set_state(UserState.main_menu)
        await message.answer("👋 С возвращением! Нашёл ваши сохранённые данные 👇")
        await send_summary(message, state, show_menu=True)
        return

    # ❌ Пользователь новый — показываем приветствие и сразу ждём ник
    await message.answer(WELCOME_TEXT)
    await state.set_state(UserState.waiting_for_nickname)


# 3) Обработка ника — обработчик в profile.py


# 4) Обработка возраста — обработчик в profile.py


# 5) Обработка подтверждения (кнопки подтверждения должны иметь callback_data 'confirm_data')
@router.callback_query(UserState.waiting_for_confirmation, F.data == "confirm_data")
async def confirm_data_handler(callback_query: types.CallbackQuery, state: FSMContext):
    from utils.storage import update_user_data
    await callback_query.answer("✅ Данные сохранены.")
    data = await state.get_data()
    user_id = str(callback_query.from_user.id)
    
    # Сохраняем данные в хранилище
    update_user_data(user_id, data)

    # Показываем меню
    await state.set_state(UserState.main_menu)
    await send_summary(callback_query.message, state, show_menu=True)


# 6) Обработка некорректных типов — удалено, т.к. F.state не поддерживается в aiogram 3