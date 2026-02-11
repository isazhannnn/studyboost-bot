"""
Модуль для работы с базой данных StudyBoost
Использует SQLite для хранения всех данных
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class Database:
    def __init__(self, db_name='studyboost.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Получение подключения к БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_points INTEGER DEFAULT 0,
                current_level INTEGER DEFAULT 1,
                last_active DATE,
                streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                settings TEXT DEFAULT '{}'
            )
        ''')
        
        # Таблица заметок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                note_type TEXT,
                content TEXT,
                file_id TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица целей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                goal_type TEXT,
                deadline DATE,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица достижений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_name TEXT,
                achievement_description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица активности (для статистики)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT,
                points_earned INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица викторин
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                score INTEGER,
                total_questions INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица расписания
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                day_of_week INTEGER,
                start_time TEXT,
                end_time TEXT,
                location TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица для отслеживания прочитанных советов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_tips_read (
                user_id INTEGER,
                date DATE,
                PRIMARY KEY (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # === РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ===
    
    def user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def create_user(self, user_id: int, first_name: str, username: str = None):
        """Создание нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_active)
            VALUES (?, ?, ?, DATE('now'))
        ''', (user_id, username, first_name))
        conn.commit()
        conn.close()
    
    def update_activity(self, user_id: int):
        """Обновление активности пользователя и подсчет серии"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Получаем последнюю активность
        cursor.execute('SELECT last_active, streak FROM users WHERE user_id = ?', 
                      (user_id,))
        row = cursor.fetchone()
        
        if row:
            last_active = datetime.strptime(row['last_active'], '%Y-%m-%d').date()
            today = datetime.now().date()
            current_streak = row['streak']
            
            # Проверяем серию
            if last_active == today:
                # Уже был сегодня активен
                pass
            elif last_active == today - timedelta(days=1):
                # Продолжение серии
                current_streak += 1
                cursor.execute('''
                    UPDATE users 
                    SET streak = ?, best_streak = MAX(best_streak, ?), last_active = DATE('now')
                    WHERE user_id = ?
                ''', (current_streak, current_streak, user_id))
            else:
                # Серия прервана
                cursor.execute('''
                    UPDATE users 
                    SET streak = 1, last_active = DATE('now')
                    WHERE user_id = ?
                ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Получение настроек пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT settings FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['settings'] or '{}')
        return {}
    
    def update_user_settings(self, user_id: int, settings: Dict):
        """Обновление настроек пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET settings = ? WHERE user_id = ?
        ''', (json.dumps(settings), user_id))
        conn.commit()
        conn.close()
    
    # === РАБОТА С ЗАМЕТКАМИ ===
    
    def save_note(self, note_data: Dict) -> int:
        """Сохранение заметки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notes (user_id, category, note_type, content, file_id, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            note_data['user_id'],
            note_data['category'],
            note_data['type'],
            note_data.get('content', ''),
            note_data.get('file_id', ''),
            json.dumps(note_data.get('tags', []))
        ))
        
        note_id = cursor.lastrowid
        
        # Обновляем активность
        self.update_activity(note_data['user_id'])
        
        conn.commit()
        conn.close()
        return note_id
    
    def get_user_notes(self, user_id: int, category: str = None) -> List[Dict]:
        """Получение заметок пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM notes 
                WHERE user_id = ? AND category = ?
                ORDER BY created_at DESC
            ''', (user_id, category))
        else:
            cursor.execute('''
                SELECT * FROM notes 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
        
        notes = []
        for row in cursor.fetchall():
            note = dict(row)
            note['tags'] = json.loads(note['tags'])
            notes.append(note)
        
        conn.close()
        return notes
    
    def get_notes_by_tags(self, user_id: int, tags: List[str]) -> List[Dict]:
        """Поиск заметок по тегам"""
        notes = self.get_user_notes(user_id)
        filtered = []
        
        for note in notes:
            note_tags = set(note['tags'])
            if any(tag in note_tags for tag in tags):
                filtered.append(note)
        
        return filtered
    
    # === РАБОТА С ЦЕЛЯМИ ===
    
    def add_goal(self, user_id: int, title: str, description: str = '', 
                 goal_type: str = 'daily', deadline: datetime = None) -> int:
        """Добавление новой цели"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO goals (user_id, title, description, goal_type, deadline)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, description, goal_type, deadline))
        
        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return goal_id
    
    def get_user_goals(self, user_id: int, active_only: bool = False) -> List[Dict]:
        """Получение целей пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute('''
                SELECT * FROM goals 
                WHERE user_id = ? AND completed = 0
                ORDER BY deadline ASC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT * FROM goals 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
        
        goals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return goals
    
    def complete_goal(self, goal_id: int):
        """Отметка цели как выполненной"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE goals 
            SET completed = 1, completed_at = CURRENT_TIMESTAMP
            WHERE goal_id = ?
        ''', (goal_id,))
        conn.commit()
        conn.close()
    
    # === СТАТИСТИКА ===
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Базовая статистика пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Общая информация
        cursor.execute('''
            SELECT total_points, current_level, streak, best_streak
            FROM users WHERE user_id = ?
        ''', (user_id,))
        user_data = dict(cursor.fetchone())
        
        # Количество заметок
        cursor.execute('SELECT COUNT(*) as count FROM notes WHERE user_id = ?', 
                      (user_id,))
        user_data['total_notes'] = cursor.fetchone()['count']
        
        # Выполненные цели сегодня
        cursor.execute('''
            SELECT COUNT(*) as count FROM goals 
            WHERE user_id = ? AND DATE(completed_at) = DATE('now')
        ''', (user_id,))
        user_data['goals_completed_today'] = cursor.fetchone()['count']
        
        conn.close()
        return user_data
    
    def get_detailed_stats(self, user_id: int) -> Dict:
        """Подробная статистика"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Данные пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = dict(cursor.fetchone())
        stats['level'] = user['current_level']
        stats['total_points'] = user['total_points']
        stats['current_streak'] = user['streak']
        stats['best_streak'] = user['best_streak']
        stats['join_date'] = datetime.strptime(user['created_at'], 
                                               '%Y-%m-%d %H:%M:%S')
        
        # Статистика заметок
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN note_type = 'text' THEN 1 ELSE 0 END) as text,
                SUM(CASE WHEN note_type = 'photo' THEN 1 ELSE 0 END) as photo,
                SUM(CASE WHEN note_type = 'voice' THEN 1 ELSE 0 END) as voice
            FROM notes WHERE user_id = ?
        ''', (user_id,))
        notes_stats = dict(cursor.fetchone())
        stats['total_notes'] = notes_stats['total']
        stats['text_notes'] = notes_stats['text'] or 0
        stats['photo_notes'] = notes_stats['photo'] or 0
        stats['voice_notes'] = notes_stats['voice'] or 0
        
        # Статистика целей
        cursor.execute('''
            SELECT COUNT(*) as count FROM goals 
            WHERE user_id = ? AND completed = 1
        ''', (user_id,))
        stats['completed_goals'] = cursor.fetchone()['count']
        
        # Статистика викторин
        cursor.execute('''
            SELECT 
                COUNT(*) as quizzes,
                SUM(score) as correct,
                SUM(total_questions) as total
            FROM quiz_results WHERE user_id = ?
        ''', (user_id,))
        quiz_stats = dict(cursor.fetchone())
        stats['quizzes_completed'] = quiz_stats['quizzes'] or 0
        stats['correct_answers'] = quiz_stats['correct'] or 0
        stats['total_answers'] = quiz_stats['total'] or 0
        
        conn.close()
        return stats
    
    # === АКТИВНОСТЬ ===
    
    def log_activity(self, user_id: int, activity_type: str, 
                    points: int, description: str = ''):
        """Логирование активности"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_log (user_id, activity_type, points_earned, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, activity_type, points, description))
        conn.commit()
        conn.close()
    
    def tip_read_today(self, user_id: int) -> bool:
        """Проверка, читал ли пользователь совет сегодня"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM daily_tips_read 
            WHERE user_id = ? AND date = DATE('now')
        ''', (user_id,))
        read = cursor.fetchone() is not None
        conn.close()
        return read
    
    def mark_tip_read(self, user_id: int):
        """Отметка чтения совета дня"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO daily_tips_read (user_id, date)
            VALUES (?, DATE('now'))
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    # === РАСПИСАНИЕ ===
    
    def add_schedule_item(self, user_id: int, subject: str, day_of_week: int,
                         start_time: str, end_time: str, location: str = ''):
        """Добавление занятия в расписание"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedule (user_id, subject, day_of_week, start_time, end_time, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, subject, day_of_week, start_time, end_time, location))
        conn.commit()
        conn.close()
    
    def get_schedule(self, user_id: int, day_of_week: int = None) -> List[Dict]:
        """Получение расписания"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if day_of_week is not None:
            cursor.execute('''
                SELECT * FROM schedule 
                WHERE user_id = ? AND day_of_week = ?
                ORDER BY start_time
            ''', (user_id, day_of_week))
        else:
            cursor.execute('''
                SELECT * FROM schedule 
                WHERE user_id = ?
                ORDER BY day_of_week, start_time
            ''', (user_id,))
        
        schedule = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return schedule
