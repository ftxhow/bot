import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования 
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO) 

# Функция обработки команды /start 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text('Привет! Я бот. Напиши "start", чтобы продолжить.') 

# Функция обработки входящих сообщений 
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    message = update.message.text.lower() 

    if message == 'start': 
        await update.message.reply_text('Это окончательное сообщение.') 
    else: 
        await update.message.reply_text('Я уже все сказал. :)') 

def main(): 
    # Создание приложения с токеном вашего бота 
    application = ApplicationBuilder().token('YOUR_BOT_TOKEN').build() 

    # Регистрация обработчиков команды /start и входящих сообщений 
    application.add_handler(CommandHandler('start', start)) 
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) 

    # Запуск бота 
    application.run_polling() 

if __name__ == '__main__': 
    main() 
