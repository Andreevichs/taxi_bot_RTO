# handlers/rto.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.rto_logic import get_session
from utils.time_utils import now_minsk, format_duration, format_datetime
from utils.achievements import AchievementManager
from utils.earnings import calculate_earnings
import database as db

achievements = AchievementManager()


async def cmd_start_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать смену"""
    query = update.callback_query
    user_id = update.effective_user.id
    session = get_session(user_id)

    car = db.get_default_car(user_id)

    result = session.start_shift(car)

    if result["ok"]:
        hour = now_minsk().hour
        new_ach = achievements.check_achievements(user_id, "shift_start", {"hour": hour})

        # ЗАПУСТИТЬ МОНИТОРИНГ СМЕНЫ (уведомления)
        from utils.scheduler import AutoScheduler
        scheduler = AutoScheduler()
        scheduler.start_shift_monitoring(user_id)

        text = (f"🟢 Смена начата!\n"
                f"🕐 {format_datetime(result['start'])}\n"
                f"🚙 Авто: {car}\n\n"
                f"Удачной работы! 🚕")

        # Показать предупреждения (если есть)
        if result.get("warnings"):
            text += "\n\n⚠️ Внимание:\n"
            for w in result["warnings"]:
                text += f"• {w}\n"

        if new_ach:
            text += "\n\n🏆 Новое достижение!\n"
            for ach in new_ach:
                text += f"• {ach['name']} — {ach['desc']}\n"

        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(f"❌ {result['error']}", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_end_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Закончить смену"""
    query = update.callback_query
    user_id = update.effective_user.id
    session = get_session(user_id)

    result = session.end_shift()

    if result["ok"]:
        # ОСТАНОВИТЬ МОНИТОРИНГ СМЕНЫ
        from utils.scheduler import AutoScheduler
        scheduler = AutoScheduler()
        scheduler.stop_shift_monitoring(user_id)

        stats = result["stats"]
        
        # Проверить достижения
        new_ach = achievements.check_achievements(
            user_id, "shift_end",
            {
                "safe_hours": stats["driving"].total_seconds() / 3600,
                "earnings": calculate_earnings(user_id, stats["driving"])["total"]
            }
        )

        text = (f"⏹️ Смена завершена!\n"
                f"🕐 {format_datetime(result.get('end_time', now_minsk()))}\n"
                f"🚗 За рулём: {format_duration(stats['driving'])}\n"
                f"☕ Перерывы: {format_duration(stats['breaks'])}\n"
                f"🚙 Авто: {stats['car']}\n")

        if result.get("warnings"):
            text += "\n⚠️ Внимание:\n"
            for w in result["warnings"]:
                text += f"• {w}\n"

        if new_ach:
            text += "\n🏆 Новое достижение!\n"
            for ach in new_ach:
                text += f"• {ach['name']} — {ach['desc']}\n"

        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(f"❌ {result['error']}", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_break_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать перерыв"""
    query = update.callback_query
    user_id = update.effective_user.id
    session = get_session(user_id)

    result = session.start_break()

    if result["ok"]:
        text = f"☕ Перерыв начат!\n🕐 {format_datetime(result['start'])}"
        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(f"❌ {result['error']}", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_break_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Закончить перерыв"""
    query = update.callback_query
    user_id = update.effective_user.id
    session = get_session(user_id)

    result = session.end_break()

    if result["ok"]:
        text = f"▶️ Перерыв окончен!\n🕐 {format_datetime(result['end'])}"
        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
        await query.edit_message_text(f"❌ {result['error']}", reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус РТО"""
    query = update.callback_query
    user_id = update.effective_user.id
    session = get_session(user_id)

    status = session.get_status()
    weekly = session.get_weekly_stats()

    if status["active"]:
        fatigue = status["fatigue"]
        if fatigue < 30:
            fatigue_emoji = "🟢"
        elif fatigue < 60:
            fatigue_emoji = "🟡"
        else:
            fatigue_emoji = "🔴"

        text = (f"📊 Текущая смена\n\n"
                f"🕐 Длительность: {format_duration(status['shift_duration'])}\n"
                f"🚗 За рулём: {format_duration(status['current_stats']['driving'])}\n"
                f"☕ Перерывы: {format_duration(status['current_stats']['breaks'])}\n"
                f"🚙 Авто: {status['car']}\n"
                f"😴 Усталость: {fatigue_emoji} {fatigue}%\n\n"
                f"📅 Сегодня за рулём: {format_duration(status['driving_today'])}\n"
                f"📆 За неделю: {format_duration(weekly['driving'])}\n"
                f"⏳ Осталось неделя: {format_duration(weekly['remaining'])}")

        if status["warnings"]:
            text += "\n\n⚠️ Предупреждения:\n"
            for w in status["warnings"]:
                text += f"• {w}\n"
    else:
        text = (f"📊 Нет активной смены\n\n"
                f"📅 Сегодня за рулём: {format_duration(status['driving_today'])}\n"
                f"📆 Смен сегодня: {status['shifts_today']}\n"
                f"📊 За неделю: {format_duration(weekly['driving'])}\n"
                f"⏳ Осталось неделя: {format_duration(weekly['remaining'])}")

    if weekly["limit_exceeded"]:
        text += "\n\n⚠️ Лимит 56 часов превышен!"

    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
