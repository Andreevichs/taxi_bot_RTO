# utils/scheduler.py
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from telegram.ext import Application
import database as db

# Глобальная ссылка на application
_app_instance = None

def set_application(app):
    """Установить application для отправки уведомлений через job_queue"""
    global _app_instance
    _app_instance = app

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
        self.active_jobs: Dict[int, list] = {}  # user_id -> list of job names

    def start(self):
        """JobQueue стартует автоматически с application"""
        pass

    def set_schedule(self, user_id: int, morning_start: str, morning_end: str,
                     evening_start: str, evening_end: str):
        """Сохранить расписание в БД"""
        db.save_schedule(user_id, morning_start, morning_end, evening_start, evening_end)

    def get_schedule(self, user_id: int) -> Optional[Dict]:
        """Получить расписание из БД"""
        return db.get_schedule(user_id)

    def get_next_shift(self, user_id: int) -> Optional[Dict]:
        """Когда следующая смена"""
        from utils.time_utils import now_minsk, parse_schedule_time
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
        if _app_instance is None:
            return

        # Удалить старые задачи для этого пользователя
        self.stop_shift_monitoring(user_id)

        job_queue = _app_instance.job_queue

        # Задача 1: Проверка каждые 15 минут
        job1 = job_queue.run_repeating(
            self._check_shift_status,
            interval=timedelta(minutes=15),
            first=timedelta(minutes=15),
            chat_id=user_id,
            name=f"shift_monitor_{user_id}"
        )

        # Задача 2: Напоминание через 4.5 часа
        job2 = job_queue.run_repeating(
            self._remind_break,
            interval=timedelta(hours=4, minutes=30),
            first=timedelta(hours=4, minutes=30),
            chat_id=user_id,
            name=f"break_remind_{user_id}"
        )

        # Задача 3: Напоминание через 9 часов
        job3 = job_queue.run_repeating(
            self._remind_daily_limit,
            interval=timedelta(hours=9),
            first=timedelta(hours=9),
            chat_id=user_id,
            name=f"limit_remind_{user_id}"
        )

        self.active_jobs[user_id] = [job1.name, job2.name, job3.name]

    def stop_shift_monitoring(self, user_id: int):
        """Остановить мониторинг смены"""
        if _app_instance is None:
            return

        job_queue = _app_instance.job_queue
        if user_id in self.active_jobs:
            for job_name in self.active_jobs[user_id]:
                jobs = job_queue.get_jobs_by_name(job_name)
                for job in jobs:
                    job.schedule_removal()
            del self.active_jobs[user_id]

    def send_test_notification(self, user_id: int, delay_seconds: int = 30, message: str = "Тестовое уведомление"):
        """Отправить тестовое уведомление через delay_seconds секунд"""
        if _app_instance is None:
            return None

        job_queue = _app_instance.job_queue
        from utils.time_utils import now_minsk, TIMEZONE
        
        run_time = datetime.now(TIMEZONE) + timedelta(seconds=delay_seconds)
        
        job = job_queue.run_once(
            self._send_notification,
            when=run_time,
            chat_id=user_id,
            data={"message": message},
            name=f"test_notification_{user_id}_{datetime.now().timestamp()}"
        )
        return job.name

    async def _send_notification(self, context):
        """Отправить уведомление (async, вызывается JobQueue)"""
        job = context.job
        chat_id = job.chat_id
        message = job.data.get("message", "Уведомление")
        
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            print(f"[_send_notification] Уведомление отправлено пользователю {chat_id}")
        except Exception as e:
            print(f"[_send_notification] Ошибка отправки: {e}")

    async def _check_shift_status(self, context):
        """Проверить статус смены каждые 15 минут"""
        from utils.rto_logic import get_session
        from utils.time_utils import format_duration

        chat_id = context.job.chat_id
        session = get_session(chat_id)
        status = session.get_status()

        if not status["active"]:
            return

        # Проверка: усталость > 80%
        if status["fatigue"] >= 80:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Высокая усталость!\n😴 Усталость: 80%+\nРекомендуется завершить смену."
            )

        # Проверка: осталось мало времени до лимита недели
        weekly = session.get_weekly_stats()
        remaining_hours = weekly["remaining"].total_seconds() / 3600
        if remaining_hours < 5:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Мало времени до лимита недели!\nОсталось: {remaining_hours:.1f} часов"
            )

    async def _remind_break(self, context):
        """Напомнить о перерыве через 4.5 часа"""
        from utils.rto_logic import get_session

        chat_id = context.job.chat_id
        session = get_session(chat_id)
        status = session.get_status()

        if not status["active"]:
            return

        # Проверить, что всё ещё за рулём (нет перерыва)
        active = db.get_active_shift(chat_id)
        if active and active["driving_sessions"]:
            last_session = active["driving_sessions"][-1]
            if last_session.get("end") is None:
                # Всё ещё за рулём!
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🔴 РТО: Вы за рулём 4.5 часа!\n\n"
                         "⚠️ Нужен перерыв 45 минут!\n"
                         "Нажмите ☕ Перерыв в меню бота."
                )

    async def _remind_daily_limit(self, context):
        """Напомнить о лимите 9 часов за сутки"""
        from utils.rto_logic import get_session

        chat_id = context.job.chat_id
        session = get_session(chat_id)
        status = session.get_status()

        if not status["active"]:
            return

        if status["driving_today"].total_seconds() >= 9 * 3600:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔴 РТО: Лимит 9 часов в сутки достигнут!\n\n"
                     "⚠️ Немедленно завершите смену!\n"
                     "Нажмите ⏹️ Закончить смену в меню."
            )

    def remove_schedule(self, user_id: int):
        """Удалить расписание"""
        db.delete_schedule(user_id)
        self.stop_shift_monitoring(user_id)
