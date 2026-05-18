import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from utils.scheduler import AutoScheduler
from utils.database import db_manager
from handlers.start import start_handler, reset_data_handler, restart_handler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === ТОКЕН ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан! Добавьте в Environment Variables на Render.")

async def menu(update: Update, context):
    from keyboards.inline import main_menu_keyboard
    text = "Главное меню:\nВыберите раздел:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard())

async def error_handler(update: object, context) -> None:
    logger.error(f"Update {update} caused error {context.error}")

# === ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ===
async def handle_text(update: Update, context):
    await update.message.reply_text("Используйте /start или /menu для навигации.")

def main():
    # 1. Инициализация БД
    logger.info("Initializing database...")
    db_manager.init_db()
    
    # 2. Планировщик (глобальный, чтобы не удалялся сборщиком мусора)
    logger.info("Starting scheduler...")
    auto_scheduler = AutoScheduler()
    auto_scheduler.start()

    # 3. Создание приложения
    application = Application.builder().token(TOKEN).build()

    # 4. Хендлеры
    application.add_handler(CommandHandler("start", start_handler.callback))
    application.add_handler(CommandHandler("menu", menu))
    
    # Кнопки
    application.add_handler(reset_data_handler)
    application.add_handler(restart_handler)
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # 5. Обработка ошибок
    application.add_error_handler(error_handler)

    # 6. Запуск polling
    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
