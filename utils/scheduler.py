from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .time_utils import now_minsk, TIMEZONE

class AutoScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=TIMEZONE)
        self.schedules: Dict[int, Dict] = {}
        self.reminders: Dict[int, list] = {}

    def start(self):
        self.scheduler.start()

    def set_schedule(self, user_id: int, morning_start: str, morning_end: str,
                     evening_start: str, evening_end: str):
        self.schedules[user_id] = {
            "morning": {"start": morning_start, "end": morning_end},
            "evening": {"start": evening_start, "end": evening_end}
        }

    def add_reminder(self, user_id: int, time_str: str, callback: Callable, message: str):
        hour, minute = map(int, time_str.split(":"))
        job = self.scheduler.add_job(
            callback,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=[user_id, message],
            id=f"reminder_{user_id}_{time_str}",
            replace_existing=True
        )
        if user_id not in self.reminders:
            self.reminders[user_id] = []
        self.reminders[user_id].append(job)

    def get_next_shift(self, user_id: int) -> Optional[Dict]:
        if user_id not in self.schedules:
            return None
        now = now_minsk()
        schedule = self.schedules[user_id]
        m_start = datetime.strptime(schedule["morning"]["start"], "%H:%M").time()
        m_end = datetime.strptime(schedule["morning"]["end"], "%H:%M").time()
        e_start = datetime.strptime(schedule["evening"]["start"], "%H:%M").time()
        e_end = datetime.strptime(schedule["evening"]["end"], "%H:%M").time()
        today_morning = now.replace(hour=m_start.hour, minute=m_start.minute)
        today_evening = now.replace(hour=e_start.hour, minute=e_start.minute)
        if now.time() < m_start:
            return {"type": "утро", "start": today_morning, "end": now.replace(hour=m_end.hour, minute=m_end.minute)}
        elif now.time() < e_start:
            return {"type": "вечер", "start": today_evening, "end": now.replace(hour=e_end.hour, minute=e_end.minute)}
        else:
            tomorrow = now + timedelta(days=1)
            return {
                "type": "утро (завтра)",
                "start": tomorrow.replace(hour=m_start.hour, minute=m_start.minute),
                "end": tomorrow.replace(hour=m_end.hour, minute=m_end.minute)
            }

    def clear_reminders(self, user_id: int):
        if user_id in self.reminders:
            for job in self.reminders[user_id]:
                job.remove()
            self.reminders[user_id] = []
