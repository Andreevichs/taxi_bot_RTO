# handlers/settings.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.scheduler import AutoScheduler
from utils.time_utils import format_datetime, time_until, parse_schedule_time
import database as db

scheduler = AutoScheduler()

ASK_SCHEDULE = 2
ASK_RATE = 3

async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки"""
    query = update.callback_query
    user_id = update.effective_user.id

    settings = db.get_user_settings(user_id)

    text = "⚙️ Настройки\n\n"
    text += f"• Минское время ✅\n"
    text += f"• Уведомления РТО ✅\n"
    text += f"• Ставка: {settings['hourly_rate']} BYN/час\n"

    keyboard = [
        [InlineKeyboardButton("💵 Изменить ставку", callback_data="set_rate")],
        [InlineKeyboardButton("⏰ Планировщик", callback_data="scheduler")],
        [InlineKeyboardButton("🔔 Уведомления", callback_data="notifications")],
        [InlineKeyboardButton("🧪 Тест уведомлений", callback_data="test_menu")],
        [InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_test_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню тестовых уведомлений"""
    query = update.callback_query
    user_id = update.effective_user.id

    text = ("🧪 Тестовые уведомления\n\n"
            "Выберите тест:\n\n"
            "1️⃣ Уведомление через 30 сек — типа 'на отдых'\n"
            "2️⃣ Уведомление через 30 сек — типа 'критично РТО'\n\n"
            "Уведомление придёт отдельным сообщением.")

    keyboard = [
        [InlineKeyboardButton("☕ Тест: Перерыв (30 сек)", callback_data="test_break_30")],
        [InlineKeyboardButton("🔴 Тест: Критично РТО (30 сек)", callback_data="test_critical_30")],
        [InlineKeyboardButton("◀️ Назад", callback_data="settings")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def test_break_30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тест: уведомление о перерыве через 30 секунд"""
    query = update.callback_query
    user_id = update.effective_user.id

    scheduler.send_test_notification(
        user_id,
        delay_seconds=30,
        message=("☕ ТЕСТ: Пора на перерыв!\n\n"
                 "🔴 РТО: Вы за рулём 4.5 часа!\n"
                 "⚠️ Нужен перерыв 45 минут!\n"
                 "Нажмите ☕ Перерыв в меню бота.")
    )

    await query.edit_message_text(
        "✅ Тестовое уведомление запланировано!\n\n"
        "☕ Через 30 секунд придёт сообщение типа 'на отдых'.\n\n"
        "Если не придёт — проверь логи Render.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="test_menu")]
        ])
    )


async def test_critical_30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тест: критичное уведомление РТО через 30 секунд"""
    query = update.callback_query
    user_id = update.effective_user.id

    scheduler.send_test_notification(
        user_id,
        delay_seconds=30,
        message=("🔴 ТЕСТ: КРИТИЧНОЕ УВЕДОМЛЕНИЕ РТО!\n\n"
                 "⚠️ Смена длится 10:30!\n"
                 "Максимум: 10:00\n\n"
                 "❌ Немедленно завершите смену!")
    )

    await query.edit_message_text(
        "✅ Тестовое уведомление запланировано!\n\n"
        "🔴 Через 30 секунд придёт критичное сообщение РТО.\n\n"
        "Если не придёт — проверь логи Render.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="test_menu")]
        ])
    )


async def cmd_scheduler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Планировщик смен"""
    query = update.callback_query
    user_id = update.effective_user.id

    next_shift = scheduler.get_next_shift(user_id)

    text = "⏰ Автопланировщик\n\n"

    if next_shift:
        text += (f"📅 Следующая смена: {next_shift['type']}\n"
                 f"🕐 Начало: {format_datetime(next_shift['start'])}\n"
                 f"🕐 Конец: {format_datetime(next_shift['end'])}\n"
                 f"⏳ До начала: {time_until(next_shift['start'])}\n\n")
    else:
        text += "Расписание не настроено.\n\n"

    text += "Формат: утро + вечер\nПример: 08:00-14:00 и 17:00-23:00"

    keyboard = [
        [InlineKeyboardButton("📝 Установить", callback_data="scheduler_set")],
        [InlineKeyboardButton("🗑 Удалить", callback_data="scheduler_del")],
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
        "Или просто: 08:00-14:00 17:00-23:00\n\n"
        "Или 'отмена'",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Отмена", callback_data="scheduler")]
        ])
    )
    context.user_data["awaiting_schedule"] = True


async def scheduler_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить расписание текстом"""
    if not context.user_data.get("awaiting_schedule"):
        return

    text = update.message.text.strip().lower()

    if text == "отмена":
        context.user_data["awaiting_schedule"] = False
        await update.message.reply_text(
            "Отменено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="scheduler")]
            ])
        )
        return

    try:
        cleaned = text.replace("утро", "").replace("вечер", "").replace("и", "").replace(",", " ")
        parts = [p for p in cleaned.split() if p and "-" in p]

        if len(parts) < 2:
            raise ValueError("Нужно два интервала")

        morning = parts[0].split("-")
        evening = parts[1].split("-")

        if len(morning) != 2 or len(evening) != 2:
            raise ValueError("Неверный формат интервалов")

        parse_schedule_time(morning[0])
        parse_schedule_time(morning[1])
        parse_schedule_time(evening[0])
        parse_schedule_time(evening[1])

        user_id = update.effective_user.id
        scheduler.set_schedule(
            user_id,
            morning[0].strip(), morning[1].strip(),
            evening[0].strip(), evening[1].strip()
        )

        context.user_data["awaiting_schedule"] = False

        await update.message.reply_text(
            f"✅ Расписание установлено!\n\n"
            f"🌅 Утро: {morning[0]}-{morning[1]}\n"
            f"🌙 Вечер: {evening[0]}-{evening[1]}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="scheduler")]
            ])
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Неверный формат.\n\n"
            f"Примеры:\n"
            f"• утро 08:00-14:00, вечер 17:00-23:00\n"
            f"• 08:00-14:00 17:00-23:00\n\n"
            f"Ошибка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="scheduler")]
            ])
        )


async def scheduler_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить расписание"""
    query = update.callback_query
    user_id = update.effective_user.id

    scheduler.remove_schedule(user_id)

    await query.edit_message_text(
        "✅ Расписание удалено!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="scheduler")]
        ])
    )


async def set_rate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать изменение ставки"""
    query = update.callback_query
    await query.answer()

    settings = db.get_user_settings(update.effective_user.id)

    await query.edit_message_text(
        f"Текущая ставка: {settings['hourly_rate']} BYN/час\n\n"
        f"Отправьте новую ставку (число, например: 30)\n\n"
        f"Или 'отмена'",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Отмена", callback_data="settings")]
        ])
    )
    context.user_data["awaiting_rate"] = True


async def set_rate_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить новую ставку"""
    if not context.user_data.get("awaiting_rate"):
        return

    text = update.message.text.strip()

    if text.lower() == "отмена":
        context.user_data["awaiting_rate"] = False
        await update.message.reply_text(
            "Отменено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="settings")]
            ])
        )
        return

    try:
        rate = float(text.replace(",", "."))
        if rate <= 0 or rate > 1000:
            raise ValueError("Ставка должна быть от 0.1 до 1000")

        user_id = update.effective_user.id
        db.set_hourly_rate(user_id, rate)

        context.user_data["awaiting_rate"] = False

        await update.message.reply_text(
            f"✅ Ставка изменена на {rate} BYN/час!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="settings")]
            ])
        )

    except ValueError as e:
        await update.message.reply_text(
            f"❌ Неверное значение: {str(e)}\nОтправьте число (например: 30)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="settings")]
            ])
        )
