# bot.py
import os
import logging
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)

import database as db
db.init_db()

from config import BOT_TOKEN
from handlers.start import start, button_handler, back_to_menu
from handlers.rto import cmd_start_shift, cmd_end_shift, cmd_break_start, cmd_break_end, cmd_status
from handlers.stats import cmd_stats, cmd_earnings, cmd_achievements, cmd_weather
from handlers.family import (
    cmd_family, family_add_start, family_add_done, family_remove,
    family_del_confirm, ASK_MEMBER_ID
)
from handlers.cars import (
    cmd_cars, car_add, car_add_text, car_default, car_set_default,
    car_remove, car_del_confirm
)
from handlers.settings import (
    cmd_settings, cmd_scheduler, scheduler_set, scheduler_text,
    scheduler_del, set_rate_start, set_rate_done,
    ASK_SCHEDULE, ASK_RATE
)
from utils.scheduler import AutoScheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "🚕 Taxi RTO Bot is running!"

@app.route('/health')
def health():
    return {"status": "ok", "time": "Europe/Minsk"}


async def handle_text(update: Update, context):
    """Обработка текстовых сообщений"""
    if context.user_data.get("awaiting_car"):
        from handlers.cars import car_add_text
        await car_add_text(update, context)
    elif context.user_data.get("awaiting_schedule"):
        from handlers.settings import scheduler_text
        await scheduler_text(update, context)
    elif context.user_data.get("awaiting_rate"):
        await set_rate_done(update, context)
    else:
        await update.message.reply_text(
            "Используйте /start для открытия меню.\n"
            "Или отправьте команду."
        )


def main():
    # Создаём event loop явно (Python 3.14 fix)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    application = Application.builder().token(BOT_TOKEN).build()

    auto_scheduler = AutoScheduler()
    auto_scheduler.start()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))

    application.add_handler(CallbackQueryHandler(button_handler, pattern="^back_menu$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^shift_"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^break_"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^status$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^earnings$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^achievements$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^weather$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^scheduler$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^family$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^cars$"))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^settings$"))

    family_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(family_add_start, pattern="^family_add$")],
        states={
            ASK_MEMBER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, family_add_done)]
        },
        fallbacks=[CallbackQueryHandler(cmd_family, pattern="^family$")],
        per_message=False
    )
    application.add_handler(family_conv)
    application.add_handler(CallbackQueryHandler(family_remove, pattern="^family_remove$"))
    application.add_handler(CallbackQueryHandler(family_del_confirm, pattern="^family_del_"))
    application.add_handler(CallbackQueryHandler(cmd_family, pattern="^family$"))

    application.add_handler(CallbackQueryHandler(cmd_cars, pattern="^cars$"))
    application.add_handler(CallbackQueryHandler(car_add, pattern="^car_add$"))
    application.add_handler(CallbackQueryHandler(car_default, pattern="^car_default$"))
    application.add_handler(CallbackQueryHandler(car_set_default, pattern="^car_set_"))
    application.add_handler(CallbackQueryHandler(car_remove, pattern="^car_remove$"))
    application.add_handler(CallbackQueryHandler(car_del_confirm, pattern="^car_del_"))

    application.add_handler(CallbackQueryHandler(cmd_settings, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(cmd_scheduler, pattern="^scheduler$"))
    application.add_handler(CallbackQueryHandler(scheduler_set, pattern="^scheduler_set$"))
    application.add_handler(CallbackQueryHandler(scheduler_del, pattern="^scheduler_del$"))
    application.add_handler(CallbackQueryHandler(set_rate_start, pattern="^set_rate$"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Starting bot...")

    if os.environ.get("RENDER"):
        PORT = int(os.environ.get("PORT", 10000))
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
            secret_token=os.environ.get("SECRET_TOKEN", "")
        )
    else:
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
