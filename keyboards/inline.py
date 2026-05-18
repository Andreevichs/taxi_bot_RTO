from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🚖 Мой автомобиль", callback_data="auto_menu")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile_menu"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats_menu")],
        [InlineKeyboardButton("📅 Расписание", callback_data="schedule_menu"),
         InlineKeyboardButton("🏆 Достижения", callback_data="achievements_menu")],
        [InlineKeyboardButton("👨‍👩‍👧‍👦 Семья", callback_data="family_menu")],
        [InlineKeyboardButton("🗑 Очистить данные (Тест)", callback_data="reset_data")],
    ]
    return InlineKeyboardMarkup(keyboard)

def profile_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def auto_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Добавить авто", callback_data="add_car")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def family_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Добавить участника", callback_data="add_family_member")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def schedule_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Добавить день", callback_data="add_schedule_day")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def yes_no_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="yes"),
         InlineKeyboardButton("❌ Нет", callback_data="no")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)
