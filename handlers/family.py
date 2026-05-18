from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from config import MAX_FAMILY_MEMBERS
from utils.database import db_manager

ASK_MEMBER_ID = 1

async def cmd_family(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню семейного доступа"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # Получаем членов семьи из БД
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM family_members WHERE user_id = ? AND status = "accepted"', (user_id,))
    members = cursor.fetchall()
    conn.close()
    
    text = "👨‍👩‍👧 Семейный доступ\n\n"
    
    if not members:
        text += "Пока никого не добавлено.\n"
    else:
        text += "Добавленные члены семьи:\n"
        for member in members:
            text += f"• {member['member_name']} (ID: {member['member_user_id']})\n"
    
    text += f"\nМакс: {MAX_FAMILY_MEMBERS} человек"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="family_add")],
        [InlineKeyboardButton("🗑 Удалить", callback_data="family_remove")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def family_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления члена семьи"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👨‍👩‍👧 Добавление члена семьи\n\n"
        "Отправьте ID пользователя Telegram (число).\n\n"
        "💡 Чтобы узнать ID, попросите человека написать боту @userinfobot",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="family")]])
    )
    return ASK_MEMBER_ID

async def family_add_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получили ID, сохраняем в БД"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        member_id = int(text)
    except ValueError:
        await update.message.reply_text("❌ Неверный ID. Отправьте число.")
        return ASK_MEMBER_ID
    
    # Проверяем лимит
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM family_members WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()['count']
    
    if count >= MAX_FAMILY_MEMBERS:
        conn.close()
        await update.message.reply_text(f"❌ Лимит {MAX_FAMILY_MEMBERS} человек!")
        return ConversationHandler.END
    
    # Проверяем, не добавлен ли уже
    cursor.execute('SELECT 1 FROM family_members WHERE user_id = ? AND member_user_id = ?', 
                   (user_id, member_id))
    if cursor.fetchone():
        conn.close()
        await update.message.reply_text("❌ Уже добавлен!")
        return ConversationHandler.END
    
    # Добавляем в БД
    cursor.execute('''
        INSERT INTO family_members (user_id, member_user_id, member_name, status)
        VALUES (?, ?, ?, 'pending')
    ''', (user_id, member_id, f"Пользователь {member_id}"))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ Пользователь {member_id} добавлен!\n\n"
        f"📩 Ему отправлено приглашение. После подтверждения он появится в списке."
    )
    return ConversationHandler.END

async def family_add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления"""
    query = update.callback_query
    await query.answer()
    await cmd_family(update, context)
    return ConversationHandler.END

async def family_remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало удаления"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM family_members WHERE user_id = ? AND status = "accepted"', (user_id,))
    members = cursor.fetchall()
    conn.close()
    
    if not members:
        await query.edit_message_text(
            "Некого удалять.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="family")]])
        )
        return
    
    keyboard = []
    for member in members:
        name = member['member_name']
        keyboard.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"family_del_{member['id']}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="family")])
    
    await query.edit_message_text("Кого удалить?", reply_markup=InlineKeyboardMarkup(keyboard))

async def family_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # Получаем ID записи (не member_user_id!)
    record_id = int(query.data.replace("family_del_", ""))
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM family_members WHERE id = ? AND user_id = ?', (record_id, user_id))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(
        "✅ Удалено!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="family")]])
    )

# === ConversationHandler для добавления члена семьи ===
family_add_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(family_add_start, pattern='^family_add$')],
    states={
        ASK_MEMBER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, family_add_done)]
    },
    fallbacks=[CallbackQueryHandler(family_add_cancel, pattern='^family$')]
)
