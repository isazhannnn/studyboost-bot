from studyboost_bot import StudyBoostBot
from database import Database
from gamification import GamificationSystem

def example_usage():
    
    print("=== Примеры использования StudyBoost Bot ===\n")
    
    print("1. Работа с базой данных:")
    db = Database()
    
    user_id = 12345
    db.create_user(user_id, "Иван")
    
    note_data = {
        'user_id': user_id,
        'category': 'Математика',
        'type': 'text',
        'content': 'Формула квадратного уравнения: ax² + bx + c = 0',
        'tags': ['#математика', '#формулы']
    }
    db.save_note(note_data)
    
    print(f"✅ Пользователь создан, заметка сохранена")
    
    print("\n2. Работа с геймификацией:")
    gamification = GamificationSystem()
    
    gamification.add_points(user_id, 10, "Регистрация")
    points = gamification.get_user_points(user_id)
    level = gamification.get_user_level(user_id)
    
    print(f"⭐ Баллы: {points}")
    print(f"🏆 Уровень: {level}")
    
    print("\n3. Получение статистики:")
    stats = db.get_detailed_stats(user_id)
    
    print(f"📊 Статистика:")
    print(f"  - Всего заметок: {stats['total_notes']}")
    print(f"  - Уровень: {stats['level']}")
    print(f"  - Баллы: {stats['total_points']}")
    
    print("\n4. Проверка достижений:")
    achievements = gamification.check_achievements(user_id, db)
    
    if achievements:
        print("🏆 Получены достижения:")
        for ach in achievements:
            print(f"  - {ach}")
    
    print("\n5. Добавление цели:")
    from datetime import datetime, timedelta
    
    deadline = datetime.now() + timedelta(days=7)
    goal_id = db.add_goal(
        user_id,
        "Подготовиться к экзамену по математике",
        "Повторить главы 1-5",
        "weekly",
        deadline
    )
    print(f"🎯 Цель добавлена с ID: {goal_id}")
    
    print("\n6. Получение заметок:")
    notes = db.get_user_notes(user_id)
    print(f"📚 Найдено заметок: {len(notes)}")
    
    for note in notes:
        print(f"\n  Категория: {note['category']}")
        print(f"  Тип: {note['note_type']}")
        print(f"  Содержание: {note['content'][:50]}...")
    
    print("\n=== Примеры завершены ===")


def quiz_example():
    from quiz_system import QuizSystem
    
    print("\n=== Пример работы с викторинами ===\n")
    
    quiz = QuizSystem()
    
    subject, questions = quiz.get_random_quiz('math')
    print(f"📗 Предмет: {quiz.get_subject_name(subject)}")
    print(f"❓ Вопросов: {len(questions)}\n")
    
    for i, q in enumerate(questions[:2], 1):
        print(f"Вопрос {i}: {q['question']}")
        for j, opt in enumerate(q['options']):
            print(f"  {j+1}) {opt}")
        print(f"✅ Правильный ответ: {q['options'][q['correct']]}")
        print(f"💡 {q['explanation']}\n")


def pdf_example():
    from pdf_generator import PDFGenerator
    from database import Database
    
    print("\n=== Пример генерации PDF ===\n")
    
    db = Database()
    pdf_gen = PDFGenerator()
    
    user_id = 12345
    notes = db.get_user_notes(user_id)
    
    if notes:
        pdf_path = pdf_gen.create_notes_pdf(
            user_id,
            notes,
            category="Математика",
            username="Иван"
        )
        print(f"📄 PDF создан: {pdf_path}")
    else:
        print("❌ Нет заметок для создания PDF")


if __name__ == '__main__':
    
    print("StudyBoost Bot - Примеры использования\n")
    print("Выберите пример:")
    print("1 - Основной функционал")
    print("2 - Викторины")
    print("3 - Генерация PDF")
    print("4 - Все примеры")
    
    choice = input("\nВаш выбор (1-4): ")
    
    if choice == '1':
        example_usage()
    elif choice == '2':
        quiz_example()
    elif choice == '3':
        pdf_example()
    elif choice == '4':
        example_usage()
        quiz_example()
        pdf_example()
    else:
        print("Неверный выбор!")
