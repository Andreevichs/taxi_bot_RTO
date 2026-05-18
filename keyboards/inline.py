from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🚖 Мой автомобиль", callback_data="auto_menu")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile_menu"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats_menu")],
        [InlineKeyboardButton("📅 Расписание", callback_data="schedule_menu"),
         InlineKeyboardButton("🏆 Достижения", callback_data="achievements_menu")],
        [InlineKeyboardButton("👨‍👩‍👧‍👦 Семья", callback_data="family_menu")],
        [InlineKeyboardButton("🗑 Очистить данные", callback_data="reset_data")],
    ]
    return InlineKeyboardMarkup(keyboard)

def profile_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
def auto_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("➕ Добавить авто", callback_data="add_car")], [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
def family_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("➕ Добавить участника", callback_data="add_family_member")], [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
def schedule_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("➕ Добавить день", callback_data="add_schedule_day")], [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
