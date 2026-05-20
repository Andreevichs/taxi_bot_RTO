from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import MAX_FAMILY_MEMBERS
import database as db

ASK_MEMBER_ID = 1


async def cmd_family(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление семейным доступом"""
    query = update.callback_query
    user_id = update.effective_user.id

    members = db.get_family_members(user_id)

    text = "👨‍👩‍👧 Семейный доступ\n\n"

    if members:
        text += "Добавленные члены семьи:\n"
        for member in members:
            text += f"• {member['name']} (ID: {member['member_id']})\n"
    else:
        text += "Пока никого не добавлено.\n"

    text += f"\nМакс: {MAX_FAMILY_MEMBERS} человек"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="family_add")],
        [InlineKeyboardButton("🗑 Удалить", callback_data="family_remove")],
        [InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def family_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление члена семьи"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    current_count = db.get_family_count(user_id)

    if current_count >= MAX_FAMILY_MEMBERS:
        await query.edit_message_text(
            f"❌ Лимит {MAX_FAMILY_MEMBERS} человек достигнут!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="family")]
            ])
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "Отправьте ID пользователя Telegram (число).\n\n"
        "Чтобы узнать ID, попросите человека написать боту @userinfobot\n\n"
        "⚠️ Пользователь должен сначала написать этому боту /start",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Отмена", callback_data="family")]
        ])
    )
    return ASK_MEMBER_ID


async def family_add_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить члена семьи"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        member_id = int(text)
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный ID. Отправьте число.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Отмена", callback_data="family")]
            ])
        )
        return ASK_MEMBER_ID

    if member_id == user_id:
        await update.message.reply_text(
            "❌ Нельзя добавить себя!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="family")]
            ])
        )
        return ConversationHandler.END

    if db.get_family_count(user_id) >= MAX_FAMILY_MEMBERS:
        await update.message.reply_text(
            f"❌ Лимит {MAX_FAMILY_MEMBERS} человек!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="family")]
            ])
        )
        return ConversationHandler.END

    success = db.add_family_member(user_id, member_id, f"Пользователь {member_id}")

    if success:
        await update.message.reply_text(
            f"✅ Пользователь {member_id} добавлен!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="family")]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ Уже добавлен или ошибка!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="family")]
            ])
        )

    return ConversationHandler.END


async def family_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить члена семьи"""
    query = update.callback_query
    user_id = update.effective_user.id

    members = db.get_family_members(user_id)

    if not members:
        await query.edit_message_text(
            "Некого удалять.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="family")]
            ])
        )
        return

    keyboard = []
    for member in members:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑 {member['name']}",
                callback_data=f"family_del_{member['member_id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="family")])

    await query.edit_message_text("Кого удалить?", reply_markup=InlineKeyboardMarkup(keyboard))


async def family_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтвердить удаление"""
    query = update.callback_query
    user_id = update.effective_user.id

    data = query.data
    member_id = int(data.replace("family_del_", ""))

    db.remove_family_member(user_id, member_id)

    await query.edit_message_text(
        "✅ Удалено!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="family")]
        ])
    )
