from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Хранилище авто (в продакшене — БД)
user_cars: dict[int, list[str]] = {}

async def cmd_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление авто"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    cars = user_cars.get(user_id, ["Основное"])
    default = context.user_data.get("default_car", "Основное")
    
    text = "🚙 Мои автомобили\n\n"
    for car in cars:
        marker = " ✅" if car == default else ""
        text += f"• {car}{marker}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить авто", callback_data="car_add")],
        [InlineKeyboardButton("⭐ По умолчанию", callback_data="car_default")],
        [InlineKeyboardButton("🗑 Удалить", callback_data="car_remove")],
        [InlineKeyboardButton("◀️ Меню", callback_data="back_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def car_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить авто"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Отправьте название авто (например: Ford Focus 2)\n\n"
        "Или отправьте 'отмена' для отмены.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Отмена", callback_data="cars")]])
    )
    context.user_data["awaiting_car"] = True

async def car_add_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить текст авто"""
    if not context.user_data.get("awaiting_car"):
        return
    
    user_id = update.effective_user.id
    car_name = update.message.text.strip()
    
    if car_name.lower() == "отмена":
        context.user_data["awaiting_car"] = False
        await update.message.reply_text("Отменено.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
        ]))
        return
    
    if user_id not in user_cars:
        user_cars[user_id] = []
    
    if car_name not in user_cars[user_id]:
        user_cars[user_id].append(car_name)
    
    context.user_data["awaiting_car"] = False
    
    await update.message.reply_text(f"✅ Авто '{car_name}' добавлено!", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
    ]))

async def car_default(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбрать авто по умолчанию"""
    query = update.callback_query
    user_id = update.effective_user.id
    cars = user_cars.get(user_id, ["Основное"])
    
    keyboard = []
    for car in cars:
        keyboard.append([InlineKeyboardButton(car, callback_data=f"car_set_{car}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="cars")])
    
    await query.edit_message_text("Выберите авто по умолчанию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def car_set_default(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить авто по умолчанию"""
    query = update.callback_query
    car = query.data.replace("car_set_", "")
    
    context.user_data["default_car"] = car
    
    await query.edit_message_text(f"✅ '{car}' выбрано по умолчанию!", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
    ]))