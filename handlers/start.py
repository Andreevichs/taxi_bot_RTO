from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"🚕 Бот контроля РТО для таксистов Беларуси\n"
        f"⏰ Минское время\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "shift_start":
        from .rto import cmd_start_shift
        await cmd_start_shift(update, context)
    elif data == "shift_end":
        from .rto import cmd_end_shift
        await cmd_end_shift(update, context)
    elif data == "break_start":
        from .rto import cmd_break_start
        await cmd_break_start(update, context)
    elif data == "break_end":
        from .rto import cmd_break_end
        await cmd_break_end(update, context)
    elif data == "status":
        from .rto import cmd_status
        await cmd_status(update, context)
    elif data == "stats":
        from .stats import cmd_stats
        await cmd_stats(update, context)
    elif data == "earnings":
        from .stats import cmd_earnings
        await cmd_earnings(update, context)
    elif data == "achievements":
        from .stats import cmd_achievements
        await cmd_achievements(update, context)
    elif data == "weather":
        from .stats import cmd_weather
        await cmd_weather(update, context)
    elif data == "scheduler":
        from .settings import cmd_scheduler
        await cmd_scheduler(update, context)
    elif data == "family":
        from .family import cmd_family
        await cmd_family(update, context)
    elif data == "cars":
        from .cars import cmd_cars
        await cmd_cars(update, context)
    elif data == "settings":
        from .settings import cmd_settings
        await cmd_settings(update, context)
    elif data == "back_menu":
        await back_to_menu(update, context)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
