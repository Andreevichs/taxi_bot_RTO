import os
import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, CallbackQueryHandler, ConversationHandler
)
from telegram import Update
from utils.scheduler import AutoScheduler
from utils.database import db_manager

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

async def handle_text(update: Update, context):
    await update.message.reply_text("Используйте /start или /menu для навигации.")

def main():
    logger.info("Initializing database...")
    db_manager.init_db()
    
    logger.info("Starting scheduler...")
    auto_scheduler = AutoScheduler()
    auto_scheduler.start()

    application = Application.builder().token(BOT_TOKEN).build()

    # === ИМПОРТ ХЕНДЛЕРОВ ===
    from handlers.start import (
        start_handler, reset_data_handler, 
        restart_handler, back_handler
    )
    from handlers.rto import (
        cmd_start_shift, cmd_end_shift, cmd_break_start, 
        cmd_break_end, cmd_status
    )
    from handlers.stats import (
        cmd_stats, cmd_earnings, cmd_achievements, cmd_weather
    )
    from handlers.cars import (
        cmd_cars, car_add_conv, car_set_active_start, 
        car_activate, car_delete_start, car_delete_confirm
    )
    from handlers.family import (
        cmd_family, family_add_conv, family_remove_start, family_del_confirm
    )
    from handlers.settings import (
        cmd_settings, cmd_scheduler, scheduler_set
    )

    # === БАЗОВЫЕ КОМАНДЫ ===
    application.add_handler(start_handler)
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(reset_data_handler)
    application.add_handler(restart_handler)
    application.add_handler(back_handler)

    # === РТО (СМЕНЫ) ===
    application.add_handler(CallbackQueryHandler(cmd_start_shift, pattern='^shift_start$'))
    application.add_handler(CallbackQueryHandler(cmd_end_shift, pattern='^shift_end$'))
    application.add_handler(CallbackQueryHandler(cmd_break_start, pattern='^break_start$'))
    application.add_handler(CallbackQueryHandler(cmd_break_end, pattern='^break_end$'))
    application.add_handler(CallbackQueryHandler(cmd_status, pattern='^status$'))

    # === СТАТИСТИКА ===
    application.add_handler(CallbackQueryHandler(cmd_stats, pattern='^stats$'))
    application.add_handler(CallbackQueryHandler(cmd_earnings, pattern='^earnings$'))
    application.add_handler(CallbackQueryHandler(cmd_achievements, pattern='^achievements$'))
    application.add_handler(CallbackQueryHandler(cmd_weather, pattern='^weather$'))

    # === АВТО ===
    application.add_handler(CallbackQueryHandler(cmd_cars, pattern='^cars$'))
    application.add_handler(car_add_conv)
    application.add_handler(CallbackQueryHandler(car_set_active_start, pattern='^car_set_active$'))
    application.add_handler(CallbackQueryHandler(car_activate, pattern='^activate_car_'))
    application.add_handler(CallbackQueryHandler(car_delete_start, pattern='^car_delete$'))
    application.add_handler(CallbackQueryHandler(car_delete_confirm, pattern='^delete_car_'))

    # === СЕМЬЯ ===
    application.add_handler(CallbackQueryHandler(cmd_family, pattern='^family$'))
    application.add_handler(family_add_conv)
    application.add_handler(CallbackQueryHandler(family_remove_start, pattern='^family_remove$'))
    application.add_handler(CallbackQueryHandler(family_del_confirm, pattern='^family_del_'))

    # === НАСТРОЙКИ ===
    application.add_handler(CallbackQueryHandler(cmd_settings, pattern='^settings$'))
    application.add_handler(CallbackQueryHandler(cmd_scheduler, pattern='^scheduler$'))
    application.add_handler(CallbackQueryHandler(scheduler_set, pattern='^scheduler_set$'))

    # === ТЕКСТ ===
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # === ОШИБКИ ===
    application.add_error_handler(error_handler)

    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
