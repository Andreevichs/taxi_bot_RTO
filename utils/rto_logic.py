# utils/rto_logic.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .time_utils import now_minsk, format_duration, TIMEZONE, get_week_start
from config import (
    MAX_DAILY_DRIVE, MAX_WEEKLY_DRIVE, MAX_CONTINUOUS_DRIVE,
    MIN_BREAK, MIN_DAILY_REST, MAX_SHIFT, MAX_CONSECUTIVE_DAYS
)
import database as db


class RTOSession:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def start_shift(self, car: str = "Основное") -> Dict:
        """Начать смену"""
        now = now_minsk()

        # Проверка: нет ли уже активной смены?
        active = db.get_active_shift(self.user_id)
        if active:
            return {
                "ok": False,
                "error": "❌ У вас уже есть активная смена! Закончите текущую перед началом новой."
            }

        warnings = []

        # Проверка отдыха между сменами — ПРЕДУПРЕЖДЕНИЕ, не блокировка
        shifts = db.get_user_shifts(self.user_id)
        if shifts:
            last_shift = shifts[-1]
            if last_shift["end_time"]:
                rest = now - last_shift["end_time"]
                if rest < MIN_DAILY_REST:
                    warnings.append(
                        f"⚠️ Отдых короткий: {format_duration(rest)} (рекомендуется {format_duration(MIN_DAILY_REST)})"
                    )

        # Проверка: не более 6 дней подряд по РТО — БЛОКИРОВКА
        consecutive_days = self._count_consecutive_days()
        if consecutive_days >= MAX_CONSECUTIVE_DAYS:
            return {
                "ok": False,
                "error": f"🔴 РТО: Вы уже работали {consecutive_days} дней подряд!\nМаксимум: {MAX_CONSECUTIVE_DAYS} дней.\n❌ Нужен отдых минимум 45 часов!"
            }

        # Проверка лимита 56 часов в неделю — БЛОКИРОВКА
        week_start = get_week_start()
        week_shifts = db.get_user_shifts(self.user_id, since=week_start)
        weekly_driving = timedelta()
        for shift in week_shifts:
            if shift["end_time"]:
                stats = self._calc_shift_stats(shift)
                weekly_driving += stats["driving"]

        if weekly_driving >= MAX_WEEKLY_DRIVE:
            return {
                "ok": False,
                "error": f"🔴 Лимит 56 часов в неделю исчерпан!\nНакоплено: {format_duration(weekly_driving)}\n❌ Смена не может быть начата!"
            }

        db.save_active_shift(self.user_id, now, car)
        result = {"ok": True, "start": now}
        if warnings:
            result["warnings"] = warnings
        return result

    def _count_consecutive_days(self) -> int:
        """Посчитать подряд идущие дни работы"""
        shifts = db.get_user_shifts(self.user_id)
        if not shifts:
            return 0
        
        work_dates = set()
        for shift in shifts:
            work_dates.add(shift["start_time"].date())
        
        today = now_minsk().date()
        consecutive = 0
        for i in range(MAX_CONSECUTIVE_DAYS + 2):
            check_date = today - timedelta(days=i)
            if check_date in work_dates:
                consecutive += 1
            else:
                break
        
        return consecutive

    def start_break(self) -> Dict:
        """Начать перерыв"""
        active = db.get_active_shift(self.user_id)
        if not active:
            return {"ok": False, "error": "❌ Нет активной смены"}

        now = now_minsk()

        # Проверка: не превышено ли 4.5 часа без перерыва?
        sessions = active["driving_sessions"]
        if sessions:
            last_session = sessions[-1]
            if last_session.get("end") is None:
                session_start = datetime.fromisoformat(last_session["start"]) if isinstance(last_session["start"], str) else last_session["start"]
                driving_without_break = now - session_start
                if driving_without_break > MAX_CONTINUOUS_DRIVE:
                    return {
                        "ok": False,
                        "error": f"🔴 РТО: Вы за рулём {format_duration(driving_without_break)}!\nМаксимум без перерыва: {format_duration(MAX_CONTINUOUS_DRIVE)}\n❌ Нужен перерыв 45 минут!"
                    }

        # Закрыть текущую сессию вождения
        if sessions:
            last = sessions[-1]
            if last.get("end") is None:
                last["end"] = now.isoformat()

        breaks = active["breaks"]
        breaks.append({"start": now.isoformat(), "end": None})

        db.update_active_shift(self.user_id, breaks=breaks, driving_sessions=sessions)
        return {"ok": True, "start": now}

    def end_break(self) -> Dict:
        """Закончить перерыв"""
        active = db.get_active_shift(self.user_id)
        if not active:
            return {"ok": False, "error": "❌ Нет активной смены"}

        now = now_minsk()

        # Проверка: перерыв минимум 45 минут?
        breaks = active["breaks"]
        if breaks:
            last_break = breaks[-1]
            if last_break.get("end") is None:
                break_start = datetime.fromisoformat(last_break["start"]) if isinstance(last_break["start"], str) else last_break["start"]
                break_duration = now - break_start
                if break_duration < MIN_BREAK:
                    return {
                        "ok": False,
                        "error": f"🔴 Перерыв слишком короткий!\nМинимум: {format_duration(MIN_BREAK)}\nПрошло: {format_duration(break_duration)}\n❌ Нельзя продолжить работу!"
                    }

        # Закрыть перерыв
        if breaks:
            last = breaks[-1]
            if last.get("end") is None:
                last["end"] = now.isoformat()

        # Новая сессия вождения
        sessions = active["driving_sessions"]
        sessions.append({"start": now.isoformat(), "end": None})

        db.update_active_shift(self.user_id, breaks=breaks, driving_sessions=sessions)
        return {"ok": True, "end": now}

    def end_shift(self) -> Dict:
        """Закончить смену"""
        active = db.get_active_shift(self.user_id)
        if not active:
            return {"ok": False, "error": "❌ Нет активной смены"}

        now = now_minsk()

        # Проверка: не превышено ли время смены?
        shift_duration = now - active["start_time"]
        if shift_duration > MAX_SHIFT:
            return {
                "ok": False,
                "error": f"🔴 РТО: Смена длится {format_duration(shift_duration)}!\nМаксимум: {format_duration(MAX_SHIFT)}\n❌ Немедленно завершите смену!"
            }

        # Закрыть всё
        sessions = active["driving_sessions"]
        if sessions:
            last = sessions[-1]
            if last.get("end") is None:
                last["end"] = now.isoformat()

        breaks = active["breaks"]
        for b in breaks:
            if b.get("end") is None:
                b["end"] = now.isoformat()

        db.update_active_shift(self.user_id, breaks=breaks, driving_sessions=sessions)
        db.end_shift(self.user_id, now)

        shifts = db.get_user_shifts(self.user_id)
        if shifts:
            last_shift = shifts[-1]
            stats = self._calc_shift_stats(last_shift)
            return {"ok": True, "stats": stats}

        return {"ok": False, "error": "Ошибка сохранения смены"}

    def _calc_shift_stats(self, shift: Dict) -> Dict:
        """Рассчитать статистику смены"""
        start = shift["start_time"]
        end = shift["end_time"] or now_minsk()
        total_duration = end - start

        driving_time = timedelta()
        for session in shift["driving_sessions"]:
            s_start = datetime.fromisoformat(session["start"]) if isinstance(session["start"], str) else session["start"]
            s_end = now_minsk() if session.get("end") is None else (
                datetime.fromisoformat(session["end"]) if isinstance(session["end"], str) else session["end"]
            )
            driving_time += s_end - s_start

        break_time = timedelta()
        for b in shift["breaks"]:
            b_start = datetime.fromisoformat(b["start"]) if isinstance(b["start"], str) else b["start"]
            b_end = now_minsk() if b.get("end") is None else (
                datetime.fromisoformat(b["end"]) if isinstance(b["end"], str) else b["end"]
            )
            break_time += b_end - b_start

        return {
            "total": total_duration,
            "driving": driving_time,
            "breaks": break_time,
            "car": shift["car"]
        }

    def get_status(self) -> Dict:
        """Текущий статус РТО"""
        now = now_minsk()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        today_shifts = db.get_user_shifts(self.user_id, since=today_start)
        today_driving = timedelta()
        today_shifts_count = len(today_shifts)

        for shift in today_shifts:
            if shift["end_time"]:
                stats = self._calc_shift_stats(shift)
                today_driving += stats["driving"]

        active = db.get_active_shift(self.user_id)
        if active:
            current_stats = self._calc_shift_stats({
                "start_time": active["start_time"],
                "end_time": now,
                "driving_sessions": active["driving_sessions"],
                "breaks": active["breaks"],
                "car": active["car"]
            })
            today_driving += current_stats["driving"]
            today_shifts_count += 1

            shift_duration = now - active["start_time"]

            warnings = []

            # Проверка непрерывного вождения
            for session in active["driving_sessions"]:
                s_start = datetime.fromisoformat(session["start"]) if isinstance(session["start"], str) else session["start"]
                s_end = now if session.get("end") is None else (
                    datetime.fromisoformat(session["end"]) if isinstance(session["end"], str) else session["end"]
                )
                if (s_end - s_start) > MAX_CONTINUOUS_DRIVE:
                    warnings.append(f"🔴 КРИТИЧНО: {format_duration(s_end - s_start)} без перерыва! Нужен перерыв 45 мин!")

            if today_driving > MAX_DAILY_DRIVE:
                warnings.append(f"🔴 КРИТИЧНО: Превышен лимит 9 часов в сутки! ({format_duration(today_driving)})")

            if shift_duration > MAX_SHIFT:
                warnings.append(f"🔴 КРИТИЧНО: Смена {format_duration(shift_duration)}! Максимум {format_duration(MAX_SHIFT)}!")

            fatigue = min(100, int((current_stats["driving"].total_seconds() / 3600) * 10))

            return {
                "active": True,
                "shift_duration": shift_duration,
                "driving_today": today_driving,
                "shifts_today": today_shifts_count,
                "current_stats": current_stats,
                "warnings": warnings,
                "fatigue": fatigue,
                "car": active["car"]
            }

        return {
            "active": False,
            "driving_today": today_driving,
            "shifts_today": today_shifts_count,
            "fatigue": 0
        }

    def get_weekly_stats(self) -> Dict:
        """Статистика за неделю"""
        week_start = get_week_start()

        week_shifts = db.get_user_shifts(self.user_id, since=week_start)
        weekly_driving = timedelta()
        shifts_count = len(week_shifts)

        for shift in week_shifts:
            if shift["end_time"]:
                stats = self._calc_shift_stats(shift)
                weekly_driving += stats["driving"]

        active = db.get_active_shift(self.user_id)
        if active:
            current_stats = self._calc_shift_stats({
                "start_time": active["start_time"],
                "end_time": now_minsk(),
                "driving_sessions": active["driving_sessions"],
                "breaks": active["breaks"],
                "car": active["car"]
            })
            weekly_driving += current_stats["driving"]
            shifts_count += 1

        remaining = MAX_WEEKLY_DRIVE - weekly_driving

        return {
            "driving": weekly_driving,
            "shifts": shifts_count,
            "remaining": remaining if remaining.total_seconds() > 0 else timedelta(),
            "limit_exceeded": remaining.total_seconds() < 0
        }


def get_session(user_id: int) -> RTOSession:
    return RTOSession(user_id)
