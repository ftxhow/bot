from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton # Убедитесь, что этот импорт ест

start_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="start_bot_init")]
    ]
)

# ===== 1. Подтверждение анкеты (БЕЗ «Изменить данные») =====
confirmation_only_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Далее", callback_data="confirm_data")]
    ]
)

main_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Показать данные 📊", callback_data="show_my_data")],
        [InlineKeyboardButton(text="Изменить данные ✍️", callback_data="change_data_start_from_menu")],
        [InlineKeyboardButton(text="План на месяц 📅", callback_data="show_plan")],
        [InlineKeyboardButton(text="Эко-советы 🌿", callback_data="eco_tips")],   # ← добавлено
        [InlineKeyboardButton(text="Записать покупки 🧾", callback_data="add_tx_start")],
    ]
)

# === 3. Меню изменения данных ===
# Содержит кнопки для каждой категории данных

change_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Имя ✍️", callback_data="change_name"),
     InlineKeyboardButton(text="Возраст 🎂", callback_data="change_age")],
    [InlineKeyboardButton(text="Бюджет 💰", callback_data="change_budget"),
     InlineKeyboardButton(text="Транспорт 🚗", callback_data="change_transport")],
    [InlineKeyboardButton(text="Жильё 🏠", callback_data="change_housing"),
     InlineKeyboardButton(text="Семейное положение 👨‍👩‍👧‍👦", callback_data="change_family_status")],
    [InlineKeyboardButton(text="Дети 👶", callback_data="change_children"),
     InlineKeyboardButton(text="Пол 🧑", callback_data="change_gender")],
    [InlineKeyboardButton(text="Кредит 💳", callback_data="change_credit"),
     InlineKeyboardButton(text="Алименты 👶", callback_data="change_alimony")],
    [InlineKeyboardButton(text="Назад в меню ↩️", callback_data="back_to_main_menu")],
])

# === 4. Клавиатура транспорта ===
transport_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Общественный транспорт", callback_data="transport_public")],
        [InlineKeyboardButton(text="Такси", callback_data="transport_taxi")],
        [InlineKeyboardButton(text="Своя машина", callback_data="transport_car")],
        [InlineKeyboardButton(text="Езжу с водителем", callback_data="transport_driver")],
    ]
)
gender_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Мужчина ♂️", callback_data="gender_male"),
            InlineKeyboardButton(text="Женщина ♀️", callback_data="gender_female"),
        ],
        [InlineKeyboardButton(text="Другое / предпочту не говорить", callback_data="gender_other")],
    ]
)

# === 5. Клавиатура жилья ===
housing_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Своё жильё", callback_data="housing_own"),
            InlineKeyboardButton(text="Арендую", callback_data="housing_rent"),
        ],
        [
            InlineKeyboardButton(text="Живу с родителями", callback_data="housing_parents"),
            InlineKeyboardButton(text="Общежитие", callback_data="housing_dorm"),
        ],
    ]
)

# === 6. Клавиатура семейного положения ===
family_status_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Холост/Не замужем", callback_data="family_single"),
            InlineKeyboardButton(text="В отношениях", callback_data="family_relationship"),
        ],
        [
            InlineKeyboardButton(text="Женат/Замужем", callback_data="family_married"),
            InlineKeyboardButton(text="В разводе", callback_data="family_divorced"),
        ],
    ]
)

# === 7. Клавиатура детей ===
children_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Есть дети", callback_data="children_yes")],
        [InlineKeyboardButton(text="Нет детей", callback_data="children_no")],
    ]
)
# === 8. Клавиатура алиментов ===

alimony_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Есть алименты", callback_data="alimony_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="alimony_no")],
    ]
)


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Новая клавиатура с одной кнопкой /start
start_command_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True # Скрывается после нажатия
)