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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(CHOOSING_CATEGORY, ADDING_NOTE, SETTING_GOAL, 
 ADDING_DEADLINE, CHOOSING_SUBJECT, QUIZ_ANSWER,
 ADDING_SCHEDULE, SETTING_REMINDER) = range(8)

class StudyBoostBot:
    def __init__(self, token: str):
        self.token = token
        self.db = Database()
        self.gamification = GamificationSystem()
        self.pdf_gen = PDFGenerator()
        self.cloud = CloudSync()
        self.quiz = QuizSystem()
        
        self.daily_tips = [
            "💡 Техника Pomodoro: 25 минут работы + 5 минут отдыха!",
            "🎯 Начните с самой сложной задачи утром - это даст заряд на весь день!",
            "📚 Повторяйте материал через 1 час, 1 день, 1 неделю и 1 месяц.",
            "🧘 Не забывайте делать перерывы - мозг тоже нуждается в отдыхе!",
            "✍️ Записывайте от руки - это улучшает запоминание на 34%!",
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
            ['🤝 Делиться', '⚙️ Настройки'],
            ['💡 Совет дня']
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        if not self.db.user_exists(user_id):
            self.db.create_user(user_id, user.first_name)
            welcome_text = f"""
🎓 *Добро пожаловать в StudyBoost, {user.first_name}!* 🚀

Я помогу тебе организовать учебу, достигать целей и оставаться мотивированным!

*Что я умею:*
📝 Сохранять заметки (текст, фото, голос)
🗂 Организовывать по предметам с тегами
📄 Генерировать PDF конспекты
🎯 Отслеживать цели и дедлайны
🏆 Система баллов и достижений
🎮 Викторины для проверки знаний
💡 Ежедневные советы
☁️ Синхронизация с облаком

Используй кнопки меню или команды:
/help - справка
/stats - статистика

*Начни свой путь к успеху прямо сейчас!* 💪
"""
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=self.get_main_menu_keyboard()
            )
            
            self.gamification.add_points(user_id, 10, "Регистрация")
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
📖 *Справка по StudyBoost*

*Основные команды:*
/start - Главное меню
/stats - Твоя статистика
/goals - Управление целями
/schedule - Расписание занятий

*Работа с заметками:*
• Используй кнопку "Добавить заметку"
• Отправь текст, фото или голосовое сообщение
• Добавь теги: #математика #лекция
• Сохрани и заработай баллы!

*Категории и теги:*
Используй хештеги для организации:
#математика, #физика, #история и т.д.

*Цели и мотивация:*
• Ставь дневные/недельные цели
• Получай напоминания о дедлайнах
• Зарабатывай баллы за достижения

*Система уровней:*
🥉 1-100 баллов: Новичок
🥈 101-500: Студент
🥇 501-1000: Отличник
💎 1000+: Гений

Нужна помощь? Пиши @support
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
            '🤝 Делиться': self.share_menu,
            '⚙️ Настройки': self.settings_menu,
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
        keyboard.append([
            InlineKeyboardButton("☁️ Синхронизировать", callback_data='sync_cloud')
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
        next_level_points = (level + 1) * 100
        progress = (points % 100) / 100 * 10
        
        progress_bar = "▰" * int(progress) + "▱" * (10 - int(progress))
        
        goals = self.db.get_user_goals(user_id)
        active_goals = [g for g in goals if not g.get('completed')]
        completed_today = [g for g in goals if g.get('completed_today')]
        
        goals_text = ""
        if active_goals:
            goals_text = "\n\n*Активные цели:*\n"
            for goal in active_goals[:5]:
                status = "✅" if goal.get('completed_today') else "⬜"
                goals_text += f"{status} {goal['title']}\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить цель", callback_data='add_goal')],
            [InlineKeyboardButton("📅 Дедлайны", callback_data='view_deadlines')],
            [InlineKeyboardButton("🏆 Достижения", callback_data='view_achievements')],
            [InlineKeyboardButton("📊 Детальная статистика", callback_data='detailed_stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🎯 *Цели и прогресс*\n\n"
            f"🏆 Уровень: {level}\n"
            f"⭐ Баллы: {points}/{next_level_points}\n"
            f"{progress_bar}\n\n"
            f"📝 Заметок создано: {stats.get('total_notes', 0)}\n"
            f"✅ Целей выполнено сегодня: {len(completed_today)}\n"
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
        
        await self.ask_quiz_question(query, context)
        return QUIZ_ANSWER
    
    async def ask_quiz_question(self, query, context):
        questions = context.user_data['quiz_questions']
        current = context.user_data['quiz_current']
        
        if current >= len(questions):
            await self.finish_quiz(query, context)
            return ConversationHandler.END
        
        question = questions[current]
        subject_name = self.quiz.get_subject_name(context.user_data['quiz_subject'])
        
        keyboard = []
        for i, option in enumerate(question['options']):
            keyboard.append([
                InlineKeyboardButton(option, callback_data=f'answer_{i}')
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
        
        answer = int(query.data.split('_')[1])
        questions = context.user_data['quiz_questions']
        current = context.user_data['quiz_current']
        question = questions[current]
        
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
        
        keyboard = [[InlineKeyboardButton("Следующий вопрос ➡️", callback_data='next_question')]]
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
        
        questions = context.user_data['quiz_questions']
        current = context.user_data['quiz_current']
        
        if current >= len(questions):
            await self.finish_quiz(query, context)
            return ConversationHandler.END
        
        await self.ask_quiz_question(query, context)
        return QUIZ_ANSWER
    
    async def finish_quiz(self, query, context):
        user_id = query.from_user.id
        score = context.user_data['quiz_score']
        total = len(context.user_data['quiz_questions'])
        subject = context.user_data['quiz_subject']
        
        percentage = (score / total) * 100
        points = score * 10
        
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
    
    async def share_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📤 Поделиться заметкой", callback_data='share_note')],
            [InlineKeyboardButton("👥 Мои группы", callback_data='my_groups')],
            [InlineKeyboardButton("➕ Создать группу", callback_data='create_group')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤝 *Обмен заметками*\n\n"
            "Делись конспектами с друзьями и одногруппниками!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        settings = self.db.get_user_settings(user_id)
        
        notifications = "🔔 Вкл" if settings.get('notifications', True) else "🔕 Выкл"
        cloud_sync = "☁️ Вкл" if settings.get('cloud_sync', False) else "❌ Выкл"
        
        keyboard = [
            [InlineKeyboardButton(f"Уведомления: {notifications}", 
                                callback_data='toggle_notifications')],
            [InlineKeyboardButton(f"Облачная синхронизация: {cloud_sync}", 
                                callback_data='toggle_cloud')],
            [InlineKeyboardButton("📅 Настроить расписание", 
                                callback_data='setup_schedule')],
            [InlineKeyboardButton("🔗 Подключить облако", 
                                callback_data='connect_cloud')],
            [InlineKeyboardButton("🗑 Очистить все данные", 
                                callback_data='clear_data')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ *Настройки*\n\n"
            "Настрой бота под себя:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        stats = self.db.get_detailed_stats(user_id)
        
        await update.message.reply_text(
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
        
        if data.startswith('cat_'):
            return await self.category_selected(update, context)
        elif data.startswith('quiz_'):
            return await self.start_quiz(update, context)
        elif data.startswith('answer_'):
            return await self.handle_quiz_answer(update, context)
        elif data == 'next_question':
            return await self.next_question(update, context)
        elif data == 'generate_pdf':
            return await self.generate_pdf_callback(update, context)
        elif data == 'sync_cloud':
            return await self.sync_cloud_callback(update, context)
        elif data == 'view_achievements':
            return await self.view_achievements(update, context)
        
        await query.answer()
    
    async def generate_pdf_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer("Генерация PDF...")
        
        user_id = query.from_user.id
        username = query.from_user.first_name
        notes = self.db.get_user_notes(user_id)
        
        pdf_path = self.pdf_gen.create_notes_pdf(user_id, notes, username=username)
        
        await query.message.reply_document(
            document=open(pdf_path, 'rb'),
            caption="📄 Твой конспект готов!\n\n"
                   "Можешь сохранить его или распечатать 📚"
        )
    
    async def sync_cloud_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.cloud.is_connected(user_id):
            await query.answer("Сначала подключи облако в настройках!", show_alert=True)
            return
        
        await query.answer("Синхронизация...")
        
        notes = self.db.get_user_notes(user_id)
        notes_data = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'notes': notes
        }
        
        success = self.cloud.sync_notes(user_id, notes_data)
        
        if success:
            await query.message.reply_text("✅ Заметки синхронизированы с облаком!")
        else:
            await query.message.reply_text("❌ Ошибка синхронизации. Попробуй позже.")
    
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
    
    def run(self):
        application = Application.builder().token(self.token).build()
        
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
            fallbacks=[CommandHandler('cancel', self.start)]
        )
        
        quiz_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_quiz, pattern='^quiz_')],
            states={
                QUIZ_ANSWER: [
                    CallbackQueryHandler(self.handle_quiz_answer, pattern='^answer_'),
                    CallbackQueryHandler(self.next_question, pattern='^next_question$')
                ]
            },
            fallbacks=[CommandHandler('cancel', self.start)]
        )
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(note_handler)
        application.add_handler(quiz_handler)
        application.add_handler(CallbackQueryHandler(self.callback_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                              self.button_handler))
        
        logger.info("StudyBoost запущен!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import os
    
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        try:
            with open('config.json', 'r') as f:
                import json
                config = json.load(f)
                TOKEN = config.get('bot_token', 'YOUR_BOT_TOKEN_HERE')
        except:
            TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Ошибка: Токен бота не найден!")
        print("📝 Установите переменную окружения BOT_TOKEN")
        print("   или укажите токен в config.json")
        exit(1)
    
    bot = StudyBoostBot(TOKEN)
    bot.run()
