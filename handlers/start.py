from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from utils.database import db_manager
from keyboards.inline import main_menu_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_manager.add_user(user.id, user.username or '', user.first_name or '', user.last_name or '')
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я твой помощник РТО. Данные теперь сохраняются надежно!\n"
        "Выбери действие в меню:",
        reply_markup=main_menu_keyboard()
    )

async def reset_data_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⚠️ Очищаю...")
    db_manager.clear_all_user_data(query.from_user.id)
    if query.from_user.id in context.user_data:
        context.user_data[query.from_user.id].clear()
    await query.edit_message_text(
        "🗑 **Данные очищены!**\nНажми /start, чтобы начать заново.",
        parse_mode='Markdown'
    )

start_handler = CommandHandler('start', start_command)
reset_data_handler = CallbackQueryHandler(reset_data_callback, pattern='^reset_data$')
