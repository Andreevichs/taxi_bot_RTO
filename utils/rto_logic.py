from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .time_utils import now_minsk, format_duration, TIMEZONE
from config import (
    MAX_DAILY_DRIVE, MAX_WEEKLY_DRIVE, MAX_CONTINUOUS_DRIVE,
    MIN_BREAK, MIN_DAILY_REST, MAX_SHIFT
)

class RTOSession:
    def __init__(self):
        self.shifts: List[Dict] = []
        self.current_shift: Optional[Dict] = None
        self.fatigue_level = 0

    def start_shift(self, car: str = "Основное") -> Dict:
        now = now_minsk()
        if self.shifts:
            last_end = self.shifts[-1].get("end")
            if last_end:
                rest = now - last_end
                if rest < MIN_DAILY_REST:
                    return {
                        "ok": False,
                        "error": f"Отдых слишком короткий! Минимум {format_duration(MIN_DAILY_REST)}, прошло {format_duration(rest)}"
                    }
        self.current_shift = {
            "start": now,
            "end": None,
            "breaks": [],
            "car": car,
            "driving_sessions": [{"start": now, "end": None}]
        }
        return {"ok": True, "start": now}

    def start_break(self) -> Dict:
        if not self.current_shift:
            return {"ok": False, "error": "Нет активной смены"}
        now = now_minsk()
        if self.current_shift["driving_sessions"]:
            last = self.current_shift["driving_sessions"][-1]
            if last["end"] is None:
                last["end"] = now
        self.current_shift["breaks"].append({"start": now, "end": None})
        return {"ok": True, "start": now}

    def end_break(self) -> Dict:
        if not self.current_shift:
            return {"ok": False, "error": "Нет активной смены"}
        now = now_minsk()
        if self.current_shift["breaks"]:
            last = self.current_shift["breaks"][-1]
            if last["end"] is None:
                last["end"] = now
        self.current_shift["driving_sessions"].append({"start": now, "end": None})
        return {"ok": True, "end": now}

    def end_shift(self) -> Dict:
        if not self.current_shift:
            return {"ok": False, "error": "Нет активной смены"}
        now = now_minsk()
        if self.current_shift["driving_sessions"]:
            last = self.current_shift["driving_sessions"][-1]
            if last["end"] is None:
                last["end"] = now
        for b in self.current_shift["breaks"]:
            if b["end"] is None:
                b["end"] = now
        self.current_shift["end"] = now
        self.shifts.append(self.current_shift)
        stats = self._calc_shift_stats(self.current_shift)
        self.current_shift = None
        return {"ok": True, "stats": stats}

    def _calc_shift_stats(self, shift: Dict) -> Dict:
        total_duration = shift["end"] - shift["start"]
        driving_time = timedelta()
        for session in shift["driving_sessions"]:
            end = session["end"] or now_minsk()
            driving_time += end - session["start"]
        break_time = timedelta()
        for b in shift["breaks"]:
            end = b["end"] or now_minsk()
            break_time += end - b["start"]
        return {
            "total": total_duration,
            "driving": driving_time,
            "breaks": break_time,
            "car": shift["car"]
        }

    def get_status(self) -> Dict:
        now = now_minsk()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_driving = timedelta()
        today_shifts = 0
        for shift in self.shifts:
            if shift["start"] >= today_start:
                stats = self._calc_shift_stats(shift)
                today_driving += stats["driving"]
                today_shifts += 1
        if self.current_shift:
            stats = self._calc_shift_stats({**self.current_shift, "end": now})
            today_driving += stats["driving"]
            today_shifts += 1
            warnings = []
            if stats["driving"] > MAX_CONTINUOUS_DRIVE:
                warnings.append("⚠️ Превышено 4 часа без перерыва!")
            if today_driving > MAX_DAILY_DRIVE:
                warnings.append("⚠️ Превышен лимит 9 часов вождения за сутки!")
            shift_duration = now - self.current_shift["start"]
            if shift_duration > MAX_SHIFT:
                warnings.append("⚠️ Смена дольше 13 часов!")
            self.fatigue_level = min(100, int((stats["driving"].total_seconds() / 3600) * 10))
            return {
                "active": True,
                "shift_duration": shift_duration,
                "driving_today": today_driving,
                "current_stats": stats,
                "warnings": warnings,
                "fatigue": self.fatigue_level,
                "car": self.current_shift["car"]
            }
        return {
            "active": False,
            "driving_today": today_driving,
            "shifts_today": today_shifts,
            "fatigue": max(0, self.fatigue_level - 20)
        }

    def get_weekly_stats(self) -> Dict:
        from .time_utils import get_week_start
        week_start = get_week_start()
        weekly_driving = timedelta()
        shifts_count = 0
        for shift in self.shifts:
            if shift["start"] >= week_start:
                stats = self._calc_shift_stats(shift)
                weekly_driving += stats["driving"]
                shifts_count += 1
        if self.current_shift:
            stats = self._calc_shift_stats({**self.current_shift, "end": now_minsk()})
            weekly_driving += stats["driving"]
            shifts_count += 1
        remaining = MAX_WEEKLY_DRIVE - weekly_driving
        return {
            "driving": weekly_driving,
            "shifts": shifts_count,
            "remaining": remaining if remaining.total_seconds() > 0 else timedelta(),
            "limit_exceeded": remaining.total_seconds() < 0
        }
