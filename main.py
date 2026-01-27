import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from global_state import TOKEN

# Импорт всех хендлеров
from handlers import start, profile, menu

logging.basicConfig(level=logging.INFO)

# Debug router для отлова необработанных сообщений
debug_router = Router()

@debug_router.callback_query()
async def _debug_any_callback(cb: types.CallbackQuery, state: FSMContext):
    st = await state.get_state()
    logging.warning(f"UNHANDLED CALLBACK: data={cb.data!r}, state={st}")
    await cb.answer()

@debug_router.message()
async def _debug_any_message(msg: types.Message, state: FSMContext):
    st = await state.get_state()
    logging.warning(f"UNHANDLED MESSAGE: text={msg.text!r}, state={st}")


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем все обработчики
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(menu.router)
    
    # Debug router регистрируем последним - он ловит всё необработанное
    dp.include_router(debug_router)

    logging.info("✅ Бот запущен и слушает обновления...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())