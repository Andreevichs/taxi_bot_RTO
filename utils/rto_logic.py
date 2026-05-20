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

        active = db.get_active_shift(self.user_id)
        if active:
            return {
                "ok": False,
                "error": "❌ У вас уже есть активная смена! Закончите текущую перед началом новой."
            }

        shifts = db.get_user_shifts(self.user_id)
        if shifts:
            last_shift = shifts[-1]
            if last_shift["end_time"]:
                rest = now - last_shift["end_time"]
                if rest < MIN_DAILY_REST:
                    return {
                        "ok": False,
                        "error": f"⏰ Отдых слишком короткий!\nМинимум: {format_duration(MIN_DAILY_REST)}\nПрошло: {format_duration(rest)}"
                    }

        # Проверка: не более 6 дней подряд по РТО!
        week_start = get_week_start()
        week_shifts = db.get_user_shifts(self.user_id, since=week_start)
        if len(week_shifts) >= MAX_CONSECUTIVE_DAYS:
            return {
                "ok": False,
                "error": f"⚠️ РТО: Максимум {MAX_CONSECUTIVE_DAYS} дней подряд!\nОтдохните минимум {format_duration(MIN_DAILY_REST)}."
            }

        # Проверка лимита 56 часов в неделю
        weekly_driving = timedelta()
        for shift in week_shifts:
            if shift["end_time"]:
                stats = self._calc_shift_stats(shift)
                weekly_driving += stats["driving"]

        if weekly_driving >= MAX_WEEKLY_DRIVE:
            return {
                "ok": False,
                "error": f"⚠️ Лимит 56 часов в неделю исчерпан!\nНакоплено: {format_duration(weekly_driving)}"
            }

        db.save_active_shift(self.user_id, now, car)
        return {"ok": True, "start": now}

    def start_break(self) -> Dict:
        """Начать перерыв"""
        active = db.get_active_shift(self.user_id)
        if not active:
            return {"ok": False, "error": "❌ Нет активной смены"}

        now = now_minsk()

        sessions = active["driving_sessions"]
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

        breaks = active["breaks"]
        if breaks:
            last = breaks[-1]
            if last.get("end") is None:
                last["end"] = now.isoformat()

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

            for session in active["driving_sessions"]:
                s_start = datetime.fromisoformat(session["start"]) if isinstance(session["start"], str) else session["start"]
                s_end = now if session.get("end") is None else (
                    datetime.fromisoformat(session["end"]) if isinstance(session["end"], str) else session["end"]
                )
                if (s_end - s_start) > MAX_CONTINUOUS_DRIVE:
                    warnings.append(f"⚠️ Превышено 4.5 часа без перерыва! ({format_duration(s_end - s_start)})")

            if today_driving > MAX_DAILY_DRIVE:
                warnings.append("⚠️ Превышен лимит 9 часов вождения за сутки!")

            if shift_duration > MAX_SHIFT:
                warnings.append("⚠️ Смена дольше 10 часов!")

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
