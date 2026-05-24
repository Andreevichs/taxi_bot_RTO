# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

MAIN_MENU_KEYBOARD = [
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартовое меню"""
    user = update.effective_user

    reply_markup = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"🚕 Бот контроля РТО для таксистов Беларуси\n"
        f"⏰ Минское время\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок меню и уведомлений"""
    query = update.callback_query
    await query.answer()

    data = query.data

    from .rto import cmd_start_shift, cmd_end_shift, cmd_break_start, cmd_break_end, cmd_status
    from .stats import cmd_stats, cmd_earnings, cmd_achievements, cmd_weather
    from .family import cmd_family
    from .cars import cmd_cars
    from .settings import (
        cmd_settings, cmd_scheduler, scheduler_set, scheduler_del,
        set_rate_start, cmd_test_menu, test_break_30, test_critical_30
    )

    handlers = {
        "shift_start": cmd_start_shift,
        "shift_end": cmd_end_shift,
        "break_start": cmd_break_start,
        "break_end": cmd_break_end,
        "status": cmd_status,
        "stats": cmd_stats,
        "earnings": cmd_earnings,
        "achievements": cmd_achievements,
        "weather": cmd_weather,
        "scheduler": cmd_scheduler,
        "family": cmd_family,
        "cars": cmd_cars,
        "settings": cmd_settings,
        "back_menu": back_to_menu,
        # Тестовые кнопки
        "test_menu": cmd_test_menu,
        "test_break_30": test_break_30,
        "test_critical_30": test_critical_30,
        # Настройки
        "scheduler_set": scheduler_set,
        "scheduler_del": scheduler_del,
        "set_rate": set_rate_start,
    }

    handler = handlers.get(data)
    if handler:
        await handler(update, context)
    else:
        await query.edit_message_text("❌ Неизвестная команда")

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в меню"""
    query = update.callback_query

    try:
        await query.edit_message_text(
            "🚕 Главное меню\n\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)
        )
    except Exception:
        # Если сообщение нельзя отредактировать (например, уведомление), отправляем новое
        await query.message.reply_text(
            "🚕 Главное меню\n\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)
        )
