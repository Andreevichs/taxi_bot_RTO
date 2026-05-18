импорт sqlite3
импорт журнала
из datetime импортировать datetime
от ввода import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_NAME = 'taxi_bot.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Ряд
    возврат конн

def init_db():
    """Инициализация таблиц базы данных"""
    conn = get_connection()
    курсор = conn.cursor()
    
    # Таблица пользователей
    курсор.выполнить('''
        СОЗДАТЬ ТАБЛИЦУ, ЕСЛИ НЕ СУЩЕСТВУЕТ пользователей (
            user_id ЦЕЛОЧИСЛЕННЫЙ ПЕРВИЧНЫЙ КЛЮЧ,
            имя пользователя ТЕКСТ,
            имя_имя ТЕКСТ,
            фамилия_имя ТЕКСТ,
            join_at МЕТКА ВРЕМЕНИ ПО УМОЛЧАНИЮ ТЕКУЩАЯ_МЕТКА ВРЕМЕНИ,
            is_active ЛОГИЧЕСКОЕ ЗНАЧЕНИЕ ПО УМОЛЧАНИЮ 1
        )
    ''')
    
    # Таблица профилей (статистика, достижения)
    курсор.выполнить('''
        СОЗДАТЬ ТАБЛИЦУ, ЕСЛИ НЕ СУЩЕСТВУЕТ профилей (
            user_id ЦЕЛОЧИСЛЕННЫЙ ПЕРВИЧНЫЙ КЛЮЧ,
            total_driving_time ЦЕЛОЕ ЧИСЛО ПО УМОЛЧАНИЮ 0, -- в минутах
            total_breaks ЦЕЛОЕ ЧИСЛО ПО УМОЛЧАНИЮ 0,
            последовательные_дни ЦЕЛОЕ ЧИСЛО ПО УМОЛЧАНИЮ 0,
            последняя_активная_дата ДАТА,
            уровень ЦЕЛОЕ ЧИСЛО ПО УМОЛЧАНИЮ 1,
            xp ЦЕЛОЕ ЧИСЛО ПО УМОЛЧАНИЮ 0,
            ВНЕШНИЙ КЛЮЧ (user_id) ССЫЛКИ пользователи(user_id)
        )
    ''')
    
    # Таблица автомобилей
    курсор.выполнить('''
        СОЗДАТЬ ТАБЛИЦУ, ЕСЛИ АВТОМОБИЛИ НЕ СУЩЕСТВУЮТ (
            id ЦЕЛОЧИСЛЕННЫЙ ПЕРВИЧНЫЙ КЛЮЧ АВТОИНКРЕМЕНТ,
            user_id ЦЕЛОЕ ЧИСЛО,
            ТЕКСТ бренда,
            модель ТЕКСТ,
            license_plate ТЕКСТ,
            цветной ТЕКСТ,
            is_active BOOLEAN DEFAULT 1,
            ВНЕШНИЙ КЛЮЧ (user_id) ССЫЛКИ пользователи(user_id)
        )
    ''')
    
    # Таблица сессий вождения (для проверки 4-часового лимита)
    курсор.выполнить('''
        СОЗДАТЬ ТАБЛИЦУ, ЕСЛИ НЕ СУЩЕСТВУЕТ driving_sessions (
            id ЦЕЛОЧИСЛЕННЫЙ ПЕРВИЧНЫЙ КЛЮЧ АВТОИНКРЕМЕНТ,
            user_id ЦЕЛОЕ ЧИСЛО,
            время_начала МЕТКА ВРЕМЕНИ,
            end_time ВРЕМЕННАЯ МЕТКА,
            продолжительность_минут ЦЕЛОЕ ЧИСЛО,
            статус ТЕКСТ ПО УМОЛЧАНИЮ 'завершено', -- активно, завершено, прервано
            ВНЕШНИЙ КЛЮЧ (user_id) ССЫЛКИ пользователи(user_id)
        )
    ''')
    
    # Таблица семьи
    курсор.выполнить('''
        СОЗДАТЬ ТАБЛИЦУ, ЕСЛИ НЕ СУЩЕСТВУЕТ family_members (
            id ЦЕЛОЧИСЛЕННЫЙ ПЕРВИЧНЫЙ КЛЮЧ АВТОИНКРЕМЕНТ,
            user_id ЦЕЛОЕ ЧИСЛО,
            идентификатор_пользователя_участника ЦЕЛОЕ ЧИСЛО,
            имя_участника ТЕКСТ,
            приглашен_в МЕТКЕ ВРЕМЕНИ ПО УМОЛЧАНИЮ ТЕКУЩАЯ_МЕТКА ВРЕМЕНИ,
            статус ТЕКСТ ПО УМОЛЧАНИЮ 'ожидание', -- ожидание, принято, отклонено
            ВНЕШНИЙ КЛЮЧ (user_id) ССЫЛКИ пользователи(user_id)
        )
    ''')
    
    # Таблица расписаний
    курсор.выполнить('''
        СОЗДАТЬ ТАБЛИЦУ, ЕСЛИ НЕ СУЩЕСТВУЕТ расписаний (
            id ЦЕЛОЧИСЛЕННЫЙ ПЕРВИЧНЫЙ КЛЮЧ АВТОИНКРЕМЕНТ,
            user_id ЦЕЛОЕ ЧИСЛО,
            день_недели ЦЕЛОЕ ЧИСЛО, -- 0=понедельник, 6=воскресенье
            текст_времени начала,
            текст end_time,
            is_active BOOLEAN DEFAULT 1,
            ВНЕШНИЙ КЛЮЧ (user_id) ССЫЛКИ пользователи(user_id)
        )
    ''')
    
    # Таблица достижений
    курсор.выполнить('''
        СОЗДАТЬ ТАБЛИЦУ, ЕСЛИ НЕ СУЩЕСТВУЕТ достижений (
            id ЦЕЛОЧИСЛЕННЫЙ ПЕРВИЧНЫЙ КЛЮЧ АВТОИНКРЕМЕНТ,
            user_id ЦЕЛОЕ ЧИСЛО,
            текст_ключа достижения,
            unlocked_at МЕТКА ВРЕМЕНИ ПО УМОЛЧАНИЮ ТЕКУЩАЯ_МЕТКА ВРЕМЕНИ,
            ВНЕШНИЙ КЛЮЧ (user_id) ССЫЛКИ пользователи(user_id),
            УНИКАЛЬНЫЙ(идентификатор_пользователя, ключ_достижения)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("База данных успешно инициализирована")

класс DatabaseManager:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        init_db()
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = None):
        conn = get_connection()
        курсор = conn.cursor()
        курсор.выполнить('''
            ВСТАВИТЬ ИЛИ ИГНОРИРОВАТЬ В пользователей (user_id, имя пользователя, имя_имя, фамилия_имя)
            ЦЕННОСТИ (?, ?, ?, ?)
        ''', (идентификатор_пользователя, имя_пользователя, имя_имя, фамилия_имя))
        
        # Создаем профиль, если нет
        курсор.выполнить('''
            ВСТАВИТЬ ИЛИ ИГНОРИРОВАТЬ В профили (user_id)
            ЦЕННОСТИ (?)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> Необязательно[Словарь]:
        conn = get_connection()
        курсор = conn.cursor()
        cursor.execute('ВЫБРАТЬ * ИЗ пользователей, ГДЕ user_id = ?', (user_id,))
        строка = курсор.fetchone()
        conn.close()
        вернуть dict(row), если строка иначе Нет
    
    def get_profile(self, user_id: int) -> Необязательно[Словарь]:
        conn = get_connection()
        курсор = conn.cursor()
        cursor.execute('ВЫБРАТЬ * ИЗ профилей, ГДЕ user_id = ?', (user_id,))
        строка = курсор.fetchone()
        conn.close()
        вернуть dict(row), если строка иначе Нет
    
    def update_profile(self, user_id: int, **kwargs):
        conn = get_connection()
        курсор = conn.cursor()
        поля = ', '.join([f"{k} = ?" для k в kwargs.keys()])
        значения = список(kwargs.values()) + [user_id]
        запрос = f'ОБНОВЛЕНИЕ профилей SET {fields} ГДЕ user_id = ?'
        cursor.execute(запрос, значения)
        conn.commit()
        conn.close()
    
    def add_car(self, user_id: int, бренд: str, модель: str, номерной знак: str, цвет: str):
        conn = get_connection()
        курсор = conn.cursor()
        # Деактивируем старые машины
        cursor.execute('ОБНОВЛЕНИЕ автомобилей SET is_active = 0 ГДЕ user_id = ?', (user_id,))
        курсор.выполнить('''
            ВСТАВИТЬ В автомобили (user_id, марка, модель, номерной знак, цвет, is_active)
            ЗНАЧЕНИЯ (?, ?, ?, ?, ?, 1)
        ''', (идентификатор_пользователя, марка, модель, номерной знак, цвет))
        conn.commit()
        conn.close()
    
    def get_active_car(self, user_id: int) -> Необязательно[Словарь]:
        conn = get_connection()
        курсор = conn.cursor()
        cursor.execute('ВЫБРАТЬ * ИЗ автомобилей, ГДЕ user_id = ? И is_active = 1', (user_id,))
        строка = курсор.fetchone()
        conn.close()
        вернуть dict(row), если строка иначе Нет
    
    def start_driving_session(self, user_id: int):
        conn = get_connection()
        курсор = conn.cursor()
        # Закрываем активные сессии, если есть
        курсор.выполнить('''
            ОБНОВЛЕНИЕ driving_sessions 
            SET end_time = CURRENT_TIMESTAMP, 
                продолжительность_минут = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 24 * 60 AS INTEGER),
                статус = 'прервано'
            ГДЕ user_id = ? И статус = 'активный'
        ''', (user_id,))
        
        курсор.выполнить('''
            ВСТАВИТЬ В driving_sessions (user_id, start_time, status)
            ЗНАЧЕНИЯ (?, CURRENT_TIMESTAMP, 'активный')
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def stop_driving_session(self, user_id: int) -> int:
        """Возвращает длительность сессии в минутах"""
        conn = get_connection()
        курсор = conn.cursor()
        
        курсор.выполнить('''
            ВЫБЕРИТЕ идентификатор, время_начала ИЗ driving_sessions 
            ГДЕ user_id = ? И статус = 'активный'
            УПОРЯДОЧИТЬ ПО времени_начала УБЫВАНИЮ ОГРАНИЧЕНИЕ 1
        ''', (user_id,))
        строка = курсор.fetchone()
        
        если нет строки:
            conn.close()
            возврат 0
            
        session_id = строка['id']
        время_начала = строка['время_начала']
        
        курсор.выполнить('''
            ОБНОВЛЕНИЕ driving_sessions 
            SET end_time = CURRENT_TIMESTAMP,
                продолжительность_минут = CAST((julianday(CURRENT_TIMESTAMP) - julianday(?)) * 24 * 60 КАК ЦЕЛОЕ ЧИСЛО),
                статус = 'завершено'
            ГДЕ id = ?
        ''', (время_начала, идентификатор_сеанса))
        
        cursor.execute('ВЫБЕРИТЕ продолжительность_минут ИЗ driving_sessions ГДЕ id = ?', (session_id,))
        продолжительность = cursor.fetchone()['duration_minutes']
        
        # Обновляем общую статистику
        курсор.выполнить('''
            ОБНОВЛЕНИЕ профилей 
            SET общее_время_вождения = общее_время_вождения + ?,
                всего_перерывов = всего_перерывов + 1
            ГДЕ user_id = ?
        ''', (продолжительность, идентификатор_пользователя))
        
        conn.commit()
        conn.close()
        продолжительность возврата
    
    def get_active_session_duration(self, user_id: int) -> int:
        """Возвращает длительность текущей активной сессии в минутах"""
        conn = get_connection()
        курсор = conn.cursor()
        курсор.выполнить('''
            ВЫБЕРИТЕ CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 24 * 60 AS INTEGER) в качестве продолжительности
            ИЗ driving_sessions
            ГДЕ user_id = ? И статус = 'активный'
            УПОРЯДОЧИТЬ ПО времени_начала УБЫВАНИЮ ОГРАНИЧЕНИЕ 1
        ''', (user_id,))
        строка = курсор.fetchone()
        conn.close()
        вернуть строку['duration'], если строка иначе 0
    
    def clear_all_user_data(self, user_id: int):
        """Полная очистка данных пользователя (для теста)"""
        conn = get_connection()
        курсор = conn.cursor()
        
        таблицы = ['достижения', 'расписания', 'члены_семьи', 'сеансы_вождения', 'автомобили', 'профили', 'пользователи']
        
        # Для пользователей и профилей подробнее или удалёем
        cursor.execute('УДАЛИТЬ ИЗ достижений, ГДЕ user_id = ?', (user_id,))
        cursor.execute('УДАЛИТЬ ИЗ расписаний, ГДЕ user_id = ?', (user_id,))
        cursor.execute('УДАЛИТЬ ИЗ family_members, ГДЕ user_id = ?', (user_id,))
        cursor.execute('УДАЛИТЬ ИЗ driving_sessions, ГДЕ user_id = ?', (user_id,))
        cursor.execute('УДАЛИТЬ ИЗ автомобилей, ГДЕ user_id = ?', (user_id,))
        cursor.execute('УДАЛИТЬ ИЗ профилей, ГДЕ user_id = ?', (user_id,))
        cursor.execute('УДАЛИТЬ ИЗ пользователей, ГДЕ user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Все данные очищены для пользователя {user_id}")

# Глобальный экземпляр
db_manager = Менеджер баз данных()
