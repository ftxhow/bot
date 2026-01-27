from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_age = State()
    waiting_for_budget = State()
    waiting_for_gender = State() 
    waiting_for_transport_choice = State()
    waiting_for_housing_choice = State()
    waiting_for_family_status_choice = State()
    waiting_for_children_choice = State()
    waiting_for_credit_amount = State()      # Новое: сумма кредита
    waiting_for_alimony_amount = State()     # Новое: сумма алиментов
    waiting_for_savings = State()            # Новое: сбережения (сумма или процент)
    waiting_for_confirmation = State()
    main_menu = State()
    change_data_menu = State()
    waiting_for_new_name = State()
    waiting_for_new_age = State()
    waiting_for_new_budget = State()
    waiting_for_new_gender = State() 
    waiting_for_new_transport = State()
    waiting_for_new_housing = State()
    waiting_for_new_family_status = State()
    waiting_for_new_children = State()
    waiting_for_new_credit_amount = State()  # Новое: изменение кредита
    waiting_for_new_alimony_amount = State() # Новое: изменение алиментов
    waiting_for_new_savings = State()        # Новое: изменение сбережений
    waiting_for_transactions_input = State()