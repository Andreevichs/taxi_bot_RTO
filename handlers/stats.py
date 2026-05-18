from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .rto import get_session, achievements
from utils.time_utils import format_duration
from utils.weather import get_minsk_weather
from utils.earnings import predict_daily_earnings, predict_weekly_earnings

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    session = get_session(user_id)
    weekly = session.get_weekly_stats()
    status = session.get_status()
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
    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def cmd_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    daily = predict_daily_earnings(8)
    weekly = predict_weekly_earnings(40)
    text = (f"💰 Прогноз заработка\n\n"
            f"📅 На день (8 часов):\n"
            f"• Часов: {daily['hours']}\n"
            f"• Примерно: {daily['total']} BYN\n\n"
            f"📆 На неделю (40 часов):\n"
            f"• Всего: {weekly['total']} BYN\n"
            f"• В день: ~{weekly['daily_avg']} BYN\n\n"
            f"💡 При ставке {daily['base']/daily['hours']:.0f} BYN/час")
    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def cmd_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    from config import ACHIEVEMENTS
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id not in [a['id'] for a in user_ach]:
            text += f"⬜ {ach['name']}\n   {ach['desc']}\n\n"
    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    weather = await get_minsk_weather()
    if weather:
        text = f"🌤️ Погода в Минске:\n\n{weather}\n\nХорошей смены! 🚕"
    else:
        text = "❌ Не удалось получить погоду. Попробуйте позже."
    keyboard = [[InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
