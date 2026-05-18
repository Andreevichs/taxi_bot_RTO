import sqlite3
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)
DB_NAME = 'taxi_bot.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создание всех необходимых таблиц"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Таблица профилей (статистика РТО)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            total_driving_minutes INTEGER DEFAULT 0,
            total_breaks INTEGER DEFAULT 0,
            consecutive_days INTEGER DEFAULT 0,
            last_active_date DATE,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица автомобилей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            brand TEXT,
            model TEXT,
            license_plate TEXT,
            color TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица сессий вождения (для РТО)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS driving_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_minutes INTEGER,
            status TEXT DEFAULT 'completed',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица семьи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            member_user_id INTEGER,
            member_name TEXT,
            invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица расписаний
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            day_of_week INTEGER,
            start_time TEXT,
            end_time TEXT,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Таблица достижений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_key TEXT,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, achievement_key)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

class DatabaseManager:
    def __init__(self):
        pass
    
    def init_db(self):
        init_db()
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = None):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        
        cursor.execute('''
            INSERT OR IGNORE INTO profiles (user_id)
            VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_profile(self, user_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_profile(self, user_id: int, **kwargs):
        if not kwargs:
            return
        conn = get_connection()
        cursor = conn.cursor()
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        query = f'UPDATE profiles SET {fields} WHERE user_id = ?'
        cursor.execute(query, values)
        conn.commit()
        conn.close()
    
    # === РТО: СТАТИСТИКА ЗА СЕГОДНЯ ===
    def get_today_driving_minutes(self, user_id: int) -> int:
        """Сколько минут за рулём сегодня (для проверки лимита 9 часов)"""
        conn = get_connection()
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute('''
            SELECT COALESCE(SUM(duration_minutes), 0) as total
            FROM driving_sessions
            WHERE user_id = ? AND date(start_time) = ? AND status = 'completed'
        ''', (user_id, today))
        row = cursor.fetchone()
        conn.close()
        return row['total'] if row else 0
    
    def get_week_driving_minutes(self, user_id: int) -> int:
        """Сколько минут за рулём за неделю (для проверки лимита 56 часов)"""
        conn = get_connection()
        cursor = conn.cursor()
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        cursor.execute('''
            SELECT COALESCE(SUM(duration_minutes), 0) as total
            FROM driving_sessions
            WHERE user_id = ? AND date(start_time) >= ? AND status = 'completed'
        ''', (user_id, week_ago))
        row = cursor.fetchone()
        conn.close()
        return row['total'] if row else 0
    
    # === АВТО ===
    def add_car(self, user_id: int, brand: str, model: str, plate: str, color: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE cars SET is_active = 0 WHERE user_id = ?', (user_id,))
        cursor.execute('''
            INSERT INTO cars (user_id, brand, model, license_plate, color, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (user_id, brand, model, plate, color))
        conn.commit()
        conn.close()
    
    def get_active_car(self, user_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cars WHERE user_id = ? AND is_active = 1', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_cars(self, user_id: int) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cars WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # === СЕССИИ ВОЖДЕНИЯ (РТО) ===
    def start_driving_session(self, user_id: int) -> bool:
        """Начать смену. Возвращает False, если уже есть активная."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, нет ли активной сессии
        cursor.execute('''
            SELECT id FROM driving_sessions 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        if cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute('''
            INSERT INTO driving_sessions (user_id, start_time, status)
            VALUES (?, datetime('now'), 'active')
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def stop_driving_session(self, user_id: int) -> int:
        """Закончить смену. Возвращает длительность в минутах."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, start_time FROM driving_sessions 
            WHERE user_id = ? AND status = 'active'
            ORDER BY start_time DESC LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return 0
            
        session_id = row['id']
        start_time = row['start_time']
        
        # Вычисляем длительность в Python (точнее)
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        now_dt = datetime.now()
        duration = int((now_dt - start_dt).total_seconds() / 60)
        
        cursor.execute('''
            UPDATE driving_sessions 
            SET end_time = datetime('now'),
                duration_minutes = ?,
                status = 'completed'
            WHERE id = ?
        ''', (duration, session_id))
        
        # Обновляем статистику
        if duration > 0:
            cursor.execute('''
                UPDATE profiles 
                SET total_driving_minutes = total_driving_minutes + ?
                WHERE user_id = ?
            ''', (duration, user_id))
        
        conn.commit()
        conn.close()
        return duration
    
    def get_active_session_duration(self, user_id: int) -> int:
        """Сколько минут идёт текущая смена."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT start_time FROM driving_sessions
            WHERE user_id = ? AND status = 'active'
            ORDER BY start_time DESC LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return 0
        
        start_dt = datetime.fromisoformat(row['start_time'].replace('Z', '+00:00'))
        return int((datetime.now() - start_dt).total_seconds() / 60)
    
    def has_active_session(self, user_id: int) -> bool:
        """Есть ли активная смена?"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM driving_sessions 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    # === ОЧИСТКА ДАННЫХ ===
    def clear_all_user_data(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        tables = ['achievements', 'schedules', 'family_members', 
                  'driving_sessions', 'cars', 'profiles', 'users']
        
        for table in tables:
            cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"All data cleared for user {user_id}")

db_manager = DatabaseManager()
