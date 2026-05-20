from typing import Dict, List, Set
from config import ACHIEVEMENTS
from datetime import datetime, timedelta
import database as db
from .time_utils import now_minsk


class AchievementManager:
    def __init__(self):
        pass

    def _get_data(self, user_id: int) -> Dict:
        return db.get_user_achievements_data(user_id)

    def _save_data(self, user_id: int, data: Dict):
        db.update_achievements(user_id, data)

    def _update_consecutive_days(self, user_id: int, data: Dict):
        """Обновить счётчик подряд идущих дней"""
        today = now_minsk().date()
        last_date_str = data.get("last_work_date")

        if last_date_str:
            last_date = datetime.fromisoformat(last_date_str).date()
            diff = (today - last_date).days

            if diff == 1:
                data["consecutive_days"] += 1
            elif diff == 0:
                pass
            else:
                data["consecutive_days"] = 1
        else:
            data["consecutive_days"] = 1

        data["last_work_date"] = today.isoformat()

    def check_achievements(self, Продолжаю отправку оставшихся файлов. Вот остальные утилиты:

---

## `utils/achievements.py` (продолжение)

```python
        user_id: int, event_type: str, data: dict = None) -> List[Dict]:
        """Проверить и выдать достижения"""
        ach_data = self._get_data(user_id)
        new_achievements = []

        if event_type == "shift_end":
            ach_data["total_shifts"] += 1
            self._update_consecutive_days(user_id, ach_data)

            if ach_data["total_shifts"] == 1 and "first_shift" not in ach_data["earned"]:
                new_achievements.append(self._grant(user_id, ach_data, "first_shift"))

            if ach_data["consecutive_days"] >= 7 and "week_worker" not in ach_data["earned"]:
                new_achievements.append(self._grant(user_id, ach_data, "week_worker"))

            if ach_data["total_shifts"] >= 30 and "month_hero" not in ach_data["earned"]:
                new_achievements.append(self._grant(user_id, ach_data, "month_hero"))

            safe_hours = data.get("safe_hours", 0) if data else 0
            ach_data["safe_hours"] += safe_hours
            if ach_data["safe_hours"] >= 100 and "safe_driver" not in ach_data["earned"]:
                new_achievements.append(self._grant(user_id, ach_data, "safe_driver"))

            earnings = data.get("earnings", 0) if data else 0
            ach_data["total_earnings"] += earnings
            if ach_data["total_earnings"] >= 1000 and "money_maker" not in ach_data["earned"]:
                new_achievements.append(self._grant(user_id, ach_data, "money_maker"))

        elif event_type == "shift_start":
            hour = data.get("hour", 12) if data else 12
            if hour < 6 and "early_bird" not in ach_data["earned"]:
                ach_data["early_starts"] += 1
                if ach_data["early_starts"] >= 1:
                    new_achievements.append(self._grant(user_id, ach_data, "early_bird"))
            if hour >= 22 and "night_owl" not in ach_data["earned"]:
                ach_data["night_shifts"] += 1
                if ach_data["night_shifts"] >= 1:
                    new_achievements.append(self._grant(user_id, ach_data, "night_owl"))

        self._save_data(user_id, ach_data)
        return new_achievements

    def _grant(self, user_id: int, ach_data: Dict, achievement_id: str) -> Dict:
        if achievement_id not in ach_data["earned"]:
            ach_data["earned"].append(achievement_id)
        ach = ACHIEVEMENTS[achievement_id]
        return {
            "id": achievement_id,
            "name": ach["name"],
            "desc": ach["desc"]
        }

    def get_user_achievements(self, user_id: int) -> List[Dict]:
        ach_data = self._get_data(user_id)
        result = []
        for ach_id in ach_data["earned"]:
            if ach_id in ACHIEVEMENTS:
                ach = ACHIEVEMENTS[ach_id]
                result.append({"id": ach_id, **ach})
        return result

    def get_progress(self, user_id: int) -> Dict:
        ach_data = self._get_data(user_id)
        total = len(ACHIEVEMENTS)
        earned = len(ach_data["earned"])
        return {
            "earned": earned,
            "total": total,
            "percent": round((earned / total) * 100, 1) if total > 0 else 0
        }
