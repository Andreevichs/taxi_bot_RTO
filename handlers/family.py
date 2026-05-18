from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from config import MAX_FAMILY_MEMBERS

# Хранилище в памяти (в продакшене заменить на БД)
family_groups: dict[int, list[int]] = {}
family_names: dict[int, str] = {}

ASK_MEMBER_ID = 1

async def cmd_family(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню семейного доступа"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    members = family_groups.get(user_id, [])

    text = "👨‍👩‍👧 Семейный доступ\n\n"
    if members:
        text += "Добавленные члены семьи:\n"
        for mid in members:
            name = family_names.get(mid, f"ID: {mid}")
            text += f"• {name}\n"
    else:
        text += "Пока никого не добавлено.\n"

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
    """Получили ID, сохраняем"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        member_id = int(text)
    except ValueError:
        await update.message.reply_text("❌ Неверный ID. Отправьте число.")
        return ASK_MEMBER_ID

    if user_id not in family_groups:
        family_groups[user_id] = []

    if len(family_groups[user_id]) >= MAX_FAMILY_MEMBERS:
        await update.message.reply_text(f"❌ Лимит {MAX_FAMILY_MEMBERS} человек!")
        return ConversationHandler.END

    if member_id in family_groups[user_id]:
        await update.message.reply_text("❌ Уже добавлен!")
        return ConversationHandler.END

    family_groups[user_id].append(member_id)
    family_names[member_id] = f"Пользователь {member_id}"

    await update.message.reply_text(f"✅ Пользователь {member_id} добавлен!")
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
    members = family_groups.get(user_id, [])

    if not members:
        await query.edit_message_text(
            "Некого удалять.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="family")]])
        )
        return

    keyboard = []
    for mid in members:
        name = family_names.get(mid, f"ID: {mid}")
        keyboard.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"family_del_{mid}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="family")])

    await query.edit_message_text("Кого удалить?", reply_markup=InlineKeyboardMarkup(keyboard))

async def family_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    member_id = int(data.replace("family_del_", ""))

    if user_id in family_groups and member_id in family_groups[user_id]:
        family_groups[user_id].remove(member_id)
        family_names.pop(member_id, None)
        await query.edit_message_text("✅ Удалено!", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="family")]
        ]))
    else:
        await query.edit_message_text("❌ Ошибка", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="family")]
        ]))

# === ConversationHandler для добавления члена семьи ===
family_add_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(family_add_start, pattern='^family_add$')],
    states={
        ASK_MEMBER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, family_add_done)]
    },
    fallbacks=[CallbackQueryHandler(family_add_cancel, pattern='^family$')],
    per_message=True  # <-- ИСПРАВЛЕНИЕ: убирает PTBUserWarning
)
