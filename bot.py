import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from utils.scheduler import AutoScheduler
from utils.database import db_manager
from handlers.start import start_handler, reset_data_handler, restart_handler
# Импортируем остальные хендлеры (убедись, что файлы существуют)
try:
    from handlers.profile import profile_conv_handler
    from handlers.auto import auto_conv_handler
    from handlers.family import family_conv_handler
    from handlers.achievements import achievements_handler
    from handlers.schedule import schedule_conv_handler
    from handlers.stats import stats_handler
except ImportError as e:
    logging.warning(f"Could not import some handlers: {e}")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def menu(update: Update, context):
    from keyboards.inline import main_menu_keyboard
    text = "Главное меню:\nВыберите раздел:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard())

async def error_handler(update: object, context) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    # Можно добавить отправку уведомления админу

def main():
    # 1. Инициализация БД
    logger.info("Initializing database...")
    db_manager.init_db()
    
    # 2. Event loop для Python 3.14+
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # 3. Планировщик
    logger.info("Starting scheduler...")
    auto_scheduler = AutoScheduler()
    auto_scheduler.start()

    # 4. ТОКЕН БОТА
    TOKEN = "8898518897:AAGsX4mTNcTf-pqm9X9GUyt7DJ_qNG-9Xb0"
    
    # 5. Создание приложения
    application = Application.builder().token(TOKEN).build()

    # 6. Хендлеры
    application.add_handler(CommandHandler("start", start_handler.callback))
    application.add_handler(CommandHandler("menu", menu))
    
    # Кнопки
    application.add_handler(reset_data_handler)
    application.add_handler(restart_handler)
    
    # Конвейеры (если файлы существуют)
    try:
        application.add_handler(profile_conv_handler)
        application.add_handler(auto_conv_handler)
        application.add_handler(family_conv_handler)
        application.add_handler(achievements_handler)
        application.add_handler(schedule_conv_handler)
        application.add_handler(stats_handler)
    except NameError:
        logger.warning("Some conversation handlers are missing, skipping...")

    # 7. Обработка ошибок
    application.add_error_handler(error_handler)

    # 8. Запуск
    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
