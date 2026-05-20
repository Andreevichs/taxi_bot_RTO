# handlers/stats.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.rto_logic import get_session
from utils.time_utils import format_duration, now_minsk, get_week_start
from utils.weather import get_minsk_weather
from utils.earnings import predict_daily_earnings, predict_weekly_earnings
from utils.achievements import AchievementManager
import database as db

achievements = AchievementManager()


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    query = update.callback_query
    user_id = update.effective_user.id
    session = get_session(user_id)

    weekly = session.get_weekly_stats()
    status = session.get_status()

    # Реальная статистика за неделю
    week_start = get_week_start()
    week_shifts = db.get_user_shifts(user_id, since=week_start)

    text = (f"📈 Статистика\n\n"
            f"📆 За неделю:\n"
            f"• Смен: {weekly['shifts']}\n"
            f"• За рулём: {format_duration(weekly['driving'])}\n"
            f"• Осталось: {format_duration(weekly['remaining'])}\n\n"
            f"📅 Сегодня:\n"
            f"• За рулём: {format_duration(status['driving_today'])}\n"
            f"• Смен: {status['shifts_today']}\n\n")

    if weekly['limit_exceeded']:
        text += "⚠️ Лимит 56 часов превышен!\n"

    # Добавить среднюю продолжительность смены
    if week_shifts:
        total_driving = sum(
            (s["end_time"] - s["start_time"]).total_seconds() if s["end_time"] else 0
            for s in week_shifts
        )
        avg_hours = (total_driving / len(week_shifts) / 3600) if week_shifts else 0
        text += f"📊 Средняя смена: {avg_hours:.1f} ч\n"

    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Прогноз заработка на основе реальной статистики"""
    query = update.callback_query
    user_id = update.effective_user.id

    # Получить средние часы за неделю
    week_start = get_week_start()
    week_shifts = db.get_user_shifts(user_id, since=week_start)

    if week_shifts:
        total_hours = sum(
            (s["end_time"] - s["start_time"]).total_seconds() / 3600 if s["end_time"] else 0
            for s in week_shifts
        )
        avg_daily = total_hours / len(week_shifts) if week_shifts else 0
        avg_weekly = total_hours
    else:
        avg_daily = 8
        avg_weekly = 40

    daily = predict_daily_earnings(user_id, avg_daily)
    weekly = predict_weekly_earnings(user_id, avg_weekly)

    text = (f"💰 Прогноз заработка\n\n"
            f"📅 На день (~{daily['hours']} часов):\n"
            f"• Примерно: {daily['total']} BYN\n\n"
            f"📆 На неделю (~{weekly['hours']} часов):\n"
            f"• Всего: {weekly['total']} BYN\n"
            f"• В день: ~{weekly['daily_avg']} BYN\n\n"
            f"💵 Ваша ставка: {daily['rate']} BYN/час\n\n"
            f"💡 Чтобы изменить ставку: Настройки → Ставка")

    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Достижения"""
    query = update.callback_query
    user_id = update.effective_user.id

    user_ach = achievements.get_user_achievements(user_id)
    progress = achievements.get_progress(user_id)

    text = f"🏆 Достижения ({progress['earned']}/{progress['total']}) — {progress['percent']}%\n\n"

    if user_ach:
        for ach in user_ach:
            text += f"✅ {ach['name']}\n   {ach['desc']}\n\n"
    else:
        text += "Пока нет достижений. Начните смену! 🚕\n\n"

    # Показать недоступные
    from config import ACHIEVEMENTS
    earned_ids = {a['id'] for a in user_ach}
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id not in earned_ids:
            text += f"⬜ {ach['name']}\n   {ach['desc']}\n\n"

    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Погода"""
    query = update.callback_query

    weather = await get_minsk_weather()

    if weather:
        text = f"🌤️ Погода в Минске:\n\n{weather}\n\nХорошей смены! 🚕"
    else:
        text = "❌ Не удалось получить погоду. Попробуйте позже."

    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
