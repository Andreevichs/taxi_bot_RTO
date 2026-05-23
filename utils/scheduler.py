# utils/scheduler.py
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from .time_utils import now_minsk, TIMEZONE, parse_schedule_time
import database as db
import threading
import asyncio

# Глобальная ссылка на бот для отправки сообщений
_bot_instance = None

def set_bot_instance(bot):
    """Установить экземпляр бота для отправки уведомлений"""
    global _bot_instance
    _bot_instance = bot

class AutoScheduler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.scheduler = BackgroundScheduler(timezone=TIMEZONE)
        self.reminders: Dict[int, list] = {}
        self.active_jobs: Dict[int, list] = {}  # user_id -> list of job IDs
        self._bot_app = None  # Ссылка на application для отправки сообщений

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def set_bot_app(self, application):
        """Установить application для отправки сообщений через job_queue"""
        self._bot_app = application

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
            tomorrow = now + timedelta(days=1)
            return {
                "type": "утро (завтра)",
                "start": tomorrow.replace(hour=m_start_h, minute=m_start_m, second=0, microsecond=0),
                "end": tomorrow.replace(hour=m_end_h, minute=m_end_m, second=0, microsecond=0)
            }

    def start_shift_monitoring(self, user_id: int):
        """Начать мониторинг смены для автоматических уведомлений"""
        # Удалить старые задачи для этого пользователя
        self.stop_shift_monitoring(user_id)

        # Задача 1: Проверка каждые 15 минут (перерыв, усталость, лимиты)
        job1 = self.scheduler.add_job(
            self._check_shift_status,
            trigger=IntervalTrigger(minutes=15),
            args=[user_id],
            id=f"shift_monitor_{user_id}",
            replace_existing=True
        )

        # Задача 2: Напоминание через 4 часа (нужен перерыв!)
        job2 = self.scheduler.add_job(
            self._remind_break,
            trigger=IntervalTrigger(hours=4, minutes=30),
            args=[user_id],
            id=f"break_remind_{user_id}",
            replace_existing=True
        )

        # Задача 3: Напоминание через 9 часов (лимит вождения за сутки)
        job3 = self.scheduler.add_job(
            self._remind_daily_limit,
            trigger=IntervalTrigger(hours=9),
            args=[user_id],
            id=f"limit_remind_{user_id}",
            replace_existing=True
        )

        self.active_jobs[user_id] = [job1.id, job2.id, job3.id]

    def stop_shift_monitoring(self, user_id: int):
        """Остановить мониторинг смены"""
        if user_id in self.active_jobs:
            for job_id in self.active_jobs[user_id]:
                try:
                    self.scheduler.remove_job(job_id)
                except Exception:
                    pass
            del self.active_jobs[user_id]

    def send_test_notification(self, user_id: int, delay_seconds: int = 30, message: str = "Тестовое уведомление"):
        """Отправить тестовое уведомление через delay_seconds секунд"""
        run_time = datetime.now(TIMEZONE) + timedelta(seconds=delay_seconds)
        
        job = self.scheduler.add_job(
            self._send_notification_sync,
            trigger=DateTrigger(run_date=run_time),
            args=[user_id, message],
            id=f"test_notification_{user_id}_{datetime.now().timestamp()}",
            replace_existing=False
        )
        return job.id

    def _send_notification_sync(self, user_id: int, message: str):
        """Отправить уведомление синхронно (для вызова из APScheduler)"""
        if _bot_instance is None:
            print(f"[_send_notification_sync] Бот не инициализирован!")
            return

        try:
            # Создаём новый event loop для отправки
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def send_msg():
                try:
                    await _bot_instance.send_message(chat_id=user_id, text=message)
                    print(f"[_send_notification_sync] Уведомление отправлено пользователю {user_id}")
                except Exception as e:
                    print(f"[_send_notification_sync] Ошибка отправки: {e}")
            
            loop.run_until_complete(send_msg())
            loop.close()
            
        except Exception as e:
            print(f"[_send_notification_sync] Критическая ошибка: {e}")

    def _check_shift_status(self, user_id: int):
        """Проверить статус смены каждые 15 минут"""
        from utils.rto_logic import get_session
        from utils.time_utils import format_duration

        session = get_session(user_id)
        status = session.get_status()

        if not status["active"]:
            return

        # Проверка: усталость > 80%
        if status["fatigue"] >= 80:
            self._send_notification_sync(
                user_id,
                "⚠️ Высокая усталость!\n😴 Усталость: 80%+\nРекомендуется завершить смену."
            )

        # Проверка: осталось мало времени до лимита недели
        weekly = session.get_weekly_stats()
        remaining_hours = weekly["remaining"].total_seconds() / 3600
        if remaining_hours < 5:
            self._send_notification_sync(
                user_id,
                f"⚠️ Мало времени до лимита недели!\nОсталось: {remaining_hours:.1f} часов"
            )

    def _remind_break(self, user_id: int):
        """Напомнить о перерыве через 4.5 часа"""
        from utils.rto_logic import get_session

        session = get_session(user_id)
        status = session.get_status()

        if not status["active"]:
            return

        # Проверить, что всё ещё за рулём (нет перерыва)
        active = db.get_active_shift(user_id)
        if active and active["driving_sessions"]:
            last_session = active["driving_sessions"][-1]
            if last_session.get("end") is None:
                # Всё ещё за рулём!
                self._send_notification_sync(
                    user_id,
                    "🔴 РТО: Вы за рулём 4.5 часа!\n\n"
                    "⚠️ Нужен перерыв 45 минут!\n"
                    "Нажмите ☕ Перерыв в меню бота."
                )

    def _remind_daily_limit(self, user_id: int):
        """Напомнить о лимите 9 часов за сутки"""
        from utils.rto_logic import get_session

        session = get_session(user_id)
        status = session.get_status()

        if not status["active"]:
            return

        if status["driving_today"].total_seconds() >= 9 * 3600:
            self._send_notification_sync(
                user_id,
                "🔴 РТО: Лимит 9 часов в сутки достигнут!\n\n"
                "⚠️ Немедленно завершите смену!\n"
                "Нажмите ⏹️ Закончить смену в меню."
            )

    def add_reminder(self, user_id: int, time_str: str, callback: Callable, message: str):
        """Добавить напоминание по времени"""
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
        self.stop_shift_monitoring(user_id)
