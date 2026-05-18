import os
from datetime import timedelta

# === ТОКЕН ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_СЮДА")

# === ВРЕМЯ ===
TIMEZONE = "Europe/Minsk"

# === РТО ПРАВИЛА БЕЛАРУСЬ ===
MAX_DAILY_DRIVE = timedelta(hours=9)      # Макс вождения за сутки
MAX_WEEKLY_DRIVE = timedelta(hours=56)    # Макс вождения за неделю
MAX_CONTINUOUS_DRIVE = timedelta(hours=4) # Макс без перерыва
MIN_BREAK = timedelta(minutes=45)         # Минимальный перерыв
MIN_DAILY_REST = timedelta(hours=11)      # Минимальный ежедневный отдых
MAX_SHIFT = timedelta(hours=13)           # Макс продолжительность смены

# === ПРОГНОЗ ЗАРАБОТКА ===
DEFAULT_HOURLY_RATE = 25  # BYN/час примерно

# === СЕМЕЙНЫЙ ДОСТУП ===
MAX_FAMILY_MEMBERS = 3

# === ДОСТИЖЕНИЯ ===
ACHIEVEMENTS = {
    "first_shift": {"name": "🚀 Первый выезд", "desc": "Завершите первую смену"},
    "week_worker": {"name": "📅 Недельный труженик", "desc": "7 дней подряд на линии"},
    "month_hero": {"name": "🏆 Месячный герой", "desc": "30 дней активной работы"},
    "early_bird": {"name": "🌅 Жаворонок", "desc": "Начните смену до 6:00"},
    "night_owl": {"name": "🦉 Сова", "desc": "Работайте после 22:00"},
    "safe_driver": {"name": "🛡️ Безопасник", "desc": "100 часов без нарушений РТО"},
    "money_maker": {"name": "💰 Заработок", "desc": "Заработайте 1000 BYN"},
}