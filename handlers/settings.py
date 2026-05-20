from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.scheduler import AutoScheduler

scheduler = AutoScheduler()

async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки"""
    query = update.callback_query
    
    text = "⚙️ Настройки\n\n"
    text += "• Минское время ✅\n"
    text += "• Уведомления РТО ✅\n"
    
    keyboard = [
        [InlineKeyboardButton("⏰ Планировщик", callback_data="scheduler")],
        [InlineKeyboardButton("🔔 Уведомления", callback_data="notifications")],
        [InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def cmd_scheduler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Планировщик смен"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    next_shift = scheduler.get_next_shift(user_id)
    
    text = "⏰ Автопланировщик\n\n"
    
    if next_shift:
        from utils.time_utils import format_datetime, time_until
        text += (f"📅 Следующая смена: {next_shift['type']}\n"
                 f"🕐 Начало: {format_datetime(next_shift['start'])}\n"
                 f"🕐 Конец: {format_datetime(next_shift['end'])}\n"
                 f"⏳ До начала: {time_until(next_shift['start'])}\n\n")
    else:
        text += "Расписание не настроено.\n\n"
    
    text += "Формат: утро + вечер\nПример: 08:00-14:00 и 17:00-23:00"
    
    keyboard = [
        [InlineKeyboardButton("📝 Установить", callback_data="scheduler_set")],
        [InlineKeyboardButton("🔔 Напоминания", callback_data="scheduler_remind")],
        [InlineKeyboardButton("◀️ Назад", callback_data="settings")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def scheduler_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить расписание"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Отправьте расписание в формате:\n"
        "утро 08:00-14:00, вечер 17:00-23:00\n\n"
        "Или 'отмена'",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="scheduler")]])
    )
    context.user_data["awaiting_schedule"] = True

async def scheduler_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить расписание текстом"""
    if not context.user_data.get("awaiting_schedule"):
        return
    
    text = update.message.text.strip()
    
    if text.lower() == "отмена":
        context.user_data["awaiting_schedule"] = False
        await update.message.reply_text("Отменено.")
        return
    
    # Простой парсер
    try:
        # Пример: "утро 08:00-14:00, вечер 17:00-23:00"
        parts = text.lower().replace("утро", "").replace("вечер", "").replace(",", " ").split()
        morning = parts[0].split("-")
        evening = parts[1].split("-")
        
        user_id = update.effective_user.id
        scheduler.set_schedule(
            user_id,
            morning[0], morning[1],
            evening[0], evening[1]
        )
        
        context.user_data["awaiting_schedule"] = False
        
        await update.message.reply_text(
            f"✅ Расписание установлено!\n\n"
            f"Утро: {morning[0]}-{morning[1]}\n"
            f"Вечер: {evening[0]}-{evening[1]}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="scheduler")]])
        )
        
    except Exception as e:
        await update.message.reply_text(
            "❌ Неверный формат. Пример: утро 08:00-14:00, вечер 17:00-23:00"
        )