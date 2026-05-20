# utils/scheduler.py
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .time_utils import now_minsk, TIMEZONE, parse_schedule_time
import database as db


class AutoScheduler:
    _instance = None

    def __new__(cls):
        # Singleton — один планировщик на всё приложение
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        self.reminders: Dict[int, list] = {}  # user_id -> list of jobs

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def set_schedule(self, user_id: int, morning_start: str, morning_end: str,
                     evening_start: str, evening_end: str):
        """Сохранить расписание в БД"""
        db.save_schedule(user_id, morning_start, morning_end, evening_start, evening_end)

    def get_schedule(self, user_id: int) -> Optional[Dict]:
        """Получить расписание из БД"""
        return db.get_schedule(user_id)

    def get_next_shift(self, user_id: int) -> Optional[Dict]:
        """Когда следующая смена"""
        schedule = db.get_schedule(user_id)
        if not schedule:
            return None

        now = now_minsk()

        try:
            m_start_h, m_start_m = parse_schedule_time(schedule["morning"]["start"])
            m_end_h, m_end_m = parse_schedule_time(schedule["morning"]["end"])
            e_start_h, e_start_m = parse_schedule_time(schedule["evening"]["start"])
            e_end_h, e_end_m = parse_schedule_time(schedule["evening"]["end"])
        except ValueError:
            return None

        today_morning = now.replace(hour=m_start_h, minute=m_start_m, second=0, microsecond=0)
        today_evening = now.replace(hour=e_start_h, minute=e_start_m, second=0, microsecond=0)

        if now < today_morning:
            return {
                "type": "утро",
                "start": today_morning,
                "end": now.replace(hour=m_end_h, minute=m_end_m, second=0, microsecond=0)
            }
        elif now < today_evening:
            return {
                "type": "вечер",
                "start": today_evening,
                "end": now.replace(hour=e_end_h, minute=e_end_m, second=0, microsecond=0)
            }
        else:
            # Завтра утро
            tomorrow = now + timedelta(days=1)
            return {
                "type": "утро (завтра)",
                "start": tomorrow.replace(hour=m_start_h, minute=m_start_m, second=0, microsecond=0),
                "end": tomorrow.replace(hour=m_end_h, minute=m_end_m, second=0, microsecond=0)
            }

    def add_reminder(self, user_id: int, time_str: str, callback: Callable, message: str):
        """Добавить напоминание"""
        try:
            hour, minute = parse_schedule_time(time_str)
        except ValueError:
            return False

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
        return True

    def clear_reminders(self, user_id: int):
        """Удалить все напоминания пользователя"""
        if user_id in self.reminders:
            for job in self.reminders[user_id]:
                try:
                    job.remove()
                except Exception:
                    pass
            self.reminders[user_id] = []

    def remove_schedule(self, user_id: int):
        """Удалить расписание"""
        db.delete_schedule(user_id)
        self.clear_reminders(user_id)
