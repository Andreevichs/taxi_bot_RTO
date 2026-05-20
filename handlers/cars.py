from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db

MAX_CARS = 5


async def cmd_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление авто"""
    query = update.callback_query
    user_id = update.effective_user.id

    cars = db.get_user_cars(user_id)
    default = db.get_default_car(user_id)

    text = "🚙 Мои автомобили\n\n"
    if cars:
        for car in cars:
            marker = " ✅" if car["name"] == default else ""
            text += f"• {car['name']}{marker}\n"
    else:
        text += "• Основное ✅\n"

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
    user_id = update.effective_user.id
    await query.answer()

    cars = db.get_user_cars(user_id)
    if len(cars) >= MAX_CARS:
        await query.edit_message_text(
            f"❌ Максимум {MAX_CARS} авто!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
            ])
        )
        return

    await query.edit_message_text(
        "Отправьте название авто (например: Ford Focus 2)\n\n"
        "Или отправьте 'отмена' для отмены.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Отмена", callback_data="cars")]
        ])
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
        await update.message.reply_text(
            "Отменено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
            ])
        )
        return

    if not car_name or len(car_name) > 50:
        await update.message.reply_text(
            "❌ Название слишком длинное или пустое. Макс 50 символов.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
            ])
        )
        return

    success = db.add_car(user_id, car_name)

    if success:
        cars = db.get_user_cars(user_id)
        if len(cars) == 1:
            db.set_default_car(user_id, car_name)

        context.user_data["awaiting_car"] = False
        await update.message.reply_text(
            f"✅ Авто '{car_name}' добавлено!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ Такое авто уже есть!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
            ])
        )


async def car_default(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбрать авто по умолчанию"""
    query = update.callback_query
    user_id = update.effective_user.id
    cars = db.get_user_cars(user_id)

    if not cars:
        await query.edit_message_text(
            "У вас только основное авто.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
            ])
        )
        return

    keyboard = []
    for car in cars:
        keyboard.append([InlineKeyboardButton(car["name"], callback_data=f"car_set_{car['name']}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="cars")])

    await query.edit_message_text("Выберите авто по умолчанию:", reply_markup=InlineKeyboardMarkup(keyboard))


async def car_set_default(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить авто по умолчанию"""
    query = update.callback_query
    car = query.data.replace("car_set_", "")

    user_id = update.effective_user.id
    db.set_default_car(user_id, car)

    await query.edit_message_text(
        f"✅ '{car}' выбрано по умолчанию!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
        ])
    )


async def car_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить авто"""
    query = update.callback_query
    user_id = update.effective_user.id
    cars = db.get_user_cars(user_id)

    if not cars:
        await query.edit_message_text(
            "Нечего удалять.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
            ])
        )
        return

    keyboard = []
    for car in cars:
        keyboard.append([
            InlineKeyboardButton(f"🗑 {car['name']}", callback_data=f"car_del_{car['name']}")
        ])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="cars")])

    await query.edit_message_text("Какое авто удалить?", reply_markup=InlineKeyboardMarkup(keyboard))


async def car_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтвердить удаление авто"""
    query = update.callback_query
    user_id = update.effective_user.id

    car = query.data.replace("car_del_", "")
    db.remove_car(user_id, car)

    default = db.get_default_car(user_id)
    if default == car:
        cars = db.get_user_cars(user_id)
        if cars:
            db.set_default_car(user_id, cars[0]["name"])

    await query.edit_message_text(
        f"✅ Авто '{car}' удалено!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="cars")]
        ])
    )
