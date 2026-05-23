# database.py
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.environ.get("DB_PATH", "taxi_bot.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создать все таблицы"""
    conn = get_db()
    c = conn.cursor()

    # Смены
    c.execute('''
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        car TEXT DEFAULT 'Основное',
        breaks TEXT DEFAULT '[]',
        driving_sessions TEXT DEFAULT '[]',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Активные смены (текущие)
    c.execute('''
    CREATE TABLE IF NOT EXISTS active_shifts (
        user_id INTEGER PRIMARY KEY,
        start_time TEXT NOT NULL,
        car TEXT DEFAULT 'Основное',
        breaks TEXT DEFAULT '[]',
        driving_sessions TEXT DEFAULT '[]',
        fatigue_level INTEGER DEFAULT 0
    )
    ''')

    # Автомобили
    c.execute('''
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        car_name TEXT NOT NULL,
        is_default INTEGER DEFAULT 0,
        UNIQUE(user_id, car_name)
    )
    ''')

    # Семейный доступ
    c.execute('''
    CREATE TABLE IF NOT EXISTS family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        member_id INTEGER NOT NULL,
        member_name TEXT DEFAULT 'Пользователь',
        UNIQUE(owner_id, member_id)
    )
    ''')

    # Достижения
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_achievements (
        user_id INTEGER PRIMARY KEY,
        earned TEXT DEFAULT '[]',
        total_shifts INTEGER DEFAULT 0,
        consecutive_days INTEGER DEFAULT 0,
        total_earnings REAL DEFAULT 0,
        early_starts INTEGER DEFAULT 0,
        night_shifts INTEGER DEFAULT 0,
        safe_hours REAL DEFAULT 0,
        last_work_date TEXT
    )
    ''')

    # Расписание
    c.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        user_id INTEGER PRIMARY KEY,
        morning_start TEXT,
        morning_end TEXT,
        evening_start TEXT,
        evening_end TEXT
    )
    ''')

    # Настройки пользователя
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        hourly_rate REAL DEFAULT 25
    )
    ''')

    conn.commit()
    conn.close()

# === СМЕНЫ ===

def save_shift(user_id: int, start_time: datetime, car: str = "Основное"):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO shifts (user_id, start_time, car) VALUES (?, ?, ?)",
        (user_id, start_time.isoformat(), car)
    )
    conn.commit()
    conn.close()
    return c.lastrowid

def save_active_shift(user_id: int, start_time: datetime, car: str = "Основное",
                      breaks: list = None, driving_sessions: list = None, fatigue: int = 0):
    conn = get_db()
    c = conn.cursor()
    breaks_json = json.dumps(breaks or [])
    sessions_json = json.dumps(driving_sessions or [{"start": start_time.isoformat(), "end": None}])
    c.execute('''
        INSERT OR REPLACE INTO active_shifts
        (user_id, start_time, car, breaks, driving_sessions, fatigue_level)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, start_time.isoformat(), car, breaks_json, sessions_json, fatigue))
    conn.commit()
    conn.close()

def get_active_shift(user_id: int) -> Optional[Dict]:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM active_shifts WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row["user_id"],
            "start_time": datetime.fromisoformat(row["start_time"]),
            "car": row["car"],
            "breaks": json.loads(row["breaks"]),
            "driving_sessions": json.loads(row["driving_sessions"]),
            "fatigue_level": row["fatigue_level"]
        }
    return None

def update_active_shift(user_id: int, breaks: list = None,
                        driving_sessions: list = None, fatigue: int = None):
    conn = get_db()
    c = conn.cursor()
    updates = []
    params = []
    if breaks is not None:
        updates.append("breaks = ?")
        params.append(json.dumps(breaks))
    if driving_sessions is not None:
        updates.append("driving_sessions = ?")
        params.append(json.dumps(driving_sessions))
    if fatigue is not None:
        updates.append("fatigue_level = ?")
        params.append(fatigue)
    if updates:
        sql = f"UPDATE active_shifts SET {', '.join(updates)} WHERE user_id = ?"
        params.append(user_id)
        c.execute(sql, params)
        conn.commit()
        conn.close()

def delete_active_shift(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM active_shifts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def end_shift(user_id: int, end_time: datetime):
    """Завершить смену: перенести из active_shifts в shifts"""
    conn = get_db()
    c = conn.cursor()

    # Получить активную смену
    c.execute("SELECT * FROM active_shifts WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if row:
        # Вставить завершённую смену в архив
        c.execute('''
            INSERT INTO shifts (user_id, start_time, end_time, car, breaks, driving_sessions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            row["start_time"],
            end_time.isoformat(),
            row["car"],
            row["breaks"],
            row["driving_sessions"]
        ))

        # Удалить активную смену
        c.execute("DELETE FROM active_shifts WHERE user_id = ?", (user_id,))

        conn.commit()

    conn.close()

def get_user_shifts(user_id: int, since: datetime = None) -> List[Dict]:
    conn = get_db()
    c = conn.cursor()
    if since:
        c.execute('''
            SELECT * FROM shifts
            WHERE user_id = ? AND start_time >= ?
            ORDER BY start_time
        ''', (user_id, since.isoformat()))
    else:
        c.execute('''
            SELECT * FROM shifts
            WHERE user_id = ?
            ORDER BY start_time
        ''', (user_id,))
    rows = c.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "start_time": datetime.fromisoformat(row["start_time"]),
            "end_time": datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
            "car": row["car"],
            "breaks": json.loads(row["breaks"]),
            "driving_sessions": json.loads(row["driving_sessions"])
        })
    return result

# === АВТО ===

def add_car(user_id: int, car_name: str):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO cars (user_id, car_name) VALUES (?, ?)", (user_id, car_name))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_user_cars(user_id: int) -> List[Dict]:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM cars WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["car_name"], "is_default": bool(r["is_default"])} for r in rows]

def set_default_car(user_id: int, car_name: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE cars SET is_default = 0 WHERE user_id = ?", (user_id,))
    c.execute(
        "UPDATE cars SET is_default = 1 WHERE user_id = ? AND car_name = ?",
        (user_id, car_name)
    )
    conn.commit()
    conn.close()

def get_default_car(user_id: int) -> str:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT car_name FROM cars WHERE user_id = ? AND is_default = 1", (user_id,))
    row = c.fetchone()
    conn.close()
    return row["car_name"] if row else "Основное"

def remove_car(user_id: int, car_name: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM cars WHERE user_id = ? AND car_name = ?", (user_id, car_name))
    conn.commit()
    conn.close()

# === СЕМЬЯ ===

def add_family_member(owner_id: int, member_id: int, member_name: str = "Пользователь"):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO family_members (owner_id, member_id, member_name) VALUES (?, ?, ?)",
            (owner_id, member_id, member_name)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_family_members(owner_id: int) -> List[Dict]:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM family_members WHERE owner_id = ?", (owner_id,))
    rows = c.fetchall()
    conn.close()
    return [{"member_id": r["member_id"], "name": r["member_name"]} for r in rows]

def remove_family_member(owner_id: int, member_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM family_members WHERE owner_id = ? AND member_id = ?", (owner_id, member_id))
    conn.commit()
    conn.close()

def get_family_count(owner_id: int) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM family_members WHERE owner_id = ?", (owner_id,))
    row = c.fetchone()
    conn.close()
    return row["cnt"]

# === ДОСТИЖЕНИЯ ===

def get_user_achievements_data(user_id: int) -> Dict:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user_achievements WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "earned": json.loads(row["earned"]),
            "total_shifts": row["total_shifts"],
            "consecutive_days": row["consecutive_days"],
            "total_earnings": row["total_earnings"],
            "early_starts": row["early_starts"],
            "night_shifts": row["night_shifts"],
            "safe_hours": row["safe_hours"],
            "last_work_date": row["last_work_date"]
        }

    # Создать запись
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO user_achievements (user_id) VALUES (?)",
        (user_id,)
    )
    conn.commit()
    conn.close()
    return get_user_achievements_data(user_id)

def update_achievements(user_id: int, data: Dict):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE user_achievements SET
        earned = ?,
        total_shifts = ?,
        consecutive_days = ?,
        total_earnings = ?,
        early_starts = ?,
        night_shifts = ?,
        safe_hours = ?,
        last_work_date = ?
        WHERE user_id = ?
    ''', (
        json.dumps(data["earned"]),
        data["total_shifts"],
        data["consecutive_days"],
        data["total_earnings"],
        data["early_starts"],
        data["night_shifts"],
        data["safe_hours"],
        data["last_work_date"],
        user_id
    ))
    conn.commit()
    conn.close()

# === РАСПИСАНИЕ ===

def save_schedule(user_id: int, morning_start: str, morning_end: str,
                  evening_start: str, evening_end: str):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO schedules
        (user_id, morning_start, morning_end, evening_start, evening_end)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, morning_start, morning_end, evening_start, evening_end))
    conn.commit()
    conn.close()

def get_schedule(user_id: int) -> Optional[Dict]:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM schedules WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "morning": {"start": row["morning_start"], "end": row["morning_end"]},
            "evening": {"start": row["evening_start"], "end": row["evening_end"]}
        }
    return None

def delete_schedule(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# === НАСТРОЙКИ ===

def get_user_settings(user_id: int) -> Dict:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"hourly_rate": row["hourly_rate"]}

    # Создать по умолчанию
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    return {"hourly_rate": 25}

def set_hourly_rate(user_id: int, rate: float):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE user_settings SET hourly_rate = ? WHERE user_id = ?",
        (rate, user_id)
    )
    conn.commit()
    conn.close()

# === АВТООЧИСТКА ЗАВИСШИХ СМЕН ===

def cleanup_stale_shifts(max_hours: int = 24):
    """Автоматически завершить смены, которые висят дольше max_hours часов"""
    conn = get_db()
    c = conn.cursor()
    
    cutoff = (datetime.now() - timedelta(hours=max_hours)).isoformat()
    
    # Найти все зависшие смены
    c.execute(
        "SELECT user_id, start_time, car, breaks, driving_sessions FROM active_shifts WHERE start_time < ?",
        (cutoff,)
    )
    stale = c.fetchall()
    
    cleaned_count = 0
    for row in stale:
        user_id = row["user_id"]
        start_time = row["start_time"]
        car = row["car"]
        breaks = row["breaks"]
        sessions = row["driving_sessions"]
        
        # Завершить смену принудительно
        now = datetime.now().isoformat()
        
        # Закрыть все открытые сессии
        breaks_list = json.loads(breaks) if breaks else []
        sessions_list = json.loads(sessions) if sessions else []
        
        for s in sessions_list:
            if s.get("end") is None:
                s["end"] = now
        
        for b in breaks_list:
            if b.get("end") is None:
                b["end"] = now
        
        # Сохранить в архив
        c.execute('''
            INSERT INTO shifts (user_id, start_time, end_time, car, breaks, driving_sessions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, start_time, now, car, json.dumps(breaks_list), json.dumps(sessions_list)))
        
        # Удалить из активных
        c.execute("DELETE FROM active_shifts WHERE user_id = ?", (user_id,))
        cleaned_count += 1
    
    conn.commit()
    conn.close()
    return cleaned_count
