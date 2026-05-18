from datetime import timedelta
from config import DEFAULT_HOURLY_RATE

def calculate_earnings(driving_time: timedelta, hourly_rate: float = DEFAULT_HOURLY_RATE) -> dict:
    """Рассчитать прогноз заработка"""
    hours = driving_time.total_seconds() / 3600
    base_earnings = hours * hourly_rate
    
    # Коэффициенты
    night_bonus = 0  # Ночные часы (22-06)
    rush_bonus = 0   # Часы пик
    
    # Пример: ночные +20%
    # В реальном боте можно анализировать время смены
    
    total = base_earnings + night_bonus + rush_bonus
    
    return {
        "hours": round(hours, 1),
        "base": round(base_earnings, 2),
        "night_bonus": round(night_bonus, 2),
        "rush_bonus": round(rush_bonus, 2),
        "total": round(total, 2)
    }

def predict_daily_earnings(hours_planned: float, hourly_rate: float = DEFAULT_HOURLY_RATE) -> dict:
    """Прогноз на день"""
    return calculate_earnings(timedelta(hours=hours_planned), hourly_rate)

def predict_weekly_earnings(weekly_hours: float, hourly_rate: float = DEFAULT_HOURLY_RATE) -> dict:
    """Прогноз на неделю"""
    total = calculate_earnings(timedelta(hours=weekly_hours), hourly_rate)
    total["daily_avg"] = round(total["total"] / 7, 2)
    return total