import sqlite3
import json
from datetime import datetime
import os

class BotUtils:
    def __init__(self, db_name='studyboost.db'):
        self.db_name = db_name
    
    def backup_database(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}.db'
        
        if os.path.exists(self.db_name):
            import shutil
            shutil.copy2(self.db_name, backup_name)
            print(f"✅ Резервная копия создана: {backup_name}")
            return backup_name
        else:
            print("❌ База данных не найдена")
            return None
    
    def export_user_data(self, user_id, output_file=None):
        if not output_file:
            output_file = f'user_{user_id}_export_{datetime.now().strftime("%Y%m%d")}.json'
        
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        data = {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'user_info': {},
            'notes': [],
            'goals': [],
            'achievements': [],
            'stats': {}
        }
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_row = cursor.fetchone()
        if user_row:
            data['user_info'] = dict(user_row)
        
        cursor.execute('SELECT * FROM notes WHERE user_id = ?', (user_id,))
        for row in cursor.fetchall():
            data['notes'].append(dict(row))
        
        cursor.execute('SELECT * FROM goals WHERE user_id = ?', (user_id,))
        for row in cursor.fetchall():
            data['goals'].append(dict(row))
        
        cursor.execute('SELECT * FROM achievements WHERE user_id = ?', (user_id,))
        for row in cursor.fetchall():
            data['achievements'].append(dict(row))
        
        conn.close()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Данные пользователя экспортированы: {output_file}")
        return output_file
    
    def get_statistics(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM users')
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM notes')
        stats['total_notes'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM goals')
        stats['total_goals'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM achievements')
        stats['total_achievements'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_points) FROM users')
        result = cursor.fetchone()[0]
        stats['total_points'] = result if result else 0
        
        cursor.execute('''
            SELECT note_type, COUNT(*) 
            FROM notes 
            GROUP BY note_type
        ''')
        stats['notes_by_type'] = {}
        for row in cursor.fetchall():
            stats['notes_by_type'][row[0]] = row[1]
        
        cursor.execute('''
            SELECT category, COUNT(*) 
            FROM notes 
            GROUP BY category 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        ''')
        stats['top_categories'] = {}
        for row in cursor.fetchall():
            stats['top_categories'][row[0]] = row[1]
        
        conn.close()
        
        return stats
    
    def print_statistics(self):
        stats = self.get_statistics()
        
        print("\n📊 Общая статистика бота")
        print("=" * 50)
        print(f"👥 Всего пользователей: {stats['total_users']}")
        print(f"📝 Всего заметок: {stats['total_notes']}")
        print(f"🎯 Всего целей: {stats['total_goals']}")
        print(f"🏆 Всего достижений выдано: {stats['total_achievements']}")
        print(f"⭐ Общая сумма баллов: {stats['total_points']}")
        
        print("\n📊 Заметки по типам:")
        for note_type, count in stats['notes_by_type'].items():
            print(f"  {note_type}: {count}")
        
        print("\n📚 Топ-5 категорий:")
        for i, (category, count) in enumerate(stats['top_categories'].items(), 1):
            print(f"  {i}. {category}: {count}")
        print()
    
    def clean_old_data(self, days=90):
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM activity_log 
            WHERE created_at < ?
        ''', (cutoff_date.strftime('%Y-%m-%d'),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ Удалено старых записей активности: {deleted}")
    
    def reset_user_data(self, user_id):
        print(f"⚠️  ВНИМАНИЕ! Будут удалены ВСЕ данные пользователя {user_id}")
        confirm = input("Введите 'ПОДТВЕРДИТЬ' для продолжения: ")
        
        if confirm != 'ПОДТВЕРДИТЬ':
            print("❌ Отменено")
            return
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        tables = ['notes', 'goals', 'achievements', 'activity_log', 
                 'quiz_results', 'schedule', 'daily_tips_read']
        
        for table in tables:
            cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
        
        cursor.execute('''
            UPDATE users 
            SET total_points = 0, current_level = 1, streak = 0 
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Данные пользователя {user_id} сброшены")


def main():
    import sys
    
    utils = BotUtils()
    
    if len(sys.argv) < 2:
        print("\n🛠️  Утилиты StudyBoost Bot")
        print("=" * 50)
        print("\nИспользование: python utils.py <команда> [параметры]")
        print("\nДоступные команды:")
        print("  stats              - Показать общую статистику")
        print("  backup             - Создать резервную копию БД")
        print("  export <user_id>   - Экспортировать данные пользователя")
        print("  clean [days]       - Очистить старые данные (по умолчанию 90 дней)")
        print("  reset <user_id>    - Сбросить данные пользователя")
        print()
        return
    
    command = sys.argv[1]
    
    if command == 'stats':
        utils.print_statistics()
    
    elif command == 'backup':
        utils.backup_database()
    
    elif command == 'export':
        if len(sys.argv) < 3:
            print("❌ Укажите user_id")
            return
        user_id = int(sys.argv[2])
        utils.export_user_data(user_id)
    
    elif command == 'clean':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        utils.clean_old_data(days)
    
    elif command == 'reset':
        if len(sys.argv) < 3:
            print("❌ Укажите user_id")
            return
        user_id = int(sys.argv[2])
        utils.reset_user_data(user_id)
    
    else:
        print(f"❌ Неизвестная команда: {command}")


if __name__ == '__main__':
    main()
