import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)

from config import BOT_TOKEN
from handlers.rto import cmd_start_shift, cmd_end_shift, cmd_break_start, cmd_break_end, cmd_status
from handlers.stats import cmd_stats, cmd_earnings, cmd_achievements, cmd_weather
from handlers.family import cmd_family
from handlers.cars import cmd_cars
from handlers.settings import cmd_settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === FLASK ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🚕 Taxi RTO Bot is running!"

@app.route('/health')
def health():
    return {"status": "ok", "time": "Europe/Minsk"}

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# === СТАРТОВОЕ МЕНЮ ===
async def start(update: Update, context):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🚗 Начать смену", callback_data="shift_start"),
         InlineKeyboardButton("⏹️ Закончить смену", callback_data="shift_end")],
        [InlineKeyboardButton("☕ Перерыв", callback_data="break_start"),
         InlineKeyboardButton("▶️ Продолжить", callback_data="break_end")],
        [InlineKeyboardButton("📊 Статус РТО", callback_data="status"),
         InlineKeyboardButton("📈 Статистика", callback_data="stats")],
        [InlineKeyboardButton("💰 Заработок", callback_data="earnings"),
         InlineKeyboardButton("🏆 Достижения", callback_data="achievements")],
        [InlineKeyboardButton("🌤️ Погода", callback_data="weather"),
         InlineKeyboardButton("⏰ Планировщик", callback_data="scheduler")],
        [InlineKeyboardButton("👨‍👩‍👧 Семейный доступ", callback_data="family"),
         InlineKeyboardButton("🚙 Мои авто", callback_data="cars")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n🚕 Бот контроля РТО\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === ОБРАБОТЧИК КНОПОК ===
async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_menu":
        await back_to_menu(update, context)
    elif data == "shift_start":
        await cmd_start_shift(update, context)
    elif data == "shift_end":
        await cmd_end_shift(update, context)
    elif data == "break_start":
        await cmd_break_start(update, context)
    elif data == "break_end":
        await cmd_break_end(update, context)
    elif data == "status":
        await cmd_status(update, context)
    elif data == "stats":
        await cmd_stats(update, context)
    elif data == "earnings":
        await cmd_earnings(update, context)
    elif data == "achievements":
        await cmd_achievements(update, context)
    elif data == "weather":
        await cmd_weather(update, context)
    elif data == "scheduler":
        await cmd_settings(update, context)  # или cmd_scheduler
    elif data == "family":
        await cmd_family(update, context)
    elif data == "cars":
        await cmd_cars(update, context)
    elif data == "settings":
        await cmd_settings(update, context)

async def back_to_menu(update: Update, context):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🚗 Начать смену", callback_data="shift_start"),
         InlineKeyboardButton("⏹️ Закончить смену", callback_data="shift_end")],
        [InlineKeyboardButton("☕ Перерыв", callback_data="break_start"),
         InlineKeyboardButton("▶️ Продолжить", callback_data="break_end")],
        [InlineKeyboardButton("📊 Статус РТО", callback_data="status"),
         InlineKeyboardButton("📈 Статистика", callback_data="stats")],
        [InlineKeyboardButton("💰 Заработок", callback_data="earnings"),
         InlineKeyboardButton("🏆 Достижения", callback_data="achievements")],
        [InlineKeyboardButton("🌤️ Погода", callback_data="weather"),
         InlineKeyboardButton("⏰ Планировщик", callback_data="scheduler")],
        [InlineKeyboardButton("👨‍👩‍👧 Семейный доступ", callback_data="family"),
         InlineKeyboardButton("🚙 Мои авто", callback_data="cars")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    await query.edit_message_text(
        "🚕 Главное меню\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context):
    await update.message.reply_text("Используйте /start для открытия меню.")

def main():
    # Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Хендлеры
    application.add_handler(CommandHandler("start", start))
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
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^back_menu$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запуск
    logger.info("Starting bot...")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query", "inline_query"]
    )

if __name__ == "__main__":
    main()
