from datetime import datetime, timedelta
import pytz

TIMEZONE = pytz.timezone("Europe/Minsk")

def now_minsk():
    return datetime.now(TIMEZONE)

def format_duration(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

def format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = TIMEZONE.localize(dt)
    return dt.strftime("%d.%m.%Y %H:%M")

def parse_time(time_str: str) -> datetime:
    formats = ["%H:%M", "%d.%m.%Y %H:%M"]
    now = now_minsk()
    for fmt in formats:
        try:
            parsed = datetime.strptime(time_str, fmt)
            if fmt == "%H:%M":
                parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
            return TIMEZONE.localize(parsed)
        except ValueError:
            continue
    raise ValueError("Неверный формат времени")

def get_week_start(dt: datetime = None) -> datetime:
    if dt is None:
        dt = now_minsk()
    return dt - timedelta(days=dt.weekday(), hours=dt.hour, minutes=dt.minute, seconds=dt.second)

def time_until(target: datetime) -> str:
    diff = target - now_minsk()
    if diff.total_seconds() <= 0:
        return "уже пора!"
    return format_duration(diff)
