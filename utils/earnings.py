# utils/earnings.py
from datetime import timedelta
from config import DEFAULT_HOURLY_RATE
import database as db


def calculate_earnings(user_id: int, driving_time: timedelta, hourly_rate: float = None) -> dict:
    """Рассчитать заработок с учётом пользовательской ставки"""
    if hourly_rate is None:
        settings = db.get_user_settings(user_id)
        hourly_rate = settings.get("hourly_rate", DEFAULT_HOURLY_RATE)

    hours = driving_time.total_seconds() / 3600
    base_earnings = hours * hourly_rate

    # Ночные часы (22:00 - 06:00) — бонус +20%
    # В реальном боте можно анализировать время смены
    night_bonus = 0
    rush_bonus = 0

    total = base_earnings + night_bonus + rush_bonus

    return {
        "hours": round(hours, 1),
        "base": round(base_earnings, 2),
        "night_bonus": round(night_bonus, 2),
        "rush_bonus": round(rush_bonus, 2),
        "total": round(total, 2),
        "rate": hourly_rate
    }


def predict_daily_earnings(user_id: int, hours_planned: float) -> dict:
    """Прогноз на день с учётом ставки пользователя"""
    settings = db.get_user_settings(user_id)
    rate = settings.get("hourly_rate", DEFAULT_HOURLY_RATE)
    return calculate_earnings(user_id, timedelta(hours=hours_planned), rate)


def predict_weekly_earnings(user_id: int, weekly_hours: float) -> dict:
    """Прогноз на неделю"""
    settings = db.get_user_settings(user_id)
    rate = settings.get("hourly_rate", DEFAULT_HOURLY_RATE)
    total = calculate_earnings(user_id, timedelta(hours=weekly_hours), rate)
    total["daily_avg"] = round(total["total"] / 7, 2)
    return total
