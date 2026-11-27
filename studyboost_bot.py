import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from database import Database
from gamification import GamificationSystem
from pdf_generator import PDFGenerator
from cloud_sync import CloudSync
from quiz_system import QuizSystem
from datetime import datetime, timedelta
import random
import secrets
from pathlib import Path
from telegram.helpers import escape_markdown
from telegram.ext import TypeHandler, ApplicationHandlerStop

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

(CHOOSING_CATEGORY, ADDING_NOTE, SETTING_GOAL, 
 ADDING_DEADLINE, CHOOSING_SUBJECT, QUIZ_ANSWER,
 ADDING_SCHEDULE, SETTING_REMINDER) = range(8)

class StudyBoostBot:
    def __init__(self, token: str, db_name: str = 'studyboost.db'):
        self.token = token
        self.db = Database(db_name)
        self.gamification = GamificationSystem(db_name)
        self.pdf_gen = PDFGenerator()
        self.cloud = CloudSync()
        self.quiz = QuizSystem()
        
        self.daily_tips = [
            "💡 Техника Pomodoro: 25 минут работы + 5 минут отдыха!",
            "🎯 Начните с самой сложной задачи утром - это даст заряд на весь день!",
            "📚 Повторяйте материал через 1 час, 1 день, 1 неделю и 1 месяц.",
            "🧘 Не забывайте делать перерывы - мозг тоже нуждается в отдыхе!",
            "✍️ Попробуйте записывать ключевые идеи своими словами.",
            "🎵 Классическая музыка или звуки природы помогают концентрации.",
            "💪 Учеба марафон, а не спринт. Регулярность важнее интенсивности!",
            "🌙 Качественный сон = лучшая память. Спите 7-8 часов!",
            "🍎 Питайте мозг: орехи, рыба, ягоды и темный шоколад.",
            "👥 Объясняйте материал другим - лучший способ его понять!"
        ]
    
    def get_main_menu_keyboard(self):
        keyboard = [
            ['📝 Добавить заметку', '📚 Мои заметки'],
            ['🎯 Цели и прогресс', '🎮 Викторины'],
            ['💡 Совет дня']
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        if context.user_data.pop('new_registration', False) or not self.db.user_exists(user_id):
            self.db.create_user(user_id, user.first_name)
            welcome_text = f"""Привет, {escape_markdown(user.first_name)}!

StudyBoost — твой учебный блокнот.

Сохраняй текст, фото и голосовые по предметам, собирай конспекты в PDF и проверяй знания в викторинах.

Начни с кнопки «Добавить заметку».
/help — команды, /privacy — хранение данных.
"""
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=self.get_main_menu_keyboard()
            )
            

        else:
            level = self.gamification.get_user_level(user_id)
            points = self.gamification.get_user_points(user_id)
            
            await update.message.reply_text(
                f"С возвращением, {user.first_name}! 🎓\n\n"
                f"🏆 Уровень: {level}\n"
                f"⭐ Баллы: {points}\n\n"
                f"Готов продолжить учебу?",
                reply_markup=self.get_main_menu_keyboard()
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
*StudyBoost — справка*

/start — главное меню
/stats — статистика
/goals — цели и прогресс
/goal Текст — добавить цель
/cancel — отменить текущий ввод
/privacy — хранение данных
/delete_me — удалить свои данные

Чтобы сохранить заметку, выбери предмет и отправь текст, фото или голос. Добавляй #теги в текст или подпись к фото.
Заметки и PDF доступны через «Мои заметки».
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        user_id = update.effective_user.id
        
        handlers = {
            '📝 Добавить заметку': self.add_note_start,
            '📚 Мои заметки': self.show_notes,
            '🎯 Цели и прогресс': self.show_goals,
            '🎮 Викторины': self.show_quizzes,
            '💡 Совет дня': self.daily_tip
        }
        
        handler = handlers.get(text)
        if handler:
            await handler(update, context)
    
    async def add_note_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📗 Математика", callback_data='cat_math')],
            [InlineKeyboardButton("⚗️ Физика", callback_data='cat_physics')],
            [InlineKeyboardButton("🧪 Химия", callback_data='cat_chemistry')],
            [InlineKeyboardButton("💻 Информатика", callback_data='cat_cs')],
            [InlineKeyboardButton("📚 История", callback_data='cat_history')],
            [InlineKeyboardButton("🌍 География", callback_data='cat_geography')],
            [InlineKeyboardButton("✏️ Другое", callback_data='cat_other')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 *Добавление заметки*\n\n"
            "Выбери предмет или категорию:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return CHOOSING_CATEGORY
    
    async def category_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        category_map = {
            'cat_math': ('Математика', '📗'),
            'cat_physics': ('Физика', '⚗️'),
            'cat_chemistry': ('Химия', '🧪'),
            'cat_cs': ('Информатика', '💻'),
            'cat_history': ('История', '📚'),
            'cat_geography': ('География', '🌍'),
            'cat_other': ('Другое', '✏️')
        }
        
        category, emoji = category_map.get(query.data, ('Другое', '✏️'))
        context.user_data['note_category'] = category
        
        await query.edit_message_text(
            f"{emoji} *{category}*\n\n"
            "Отлично! Теперь отправь:\n"
            "📝 Текст заметки\n"
            "📷 Фото с текстом\n"
            "🎤 Голосовое сообщение\n\n"
            "_Можешь добавить теги: #лекция #важное_",
            parse_mode='Markdown'
        )
        return ADDING_NOTE
    
    async def save_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        category = context.user_data.get('note_category', 'Другое')
        
        note_data = {
            'user_id': user_id,
            'category': category,
            'created_at': datetime.now()
        }
        
        if update.message.text:
            note_data['type'] = 'text'
            note_data['content'] = update.message.text
            tags = [word for word in update.message.text.split() if word.startswith('#')]
            note_data['tags'] = tags
        
        elif update.message.photo:
            note_data['type'] = 'photo'
            photo = update.message.photo[-1]
            note_data['file_id'] = photo.file_id
            note_data['content'] = update.message.caption or ''
            note_data['tags'] = [word for word in (update.message.caption or '').split() if word.startswith('#')]
        
        elif update.message.voice:
            note_data['type'] = 'voice'
            note_data['file_id'] = update.message.voice.file_id
            note_data['duration'] = update.message.voice.duration
            note_data['tags'] = []
        
        note_id = self.db.save_note(note_data)
        
        points = 5
        self.gamification.add_points(user_id, points, "Добавление заметки")
        
        achievements = self.gamification.check_achievements(user_id, self.db)
        achievement_text = ""
        if achievements:
            achievement_text = "\n🏆 " + "\n🏆 ".join(achievements)
        
        await update.message.reply_text(
            f"✅ Заметка сохранена!\n"
            f"📁 Категория: {category}\n"
            f"⭐ +{points} баллов{achievement_text}",
            reply_markup=self.get_main_menu_keyboard()
        )
        
        return ConversationHandler.END
    
    async def show_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        notes = self.db.get_user_notes(user_id)
        
        if not notes:
            await update.message.reply_text(
                "📭 У тебя пока нет заметок.\n"
                "Нажми '📝 Добавить заметку' чтобы создать первую!",
                reply_markup=self.get_main_menu_keyboard()
            )
            return
        
        categories = {}
        for note in notes:
            cat = note.get('category', 'Другое')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(note)
        
        keyboard = []
        for category, cat_notes in categories.items():
            count = len(cat_notes)
            keyboard.append([
                InlineKeyboardButton(
                    f"{category} ({count})",
                    callback_data=f'view_cat_{category}'
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("📄 Создать PDF конспект", callback_data='generate_pdf')
        ])

        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📚 *Твои заметки*\n\n"
            f"Всего заметок: {len(notes)}\n"
            f"Категорий: {len(categories)}\n\n"
            f"Выбери категорию:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def show_goals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        stats = self.db.get_user_stats(user_id)
        level = self.gamification.get_user_level(user_id)
        points = self.gamification.get_user_points(user_id)
        requirements = self.gamification.level_requirements
        floor = requirements[level]
        next_level_points = requirements.get(level + 1, floor)
        progress = 10 if next_level_points == floor else min(10, (points - floor) / (next_level_points - floor) * 10)
        
        progress_bar = "▰" * int(progress) + "▱" * (10 - int(progress))
        
        goals = self.db.get_user_goals(user_id)
        active_goals = [g for g in goals if not g.get('completed')]
        completed_today = [g for g in goals if g.get('completed_today')]
        
        goals_text = ""
        if active_goals:
            goals_text = "\n\n*Активные цели:*\n"
            for goal in active_goals[:5]:
                status = "✅" if goal.get('completed_today') else "⬜"
                goals_text += f"{status} {escape_markdown(goal['title'][:180])}\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить цель", callback_data='add_goal')],
            [InlineKeyboardButton("🏆 Достижения", callback_data='view_achievements')],
            [InlineKeyboardButton("📊 Детальная статистика", callback_data='detailed_stats')]
        ]
        for goal in active_goals[:5]:
            keyboard.append([InlineKeyboardButton(
                "Выполнено: " + goal['title'][:30],
                callback_data=f"complete_goal_{goal['goal_id']}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🎯 *Цели и прогресс*\n\n"
            f"🏆 Уровень: {level}\n"
            f"⭐ Баллы: {points}/{next_level_points}\n"
            f"{progress_bar}\n\n"
            f"📝 Заметок создано: {stats.get('total_notes', 0)}\n"
            f"✅ Целей выполнено сегодня: {stats.get('goals_completed_today', 0)}\n"
            f"🔥 Дней подряд: {stats.get('streak', 0)}"
            f"{goals_text}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def show_quizzes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📗 Математика", callback_data='quiz_math')],
            [InlineKeyboardButton("⚗️ Физика", callback_data='quiz_physics')],
            [InlineKeyboardButton("🧪 Химия", callback_data='quiz_chemistry')],
            [InlineKeyboardButton("💻 Информатика", callback_data='quiz_cs')],
            [InlineKeyboardButton("🎲 Случайная викторина", callback_data='quiz_random')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎮 *Викторины*\n\n"
            "Проверь свои знания и заработай баллы!\n"
            "Правильный ответ = +10 баллов ⭐\n\n"
            "Выбери предмет:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def start_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        subject_map = {
            'quiz_math': 'math',
            'quiz_physics': 'physics',
            'quiz_chemistry': 'chemistry',
            'quiz_cs': 'cs',
            'quiz_random': None
        }
        
        subject = subject_map.get(query.data)
        subject_name, questions = self.quiz.get_random_quiz(subject)
        
        context.user_data['quiz_subject'] = subject_name
        context.user_data['quiz_questions'] = questions
        context.user_data['quiz_current'] = 0
        context.user_data['quiz_score'] = 0
        context.user_data['quiz_session'] = secrets.token_hex(4)
        context.user_data['quiz_message'] = query.message.message_id
        context.user_data['quiz_awaiting_answer'] = True
        context.user_data['quiz_finished'] = False
        
        await self.ask_quiz_question(query, context)
        return QUIZ_ANSWER
    
    async def ask_quiz_question(self, query, context):
        questions = context.user_data['quiz_questions']
        current = context.user_data['quiz_current']
        
        if current >= len(questions):
            await self.finish_quiz(query, context)
            return ConversationHandler.END
        
        context.user_data['quiz_awaiting_answer'] = True
        question = questions[current]
        subject_name = self.quiz.get_subject_name(context.user_data['quiz_subject'])
        
        keyboard = []
        for i, option in enumerate(question['options']):
            keyboard.append([
                InlineKeyboardButton(option, callback_data=f"answer_{context.user_data['quiz_session']}_{current}_{i}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎮 *Викторина: {subject_name}*\n\n"
            f"Вопрос {current + 1}/{len(questions)}\n\n"
            f"{question['question']}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_quiz_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        parts = query.data.split('_')
        if (len(parts) != 4 or not parts[2].isdigit() or not parts[3].isdigit()
                or parts[1] != context.user_data.get('quiz_session')
                or int(parts[2]) != context.user_data.get('quiz_current')
                or query.message.message_id != context.user_data.get('quiz_message')
                or not context.user_data.get('quiz_awaiting_answer')
                or context.user_data.get('quiz_finished')):
            return QUIZ_ANSWER
        answer = int(parts[3])
        questions = context.user_data['quiz_questions']
        current = context.user_data['quiz_current']
        question = questions[current]
        
        if not 0 <= answer < len(question['options']):
            return QUIZ_ANSWER
        context.user_data['quiz_awaiting_answer'] = False
        is_correct, explanation = self.quiz.check_answer(question, answer)
        
        if is_correct:
            context.user_data['quiz_score'] += 1
            result_text = "✅ *Правильно!*"
        else:
            result_text = "❌ *Неправильно*"
            correct_answer = question['options'][question['correct']]
            result_text += f"\n\nПравильный ответ: {correct_answer}"
        
        result_text += f"\n\n💡 {explanation}"
        
        context.user_data['quiz_current'] += 1
        
        keyboard = [[InlineKeyboardButton("Следующий вопрос ➡️", callback_data=f"next_question_{context.user_data['quiz_session']}_{context.user_data['quiz_current']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            result_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return QUIZ_ANSWER
    
    async def next_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        expected = f"next_question_{context.user_data.get('quiz_session')}_{context.user_data.get('quiz_current')}"
        if (query.data != expected
                or query.message.message_id != context.user_data.get('quiz_message')
                or context.user_data.get('quiz_awaiting_answer')
                or context.user_data.get('quiz_finished')):
            return QUIZ_ANSWER
        questions = context.user_data['quiz_questions']
        current = context.user_data['quiz_current']
        if current >= len(questions):
            await self.finish_quiz(query, context)
            return ConversationHandler.END
        await self.ask_quiz_question(query, context)
        return QUIZ_ANSWER
    
    async def finish_quiz(self, query, context):
        if context.user_data.get('quiz_finished'):
            return
        context.user_data['quiz_finished'] = True
        user_id = query.from_user.id
        score = context.user_data['quiz_score']
        total = len(context.user_data['quiz_questions'])
        subject = context.user_data['quiz_subject']
        
        percentage = (score / total) * 100
        points = score * 10
        
        self.db.record_quiz_result(user_id, subject, score, total)
        self.gamification.add_points(user_id, points, f"Викторина по {subject}")
        
        if percentage == 100:
            emoji = "🏆"
            message = "Идеально! Ты гений!"
        elif percentage >= 80:
            emoji = "🌟"
            message = "Отлично! Так держать!"
        elif percentage >= 60:
            emoji = "👍"
            message = "Хорошо! Есть куда расти!"
        else:
            emoji = "📚"
            message = "Повтори материал и попробуй снова!"
        
        subject_name = self.quiz.get_subject_name(subject)
        
        await query.edit_message_text(
            f"{emoji} *Викторина завершена!*\n\n"
            f"Предмет: {subject_name}\n"
            f"Результат: {score}/{total} ({percentage:.0f}%)\n"
            f"Баллов заработано: +{points} ⭐\n\n"
            f"{message}",
            parse_mode='Markdown'
        )
    
    async def daily_tip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        tip_index = datetime.now().day % len(self.daily_tips)
        tip = self.daily_tips[tip_index]
        
        if not self.db.tip_read_today(user_id):
            self.gamification.add_points(user_id, 2, "Чтение совета дня")
            self.db.mark_tip_read(user_id)
            bonus_text = "\n\n⭐ +2 балла за мотивацию!"
        else:
            bonus_text = ""
        
        await update.message.reply_text(
            f"💡 *Совет дня*\n\n{tip}{bonus_text}",
            parse_mode='Markdown',
            reply_markup=self.get_main_menu_keyboard()
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        stats = self.db.get_detailed_stats(user_id)
        
        await update.effective_message.reply_text(
            f"📊 *Твоя статистика*\n\n"
            f"🏆 Уровень: {stats['level']}\n"
            f"⭐ Всего баллов: {stats['total_points']}\n\n"
            f"📝 Заметок создано: {stats['total_notes']}\n"
            f"├ Текстовых: {stats['text_notes']}\n"
            f"├ С фото: {stats['photo_notes']}\n"
            f"└ Голосовых: {stats['voice_notes']}\n\n"
            f"🎯 Целей выполнено: {stats['completed_goals']}\n"
            f"🔥 Текущая серия: {stats['current_streak']} дней\n"
            f"🏅 Лучшая серия: {stats['best_streak']} дней\n\n"
            f"🎮 Викторин пройдено: {stats['quizzes_completed']}\n"
            f"✅ Правильных ответов: {stats['correct_answers']}/{stats['total_answers']}\n\n"
            f"📅 С нами с: {stats['join_date'].strftime('%d.%m.%Y')}",
            parse_mode='Markdown'
        )
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        
        if data == 'add_goal':
            await query.answer()
            await query.message.reply_text("Отправь /goal и текст цели. Например: /goal Повторить квадратные уравнения")
            return
        if data.startswith('complete_goal_'):
            await query.answer()
            try:
                goal_id = int(data[len('complete_goal_'):])
            except ValueError:
                return
            completed = self.db.complete_goal(goal_id, query.from_user.id)
            await query.message.reply_text("Цель выполнена." if completed else "Цель уже выполнена или недоступна.")
            return
        if data.startswith('delete_confirm_'):
            nonce = context.user_data.pop('delete_nonce', None)
            if not nonce or data != f'delete_confirm_{nonce}':
                await query.answer("Подтверждение устарело.", show_alert=True)
                return
            self.db.delete_user_data(query.from_user.id)
            context.user_data.clear()
            await query.answer()
            await query.edit_message_text("Твои данные удалены из базы бота. Чтобы начать заново, отправь /start.")
            return ConversationHandler.END
        if data.startswith('view_cat_'):
            await query.answer()
            notes = self.db.get_user_notes(query.from_user.id, data[len('view_cat_'):])
            if not notes:
                await query.message.reply_text("В этой категории пока нет заметок.")
            for note in notes[:20]:
                if note['note_type'] == 'photo' and note.get('file_id'):
                    await query.message.reply_photo(note['file_id'], caption=(note.get('content') or '')[:1024])
                elif note['note_type'] == 'voice' and note.get('file_id'):
                    await query.message.reply_voice(note['file_id'])
                else:
                    content = note.get('content') or '(пустая заметка)'
                    for offset in range(0, len(content), 4000):
                        await query.message.reply_text(content[offset:offset + 4000])
            if len(notes) > 20:
                await query.message.reply_text("Показаны последние 20 заметок. Полный конспект доступен в PDF.")
            return
        if data == 'generate_pdf':
            return await self.generate_pdf_callback(update, context)
        if data == 'view_achievements':
            return await self.view_achievements(update, context)
        if data == 'detailed_stats':
            return await self.stats_command(update, context)
        if data.startswith(('cat_', 'quiz_', 'answer_', 'next_question')):
            await query.answer("Эта кнопка устарела. Начни заново из меню.", show_alert=True)
            return
        await query.answer("Эта функция пока в разработке.", show_alert=True)

    async def generate_pdf_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer("Генерация PDF...")
        
        user_id = query.from_user.id
        username = query.from_user.first_name
        notes = self.db.get_user_notes(user_id)
        
        try:
            pdf_path = self.pdf_gen.create_notes_pdf(user_id, notes, username=username)
        except RuntimeError:
            await query.message.reply_text("Для PDF нужен шрифт с кириллицей. Попроси владельца установить DejaVu Sans или задать STUDYBOOST_FONT.")
            return
        
        try:
            with open(pdf_path, 'rb') as document:
                await query.message.reply_document(
                    document=document, caption="📄 Твой конспект готов!")
        finally:
            Path(pdf_path).unlink(missing_ok=True)
    
    async def view_achievements(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        achievements = self.gamification.get_user_achievements(user_id)
        available = self.gamification.get_available_achievements(user_id)
        
        text = "🏆 *Твои достижения*\n\n"
        
        if achievements:
            text += "*Получено:*\n"
            for ach in achievements[:10]:
                text += f"{ach['emoji']} {ach['name']} - {ach['description']}\n"
        
        text += f"\n\n*Доступно для получения:* {len(available)}"
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    async def add_goal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        title = ' '.join(context.args).strip()
        if not title or len(title) > 200:
            await update.effective_message.reply_text("Отправь /goal и название цели длиной до 200 символов.")
            return
        self.db.add_goal(update.effective_user.id, title)
        await update.effective_message.reply_text("Цель добавлена. Посмотреть цели: /goals")

    async def privacy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text(
            "Бот хранит Telegram ID, имя, username, заметки, ссылки на вложения, цели и статистику "
            "в SQLite на сервере владельца. Данные не зашифрованы на уровне приложения; "
            "владелец сервера имеет к ним доступ. Не отправляй пароли и другие секреты. "
            "Облачной синхронизации нет. Удалить записи из базы: /delete_me. "
            "Удаление не затрагивает переписку в Telegram и резервные копии владельца.")

    async def delete_me_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        nonce = secrets.token_hex(8)
        context.user_data['delete_nonce'] = nonce
        await update.effective_message.reply_text(
            "Удалить все твои заметки, цели, баллы и профиль из базы бота? Это действие нельзя отменить. "
            "Переписка в Telegram и резервные копии не удаляются.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                "Удалить мои данные", callback_data=f"delete_confirm_{nonce}")]]))

    async def guard_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # A study notebook is private: never display notes in group chats.
        if not update.effective_chat or update.effective_chat.type != 'private' or not update.effective_user:
            raise ApplicationHandlerStop
        user = update.effective_user
        if not self.db.user_exists(user.id):
            self.db.create_user(user.id, user.first_name, user.username)
            context.user_data['new_registration'] = True
            self.gamification.add_points(user.id, 10, "Регистрация")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "Действие отменено.", reply_markup=self.get_main_menu_keyboard())
        return ConversationHandler.END

    async def on_error(self, update, context):
        logger.error("Update failed (%s)", type(context.error).__name__)
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("Не удалось выполнить действие. Попробуй /cancel и начни заново.")

    def build_application(self):
        application = Application.builder().token(self.token).concurrent_updates(False).build()
        
        note_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^📝 Добавить заметку$'), 
                                        self.add_note_start)],
            states={
                CHOOSING_CATEGORY: [CallbackQueryHandler(self.category_selected, pattern='^cat_')],
                ADDING_NOTE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_note),
                    MessageHandler(filters.PHOTO, self.save_note),
                    MessageHandler(filters.VOICE, self.save_note)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel),
                CallbackQueryHandler(self.callback_handler, pattern='^delete_confirm_')
            ],
            allow_reentry=True
        )
        
        quiz_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_quiz, pattern='^quiz_')],
            states={
                QUIZ_ANSWER: [
                    CallbackQueryHandler(self.handle_quiz_answer, pattern=r'^answer_[0-9a-f]{8}_\d+_\d+$'),
                    CallbackQueryHandler(self.next_question, pattern=r'^next_question_[0-9a-f]{8}_\d+$')
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel),
                CallbackQueryHandler(self.callback_handler, pattern='^delete_confirm_')
            ],
            allow_reentry=True
        )
        
        application.add_handler(TypeHandler(Update, self.guard_update), group=-1)
        application.add_error_handler(self.on_error)
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("goals", self.show_goals))
        application.add_handler(CommandHandler("goal", self.add_goal_command))
        application.add_handler(CommandHandler("privacy", self.privacy_command))
        application.add_handler(CommandHandler("delete_me", self.delete_me_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(note_handler)
        application.add_handler(quiz_handler)
        application.add_handler(CommandHandler('cancel', self.cancel))
        application.add_handler(CallbackQueryHandler(self.callback_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                              self.button_handler))
        
        return application

    def run(self):
        application = self.build_application()
        logger.info("StudyBoost запущен!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    from run import main
    raise SystemExit(main())
