import os
from datetime import timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН_СЮДА":
    raise ValueError(
        "❌ BOT_TOKEN не задан! Установите переменную окружения BOT_TOKEN в Render:\n"
        "   Settings → Environment → Add Environment Variable\n"
        "   Key: BOT_TOKEN\n"
        "   Value: ваш_токен_от_BotFather"
    )

TIMEZONE = "Europe/Minsk"

# === РТО ПРАВИЛА БЕЛАРУСЬ (2025-2026) ===
MAX_DAILY_DRIVE = timedelta(hours=9)          # Макс вождение в сутки (2 раза/неделю до 10)
MAX_WEEKLY_DRIVE = timedelta(hours=56)      # Макс в неделю
MAX_CONTINUOUS_DRIVE = timedelta(hours=4, minutes=30)  # Без перерыва
MIN_BREAK = timedelta(minutes=45)             # Перерыв после 4.5 часов
MIN_DAILY_REST = timedelta(hours=11)          # Отдых между сменами
MAX_SHIFT = timedelta(hours=10)              # Макс смена (2 раза/неделю до 10)
MAX_CONSECUTIVE_DAYS = 6                      # Макс дней подряд по РТО!

DEFAULT_HOURLY_RATE = 25

MAX_FAMILY_MEMBERS = 3

# === ДОСТИЖЕНИЯ — ВСЕ ПО РТО БЕЛАРУСИ ===
ACHIEVEMENTS = {
    "first_shift": {"name": "🚀 Первый выезд", "desc": "Завершите первую смену"},
    "week_max": {"name": "📅 Полная неделя", "desc": "6 дней работы с соблюдением РТО (максимум)"},
    "month_hero": {"name": "🏆 Месячный герой", "desc": "30 смен с соблюдением отдыха"},
    "early_bird": {"name": "🌅 Жаворонок", "desc": "Начните смену до 6:00"},
    "night_owl": {"name": "🦉 Сова", "desc": "Работайте после 22:00"},
    "safe_driver": {"name": "🛡️ Безопасник", "desc": "100 часов без нарушений РТО"},
    "no_violations_week": {"name": "✅ Чистая неделя", "desc": "Неделя без нарушений РТО"},
    "money_maker": {"name": "💰 Заработок", "desc": "Заработайте 1000 BYN"},
}
