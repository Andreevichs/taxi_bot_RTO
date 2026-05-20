# utils/time_utils.py
from datetime import datetime, timedelta
import pytz

TIMEZONE = pytz.timezone("Europe/Minsk")


def now_minsk():
    """Текущее время в Минске"""
    return datetime.now(TIMEZONE)


def format_duration(td: timedelta) -> str:
    """Форматировать timedelta как ЧЧ:ММ"""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def format_datetime(dt: datetime) -> str:
    """Форматировать дату-время"""
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = TIMEZONE.localize(dt)
    return dt.strftime("%d.%m.%Y %H:%M")


def parse_time(time_str: str) -> datetime:
    """Парсить время из строки"""
    formats = ["%H:%M", "%d.%m.%Y %H:%M"]
    now = now_minsk()
    for fmt in formats:
        try:
            parsed = datetime.strptime(time_str.strip(), fmt)
            if fmt == "%H:%M":
                parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
            if parsed.tzinfo is None:
                parsed = TIMEZONE.localize(parsed)
            return parsed
        except ValueError:
            continue
    raise ValueError("Неверный формат времени")


def get_week_start(dt: datetime = None) -> datetime:
    """Начало недели (понедельник)"""
    if dt is None:
        dt = now_minsk()
    # Сбросить время до начала дня
    start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    # Отнять дни до понедельника
    monday = start_of_day - timedelta(days=start_of_day.weekday())
    return monday


def time_until(target: datetime) -> str:
    """Сколько времени до цели"""
    diff = target - now_minsk()
    if diff.total_seconds() <= 0:
        return "уже пора!"
    return format_duration(diff)


def parse_schedule_time(time_str: str) -> tuple:
    """Парсить время расписания '08:00' → (8, 0)"""
    try:
        hour, minute = map(int, time_str.strip().split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        return hour, minute
    except (ValueError, AttributeError):
        raise ValueError("Время должно быть в формате ЧЧ:ММ (например, 08:00)")
