from typing import Dict, List, Set
from config import ACHIEVEMENTS

class AchievementManager:
    def __init__(self):
        self.user_achievements: Dict[int, Set[str]] = {}
        self.user_stats: Dict[int, Dict] = {}

    def init_user(self, user_id: int):
        if user_id not in self.user_achievements:
            self.user_achievements[user_id] = set()
            self.user_stats[user_id] = {
                "total_shifts": 0,
                "consecutive_days": 0,
                "total_earnings": 0,
                "early_starts": 0,
                "night_shifts": 0,
                "safe_hours": 0,
                "last_work_date": None
            }

    def check_achievements(self, user_id: int, event_type: str, data: dict = None) -> List[Dict]:
        self.init_user(user_id)
        new_achievements = []
        stats = self.user_stats[user_id]

        if event_type == "shift_end":
            stats["total_shifts"] += 1
            if stats["total_shifts"] == 1 and "first_shift" not in self.user_achievements[user_id]:
                new_achievements.append(self._grant(user_id, "first_shift"))
            if stats["consecutive_days"] >= 7 and "week_worker" not in self.user_achievements[user_id]:
                new_achievements.append(self._grant(user_id, "week_worker"))
            if stats["total_shifts"] >= 30 and "month_hero" not in self.user_achievements[user_id]:
                new_achievements.append(self._grant(user_id, "month_hero"))
            safe_hours = data.get("safe_hours", 0) if data else 0
            stats["safe_hours"] += safe_hours
            if stats["safe_hours"] >= 100 and "safe_driver" not in self.user_achievements[user_id]:
                new_achievements.append(self._grant(user_id, "safe_driver"))
            earnings = data.get("earnings", 0) if data else 0
            stats["total_earnings"] += earnings
            if stats["total_earnings"] >= 1000 and "money_maker" not in self.user_achievements[user_id]:
                new_achievements.append(self._grant(user_id, "money_maker"))

        elif event_type == "shift_start":
            hour = data.get("hour", 12) if data else 12
            if hour < 6 and "early_bird" not in self.user_achievements[user_id]:
                new_achievements.append(self._grant(user_id, "early_bird"))
            if hour >= 22 and "night_owl" not in self.user_achievements[user_id]:
                new_achievements.append(self._grant(user_id, "night_owl"))

        return new_achievements

    def _grant(self, user_id: int, achievement_id: str) -> Dict:
        self.user_achievements[user_id].add(achievement_id)
        ach = ACHIEVEMENTS[achievement_id]
        return {
            "id": achievement_id,
            "name": ach["name"],
            "desc": ach["desc"]
        }

    def get_user_achievements(self, user_id: int) -> List[Dict]:
        self.init_user(user_id)
        result = []
        for ach_id in self.user_achievements[user_id]:
            ach = ACHIEVEMENTS[ach_id]
            result.append({"id": ach_id, **ach})
        return result

    def get_progress(self, user_id: int) -> Dict:
        self.init_user(user_id)
        total = len(ACHIEVEMENTS)
        earned = len(self.user_achievements[user_id])
        return {
            "earned": earned,
            "total": total,
            "percent": round((earned / total) * 100, 1)
        }
