from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from utils.database import db_manager
from keyboards.inline import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Сохраняем пользователя в БД
    db_manager.add_user(
        user_id=user_id,
        username=user.username or '',
        first_name=user.first_name or '',
        last_name=user.last_name or ''
    )
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🚕 Я твой помощник для контроля РТО (Режима Труда и Отдыха).\n"
        "✅ Все данные сохраняются в надёжной базе.\n"
        "✅ Слежу за временем за рулём и напоминаю о перерывах.\n\n"
        "Выбери действие в меню:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=main_menu_keyboard())

async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Назад в меню'"""
    query = update.callback_query
    await query.answer()
    await start_command(update, context)

async def reset_data_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
        
    user_id = query.from_user.id
    
    await query.answer("⚠️ Начинаю полную очистку...")
    
    try:
        db_manager.clear_all_user_data(user_id)
        
        if user_id in context.user_data:
            context.user_data.clear()
        
        await query.edit_message_text(
            "🗑 *Данные успешно очищены!*\n\n"
            "Вся статистика, машина и настройки удалены безвозвратно.\n"
            "Теперь ты как новый пользователь.\n\n"
            "Нажми /start, чтобы начать заново.",
            parse_mode='MarkdownV2',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Начать заново", callback_data="start_restart")]])
        )
    except Exception as e:
        logger.error(f"Error clearing data for {user_id}: {e}")
        await query.edit_message_text("❌ Произошла ошибка при очистке данных. Попробуйте позже.")

async def restart_after_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start_command(update, context)

# === ХЕНДЛЕРЫ ===
start_handler = CommandHandler('start', start_command)
reset_data_handler = CallbackQueryHandler(reset_data_callback, pattern='^reset_data$')
restart_handler = CallbackQueryHandler(restart_after_reset, pattern='^start_restart$')
back_handler = CallbackQueryHandler(back_to_main_callback, pattern='^back_to_main$')  # НОВЫЙ
