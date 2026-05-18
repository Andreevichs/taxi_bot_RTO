import sqlite3
import logging
from datetime import datetime, date
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
    
    # 1. Таблица пользователей
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
    
    # 2. Таблица профилей (статистика)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            total_driving_time INTEGER DEFAULT 0,
            total_breaks INTEGER DEFAULT 0,
            consecutive_days INTEGER DEFAULT 0,
            last_active_date DATE,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # 3. Таблица автомобилей
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
    
    # 4. Таблица сессий вождения (для РТО)
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
    
    # 5. Таблица семьи
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
    
    # 6. Таблица расписаний
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
    
    # 7. Таблица достижений
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
        pass # Инициализация происходит при импорте модуля
    
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
        if not kwargs: return
        conn = get_connection()
        cursor = conn.cursor()
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        query = f'UPDATE profiles SET {fields} WHERE user_id = ?'
        cursor.execute(query, values)
        conn.commit()
        conn.close()
    
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
    
    def start_driving_session(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE driving_sessions 
            SET end_time = CURRENT_TIMESTAMP, 
                duration_minutes = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 24 * 60 AS INTEGER),
                status = 'interrupted'
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        cursor.execute('''
            INSERT INTO driving_sessions (user_id, start_time, status)
            VALUES (?, CURRENT_TIMESTAMP, 'active')
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def stop_driving_session(self, user_id: int) -> int:
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
        
        cursor.execute('''
            UPDATE driving_sessions 
            SET end_time = CURRENT_TIMESTAMP,
                duration_minutes = CAST((julianday(CURRENT_TIMESTAMP) - julianday(?)) * 24 * 60 AS INTEGER),
                status = 'completed'
            WHERE id = ?
        ''', (start_time, session_id))
        
        cursor.execute('SELECT duration_minutes FROM driving_sessions WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        duration = result['duration_minutes'] if result else 0
        
        if duration > 0:
            cursor.execute('''
                UPDATE profiles 
                SET total_driving_time = total_driving_time + ?,
                    total_breaks = total_breaks + 1
                WHERE user_id = ?
            ''', (duration, user_id))
        
        conn.commit()
        conn.close()
        return duration
    
    def get_active_session_duration(self, user_id: int) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 24 * 60 AS INTEGER) as duration
            FROM driving_sessions
            WHERE user_id = ? AND status = 'active'
            ORDER BY start_time DESC LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row['duration'] if row else 0
    
    def clear_all_user_data(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        tables = ['achievements', 'schedules', 'family_members', 'driving_sessions', 'cars', 'profiles', 'users']
        
        for table in ['achievements', 'schedules', 'family_members', 'driving_sessions', 'cars', 'profiles']:
            cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
        
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"All data cleared for user {user_id}")

db_manager = DatabaseManager()
