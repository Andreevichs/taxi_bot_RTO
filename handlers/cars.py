from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from utils.database import db_manager

# Состояния для ConversationHandler
WAITING_CAR_BRAND = 1
WAITING_CAR_MODEL = 2
WAITING_CAR_PLATE = 3
WAITING_CAR_COLOR = 4

async def cmd_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню автомобилей"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    cars = db_manager.get_all_cars(user_id)
    active_car = db_manager.get_active_car(user_id)

    text = "🚙 Мои автомобили\n\n"

    if not cars:
        text += "У вас пока нет добавленных автомобилей.\n"
    else:
        for car in cars:
            marker = " ✅ (по умолчанию)" if active_car and car['id'] == active_car['id'] else ""
            text += f"• {car['brand']} {car['model']} ({car['license_plate']}){marker}\n"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить авто", callback_data="car_add")],
        [InlineKeyboardButton("⭐ Сделать активным", callback_data="car_set_active")],
        [InlineKeyboardButton("🗑 Удалить авто", callback_data="car_delete")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_main")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === ДОБАВЛЕНИЕ АВТО (ConversationHandler) ===

async def car_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления авто"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🚗 Добавление автомобиля\n\n"
        "Шаг 1/4: Введите марку авто (например: Ford):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="cars")]])
    )
    return WAITING_CAR_BRAND

async def car_brand_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получили марку"""
    context.user_data['car_brand'] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 2/4: Введите модель (например: Focus):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="cars")]])
    )
    return WAITING_CAR_MODEL

async def car_model_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получили модель"""
    context.user_data['car_model'] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 3/4: Введите номерной знак (например: АВ1234-5):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="cars")]])
    )
    return WAITING_CAR_PLATE

async def car_plate_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получили номер"""
    context.user_data['car_plate'] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 4/4: Введите цвет (например: Серебристый):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="cars")]])
    )
    return WAITING_CAR_COLOR

async def car_color_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получили цвет, сохраняем в БД"""
    user_id = update.effective_user.id
    color = update.message.text.strip()

    db_manager.add_car(
        user_id=user_id,
        brand=context.user_data['car_brand'],
        model=context.user_data['car_model'],
        plate=context.user_data['car_plate'],
        color=color
    )

    # Очищаем временные данные
    for key in ['car_brand', 'car_model', 'car_plate']:
        context.user_data.pop(key, None)

    await update.message.reply_text(
        "✅ Автомобиль успешно добавлен!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ К списку авто", callback_data="cars")]])
    )
    return ConversationHandler.END

async def car_add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления"""
    query = update.callback_query
    await query.answer()
    # Очищаем временные данные
    for key in ['car_brand', 'car_model', 'car_plate']:
        context.user_data.pop(key, None)
    await cmd_cars(update, context)
    return ConversationHandler.END

# === УСТАНОВКА АКТИВНОГО АВТО ===

async def car_set_active_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор активного авто"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    cars = db_manager.get_all_cars(user_id)

    if not cars:
        await query.edit_message_text(
            "❌ У вас нет автомобилей.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="cars")]])
        )
        return

    keyboard = []
    for car in cars:
        text = f"{car['brand']} {car['model']}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"activate_car_{car['id']}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="cars")])

    await query.edit_message_text(
        "Выберите активный автомобиль:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def car_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активировать выбранное авто"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    car_id = int(query.data.replace("activate_car_", ""))

    # Деактивируем все, активируем выбранное
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cars SET is_active = 0 WHERE user_id = ?', (user_id,))
    cursor.execute('UPDATE cars SET is_active = 1 WHERE id = ? AND user_id = ?', (car_id, user_id))
    conn.commit()
    conn.close()

    await query.edit_message_text(
        "✅ Автомобиль выбран по умолчанию!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ К списку авто", callback_data="cars")]])
    )

# === УДАЛЕНИЕ АВТО ===

async def car_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало удаления"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    cars = db_manager.get_all_cars(user_id)

    if not cars:
        await query.edit_message_text(
            "❌ У вас нет автомобилей для удаления.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="cars")]])
        )
        return

    keyboard = []
    for car in cars:
        text = f"🗑 {car['brand']} {car['model']}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"delete_car_{car['id']}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="cars")])

    await query.edit_message_text(
        "Какой автомобиль удалить?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def car_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    car_id = int(query.data.replace("delete_car_", ""))

    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cars WHERE id = ? AND user_id = ?', (car_id, user_id))
    conn.commit()
    conn.close()

    await query.edit_message_text(
        "🗑 Автомобиль удалён!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ К списку авто", callback_data="cars")]])
    )

# === ConversationHandler для добавления авто ===
car_add_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(car_add_start, pattern='^car_add$')],
    states={
        WAITING_CAR_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_brand_received)],
        WAITING_CAR_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_model_received)],
        WAITING_CAR_PLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_plate_received)],
        WAITING_CAR_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_color_received)],
    },
    fallbacks=[CallbackQueryHandler(car_add_cancel, pattern='^cars$')]
)
