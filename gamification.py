"""
Модуль геймификации для StudyBoost
Система уровней, баллов и достижений
"""

from typing import List, Dict
import sqlite3


class GamificationSystem:
    def __init__(self):
        # Таблица уровней и требований
        self.level_requirements = {
            1: 0,      # Новичок
            2: 100,    # Студент
            3: 250,    # Прилежный
            4: 500,    # Отличник
            5: 1000,   # Эрудит
            6: 2000,   # Мастер
            7: 3500,   # Профессор
            8: 5500,   # Гений
            9: 8000,   # Легенда
            10: 12000  # Бог учебы
        }
        
        # Эмодзи для уровней
        self.level_emoji = {
            1: "🌱", 2: "📚", 3: "🎓", 4: "⭐", 5: "🏆",
            6: "💎", 7: "👑", 8: "🧠", 9: "⚡", 10: "🔥"
        }
        
        # Определения достижений
        self.achievements = {
            'first_note': {
                'name': 'Первый шаг',
                'description': 'Создай первую заметку',
                'emoji': '🎯',
                'points': 10
            },
            'note_master_10': {
                'name': 'Конспектер',
                'description': 'Создай 10 заметок',
                'emoji': '📝',
                'points': 25
            },
            'note_master_50': {
                'name': 'Мастер заметок',
                'description': 'Создай 50 заметок',
                'emoji': '📚',
                'points': 50
            },
            'note_master_100': {
                'name': 'Библиотекарь',
                'description': 'Создай 100 заметок',
                'emoji': '📖',
                'points': 100
            },
            'streak_3': {
                'name': 'Постоянство',
                'description': 'Будь активен 3 дня подряд',
                'emoji': '🔥',
                'points': 20
            },
            'streak_7': {
                'name': 'Неделя силы',
                'description': 'Будь активен 7 дней подряд',
                'emoji': '💪',
                'points': 50
            },
            'streak_30': {
                'name': 'Железная воля',
                'description': 'Будь активен 30 дней подряд',
                'emoji': '🏅',
                'points': 200
            },
            'quiz_master_5': {
                'name': 'Викторина',
                'description': 'Пройди 5 викторин',
                'emoji': '🎮',
                'points': 30
            },
            'quiz_master_20': {
                'name': 'Эксперт викторин',
                'description': 'Пройди 20 викторин',
                'emoji': '🎯',
                'points': 75
            },
            'perfect_quiz': {
                'name': 'Идеально!',
                'description': 'Ответь правильно на все вопросы викторины',
                'emoji': '💯',
                'points': 40
            },
            'goal_achiever_5': {
                'name': 'Целеустремленный',
                'description': 'Выполни 5 целей',
                'emoji': '🎯',
                'points': 25
            },
            'goal_achiever_25': {
                'name': 'Достигатор',
                'description': 'Выполни 25 целей',
                'emoji': '🏆',
                'points': 75
            },
            'early_bird': {
                'name': 'Ранняя пташка',
                'description': 'Создай заметку до 7 утра',
                'emoji': '🌅',
                'points': 15
            },
            'night_owl': {
                'name': 'Сова',
                'description': 'Создай заметку после 23:00',
                'emoji': '🦉',
                'points': 15
            },
            'multitasker': {
                'name': 'Многозадачность',
                'description': 'Создай заметки по 5 разным предметам',
                'emoji': '🎨',
                'points': 35
            },
            'voice_master': {
                'name': 'Голосовой гуру',
                'description': 'Создай 10 голосовых заметок',
                'emoji': '🎤',
                'points': 30
            },
            'photo_pro': {
                'name': 'Фото-профи',
                'description': 'Создай 15 заметок с фото',
                'emoji': '📷',
                'points': 30
            },
            'tag_master': {
                'name': 'Мастер тегов',
                'description': 'Используй 20 разных тегов',
                'emoji': '#️⃣',
                'points': 25
            },
            'social_butterfly': {
                'name': 'Общительный',
                'description': 'Поделись 10 заметками',
                'emoji': '🤝',
                'points': 40
            },
            'level_5': {
                'name': 'Эрудит',
                'description': 'Достигни 5 уровня',
                'emoji': '🏆',
                'points': 100
            },
            'level_10': {
                'name': 'Бог учебы',
                'description': 'Достигни максимального уровня',
                'emoji': '🔥',
                'points': 500
            }
        }
    
    def get_connection(self):
        """Получение подключения к БД"""
        conn = sqlite3.connect('studyboost.db')
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_points(self, user_id: int, points: int, reason: str = ''):
        """Добавление баллов пользователю"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Добавляем баллы
        cursor.execute('''
            UPDATE users 
            SET total_points = total_points + ?
            WHERE user_id = ?
        ''', (points, user_id))
        
        # Получаем новое количество баллов
        cursor.execute('SELECT total_points FROM users WHERE user_id = ?', 
                      (user_id,))
        total_points = cursor.fetchone()['total_points']
        
        # Проверяем уровень
        new_level = self.calculate_level(total_points)
        cursor.execute('''
            UPDATE users 
            SET current_level = ?
            WHERE user_id = ?
        ''', (new_level, user_id))
        
        # Логируем активность
        cursor.execute('''
            INSERT INTO activity_log (user_id, activity_type, points_earned, description)
            VALUES (?, 'points_earned', ?, ?)
        ''', (user_id, points, reason))
        
        conn.commit()
        conn.close()
        
        return total_points, new_level
    
    def calculate_level(self, total_points: int) -> int:
        """Расчет уровня по баллам"""
        level = 1
        for lvl, required_points in sorted(self.level_requirements.items()):
            if total_points >= required_points:
                level = lvl
            else:
                break
        return level
    
    def get_user_level(self, user_id: int) -> int:
        """Получение текущего уровня пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_level FROM users WHERE user_id = ?', 
                      (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row['current_level'] if row else 1
    
    def get_user_points(self, user_id: int) -> int:
        """Получение баллов пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT total_points FROM users WHERE user_id = ?', 
                      (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row['total_points'] if row else 0
    
    def get_level_info(self, level: int) -> Dict:
        """Получение информации об уровне"""
        return {
            'level': level,
            'emoji': self.level_emoji.get(level, '⭐'),
            'required_points': self.level_requirements.get(level, 0),
            'next_level_points': self.level_requirements.get(level + 1, 0)
        }
    
    def check_achievements(self, user_id: int, db) -> List[str]:
        """Проверка и выдача новых достижений"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Получаем уже полученные достижения
        cursor.execute('''
            SELECT achievement_name FROM achievements WHERE user_id = ?
        ''', (user_id,))
        earned = {row['achievement_name'] for row in cursor.fetchall()}
        
        new_achievements = []
        
        # Получаем статистику
        stats = db.get_detailed_stats(user_id)
        
        # Проверяем достижения по заметкам
        note_count = stats['total_notes']
        if note_count >= 1 and 'first_note' not in earned:
            new_achievements.append('first_note')
        if note_count >= 10 and 'note_master_10' not in earned:
            new_achievements.append('note_master_10')
        if note_count >= 50 and 'note_master_50' not in earned:
            new_achievements.append('note_master_50')
        if note_count >= 100 and 'note_master_100' not in earned:
            new_achievements.append('note_master_100')
        
        # Проверяем достижения по серии
        streak = stats['current_streak']
        if streak >= 3 and 'streak_3' not in earned:
            new_achievements.append('streak_3')
        if streak >= 7 and 'streak_7' not in earned:
            new_achievements.append('streak_7')
        if streak >= 30 and 'streak_30' not in earned:
            new_achievements.append('streak_30')
        
        # Проверяем достижения по викторинам
        quiz_count = stats['quizzes_completed']
        if quiz_count >= 5 and 'quiz_master_5' not in earned:
            new_achievements.append('quiz_master_5')
        if quiz_count >= 20 and 'quiz_master_20' not in earned:
            new_achievements.append('quiz_master_20')
        
        # Проверяем достижения по целям
        goals_completed = stats['completed_goals']
        if goals_completed >= 5 and 'goal_achiever_5' not in earned:
            new_achievements.append('goal_achiever_5')
        if goals_completed >= 25 and 'goal_achiever_25' not in earned:
            new_achievements.append('goal_achiever_25')
        
        # Проверяем достижения по типам заметок
        if stats['voice_notes'] >= 10 and 'voice_master' not in earned:
            new_achievements.append('voice_master')
        if stats['photo_notes'] >= 15 and 'photo_pro' not in earned:
            new_achievements.append('photo_pro')
        
        # Проверяем достижения по уровням
        level = stats['level']
        if level >= 5 and 'level_5' not in earned:
            new_achievements.append('level_5')
        if level >= 10 and 'level_10' not in earned:
            new_achievements.append('level_10')
        
        # Выдаем новые достижения
        achievement_texts = []
        for achievement_key in new_achievements:
            achievement = self.achievements[achievement_key]
            
            # Записываем в БД
            cursor.execute('''
                INSERT INTO achievements (user_id, achievement_name, achievement_description)
                VALUES (?, ?, ?)
            ''', (user_id, achievement_key, achievement['description']))
            
            # Начисляем баллы
            self.add_points(user_id, achievement['points'], 
                          f"Достижение: {achievement['name']}")
            
            achievement_texts.append(
                f"{achievement['emoji']} {achievement['name']} (+{achievement['points']} баллов)"
            )
        
        conn.commit()
        conn.close()
        
        return achievement_texts
    
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Получение всех достижений пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT achievement_name, earned_at 
            FROM achievements 
            WHERE user_id = ?
            ORDER BY earned_at DESC
        ''', (user_id,))
        
        user_achievements = []
        for row in cursor.fetchall():
            achievement_key = row['achievement_name']
            if achievement_key in self.achievements:
                achievement = self.achievements[achievement_key].copy()
                achievement['earned_at'] = row['earned_at']
                user_achievements.append(achievement)
        
        conn.close()
        return user_achievements
    
    def get_available_achievements(self, user_id: int) -> List[Dict]:
        """Получение доступных (еще не полученных) достижений"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT achievement_name FROM achievements WHERE user_id = ?
        ''', (user_id,))
        earned = {row['achievement_name'] for row in cursor.fetchall()}
        conn.close()
        
        available = []
        for key, achievement in self.achievements.items():
            if key not in earned:
                available.append({
                    'key': key,
                    **achievement
                })
        
        return available
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Получение таблицы лидеров"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, first_name, total_points, current_level
            FROM users
            ORDER BY total_points DESC
            LIMIT ?
        ''', (limit,))
        
        leaderboard = []
        for i, row in enumerate(cursor.fetchall(), 1):
            leaderboard.append({
                'rank': i,
                'user_id': row['user_id'],
                'name': row['first_name'],
                'points': row['total_points'],
                'level': row['current_level'],
                'emoji': self.level_emoji.get(row['current_level'], '⭐')
            })
        
        conn.close()
        return leaderboard
