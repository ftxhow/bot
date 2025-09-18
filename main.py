from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Настройка логирования 
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO) 

# Функция обработки команды /start 
def start(update, context): 
    context.bot.send_message(chat_id=update.effective_chat.id, text='Привет! Я бот. Напиши "start", чтобы продолжить.') 

# Функция обработки входящих сообщений 
def handle_message(update, context): 
    message = update.message.text.lower() 

    if message == 'start': 
        context.bot.send_message(chat_id=update.effective_chat.id, text='Это окончательное сообщение.') 
    else: 
        context.bot.send_message(chat_id=update.effective_chat.id, text='Я уже все сказал. :)') 

def main(): 
    # Создание объекта Updater и передача токена вашего бота 
    updater = Updater(token='YOUR_BOT_TOKEN', use_context=True) 

    # Получение диспетчера для регистрации обработчиков 
    dispatcher = updater.dispatcher 

    # Регистрация обработчиков команды /start и входящих сообщений 
    start_handler = CommandHandler('start', start) 
    message_handler = MessageHandler(Filters.text & ~Filters.command, handle_message) 
    dispatcher.add_handler(start_handler) 
    dispatcher.add_handler(message_handler) 

    # Запуск бота 
    updater.start_polling() 

if __name__ == '__main__': 
    main() 
