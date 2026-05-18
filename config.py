import os
from datetime import timedelta

# === ТОКЕН ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_СЮДА")

# === ВРЕМЯ ===
TIMEZONE = "Europe/Minsk"

# === РТО ПРАВИЛА БЕЛАРУСЬ ===
MAX_DAILY_DRIVE = timedelta(hours=9)
MAX_WEEKLY_DRIVE = timedelta(hours=56)
MAX_CONTINUOUS_DRIVE = timedelta(hours=4)
MIN_BREAK = timedelta(minutes=45)
MIN_DAILY_REST = timedelta(hours=11)
MAX_SHIFT = timedelta(hours=13)

# === ПРОГНОЗ ЗАРАБОТКА ===
DEFAULT_HOURLY_RATE = 25

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
