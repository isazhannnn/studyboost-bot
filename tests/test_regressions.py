import asyncio
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from cloud_sync import CloudSync
from database import Database
from gamification import GamificationSystem
from pdf_generator import PDFGenerator
import run
from studyboost_bot import StudyBoostBot, QUIZ_ANSWER
from telegram.ext import ApplicationHandlerStop, ConversationHandler


# Deliberately invalid for real authentication, assembled to avoid secret detectors.
TEST_TOKEN = '123456789:' + 'x' * 35


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'notes.db')
        self.db = Database(self.path)
        self.db.create_user(1, 'Student')
        self.game = GamificationSystem(self.path)

    def test_note_save_does_not_lock_activity_update(self):
        self.db.save_note(dict(user_id=1, category='Math', type='text',
                               content='2 < 3', tags=['#math']))
        self.assertEqual(len(self.db.get_user_notes(1)), 1)
        self.assertEqual(self.db.get_user_stats(1)['streak'], 1)

    def test_achievement_awards_once_without_nested_write_lock(self):
        self.db.save_note(dict(user_id=1, category='Math', type='text', content='A'))
        self.assertEqual(len(self.game.check_achievements(1, self.db)), 1)
        points = self.game.get_user_points(1)
        self.assertEqual(points, 10)
        self.assertEqual(self.game.check_achievements(1, self.db), [])
        self.assertEqual(self.game.get_user_points(1), points)

    def test_registration_is_idempotent(self):
        self.game.add_points(1, 100)
        self.db.create_user(1, 'Student')
        self.assertEqual(self.game.get_user_points(1), 100)

    def test_notes_are_scoped_to_owner(self):
        self.db.create_user(2, 'Other')
        self.db.save_note(dict(user_id=2, category='Math', type='text', content='Private'))
        self.assertEqual(self.db.get_user_notes(1, 'Math'), [])

    def test_quiz_results_appear_in_statistics(self):
        self.db.record_quiz_result(1, 'math', 2, 3)
        stats = self.db.get_detailed_stats(1)
        self.assertEqual((stats['quizzes_completed'], stats['correct_answers'],
                          stats['total_answers']), (1, 2, 3))

    def test_goal_can_only_be_completed_by_its_owner_once(self):
        self.db.create_user(2, 'Other')
        goal = self.db.add_goal(1, 'Read chapter 2')
        self.assertFalse(self.db.complete_goal(goal, 2))
        self.assertTrue(self.db.complete_goal(goal, 1))
        self.assertFalse(self.db.complete_goal(goal, 1))

    def test_delete_user_data_keeps_other_users_data(self):
        self.db.create_user(2, 'Other')
        for owner in (1, 2):
            self.db.save_note(dict(user_id=owner, category='Math', type='text', content='Note'))
            self.db.add_goal(owner, 'Study')
            self.db.record_quiz_result(owner, 'math', 1, 2)
            self.game.add_points(owner, 5)
            self.db.mark_tip_read(owner)
        self.db.delete_user_data(1)
        self.assertFalse(self.db.user_exists(1))
        self.assertEqual(self.db.get_user_notes(1), [])
        self.assertEqual(self.db.get_user_goals(1), [])
        self.assertTrue(self.db.user_exists(2))
        self.assertEqual(len(self.db.get_user_notes(2)), 1)
        self.assertEqual(self.db.get_detailed_stats(2)['quizzes_completed'], 1)


class ConfigTests(unittest.TestCase):
    def test_environment_only_startup_config(self):
        with TemporaryDirectory() as folder, patch.object(run, 'BASE_DIR', Path(folder)):
            with patch.dict(os.environ, {'BOT_TOKEN': TEST_TOKEN, 'STUDYBOOST_DB': 'custom.db'}):
                config = run.load_config()
        self.assertTrue(run.validate_config(config))
        self.assertEqual(config['database_path'], 'custom.db')

    def test_environment_overrides_legacy_local_config(self):
        with TemporaryDirectory() as folder, patch.object(run, 'BASE_DIR', Path(folder)):
            Path(folder, 'config.json').write_text(json.dumps({'bot_token': 'old'}))
            with patch.dict(os.environ, {'BOT_TOKEN': TEST_TOKEN}):
                self.assertEqual(run.load_config()['bot_token'], TEST_TOKEN)

    def test_placeholder_and_empty_token_rejected(self):
        for token in ('', 'YOUR_BOT_TOKEN_HERE', 'invalid'):
            self.assertFalse(run.validate_config({'bot_token': token}))

    def test_cloud_never_claims_upload_or_saves_credentials(self):
        with TemporaryDirectory() as folder, patch('os.getcwd', return_value=folder):
            cloud = CloudSync()
            self.assertFalse(cloud.connect_dropbox(1, 'dummy'))
            self.assertFalse(cloud.connect_google_drive(1, 'dummy'))
            self.assertFalse(cloud.sync_notes(1, {'private': 'note'}))
            self.assertIsNone(cloud.upload_to_dropbox(1, 'unused'))
            self.assertEqual(list(Path(folder).iterdir()), [])


class PDFTests(unittest.TestCase):
    def test_export_escapes_markup_and_does_not_use_category_as_path(self):
        with TemporaryDirectory() as folder:
            generator = PDFGenerator()
            if not generator.russian_font:
                self.skipTest('No Cyrillic font installed')
            generator.output_dir = folder
            category = '../outside'
            notes = [dict(category=category, created_at='2026-11-27 10:00:00',
                          tags=['#<img>'], note_type='text', content='<img> & текст')]
            output = Path(generator.create_notes_pdf(1, notes, category, '<img> Student'))
            self.assertEqual(output.parent.resolve(), Path(folder).resolve())
            self.assertTrue(output.read_bytes().startswith(b'%PDF-'))

    def test_missing_font_reports_configuration_problem(self):
        generator = PDFGenerator()
        generator.russian_font = None
        with self.assertRaises(RuntimeError):
            generator.create_notes_pdf(1, [])


class BotTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bot = StudyBoostBot(TEST_TOKEN, str(Path(self.temp.name) / 'bot.db'))
        self.bot.db.create_user(1, 'Student')
        self.context = SimpleNamespace(user_data={})
        self.query = SimpleNamespace(
            data='quiz_math', from_user=SimpleNamespace(id=1, first_name='Student'),
            message=SimpleNamespace(message_id=42, reply_text=AsyncMock(),
                                    reply_photo=AsyncMock(), reply_voice=AsyncMock()),
            answer=AsyncMock(), edit_message_text=AsyncMock())
        self.update = SimpleNamespace(callback_query=self.query)

    async def test_duplicate_and_stale_quiz_answers_are_ignored(self):
        await self.bot.start_quiz(self.update, self.context)
        data = self.context.user_data
        correct = data['quiz_questions'][0]['correct']
        self.query.data = f"answer_{data['quiz_session']}_0_{correct}"
        await self.bot.handle_quiz_answer(self.update, self.context)
        await self.bot.handle_quiz_answer(self.update, self.context)
        self.assertEqual((data['quiz_current'], data['quiz_score']), (1, 1))
        self.query.data = f"next_question_{data['quiz_session']}_1"
        await self.bot.next_question(self.update, self.context)
        self.query.data = f"answer_{data['quiz_session']}_0_{correct}"
        await self.bot.handle_quiz_answer(self.update, self.context)
        self.assertEqual(data['quiz_current'], 1)

    async def test_quiz_from_another_message_cannot_advance(self):
        await self.bot.start_quiz(self.update, self.context)
        data = self.context.user_data
        self.query.message.message_id = 99
        self.query.data = f"answer_{data['quiz_session']}_0_0"
        await self.bot.handle_quiz_answer(self.update, self.context)
        self.assertEqual(data['quiz_current'], 0)

    async def test_finish_awards_and_records_only_once(self):
        await self.bot.start_quiz(self.update, self.context)
        data = self.context.user_data
        total = len(data['quiz_questions'])
        data['quiz_score'] = total
        await self.bot.finish_quiz(self.query, self.context)
        await self.bot.finish_quiz(self.query, self.context)
        self.assertEqual(self.bot.gamification.get_user_points(1), total * 10)
        self.assertEqual(self.bot.db.get_detailed_stats(1)['quizzes_completed'], 1)

    async def test_stale_callback_after_restart_is_safe(self):
        self.query.data = 'answer_old'
        await self.bot.callback_handler(self.update, self.context)
        self.query.answer.assert_awaited_once()
        self.assertEqual(self.context.user_data, {})

    async def test_delete_requires_current_confirmation_nonce(self):
        self.query.data = 'delete_confirm_stale'
        await self.bot.callback_handler(self.update, self.context)
        self.assertTrue(self.bot.db.user_exists(1))
        self.context.user_data['delete_nonce'] = 'current'
        self.query.data = 'delete_confirm_current'
        result = await self.bot.callback_handler(self.update, self.context)
        self.assertEqual(result, ConversationHandler.END)
        self.assertFalse(self.bot.db.user_exists(1))
        self.assertEqual(self.context.user_data, {})

    async def test_generated_pdf_is_closed_and_deleted_after_send_failure(self):
        pdf = Path(self.temp.name) / 'export.pdf'
        pdf.write_bytes(b'%PDF-fixture')
        self.query.message.reply_document = AsyncMock(side_effect=RuntimeError('send failed'))
        with patch.object(self.bot.pdf_gen, 'create_notes_pdf', return_value=str(pdf)):
            with self.assertRaises(RuntimeError):
                await self.bot.generate_pdf_callback(self.update, self.context)
        self.assertFalse(pdf.exists())

    async def test_group_updates_stop_before_private_data_access(self):
        update = SimpleNamespace(effective_chat=SimpleNamespace(type='supergroup'),
                                 effective_user=SimpleNamespace(id=1))
        with self.assertRaises(ApplicationHandlerStop):
            await self.bot.guard_update(update, self.context)

    async def test_cancel_ends_conversation_and_clears_quiz(self):
        self.context.user_data['quiz_questions'] = ['old']
        update = SimpleNamespace(effective_message=SimpleNamespace(reply_text=AsyncMock()))
        result = await self.bot.cancel(update, self.context)
        self.assertEqual(result, ConversationHandler.END)
        self.assertEqual(self.context.user_data, {})

    async def test_category_callback_does_not_leak_other_users_notes(self):
        self.bot.db.create_user(2, 'Other')
        for user_id, text in ((1, 'Mine'), (2, 'Private')):
            self.bot.db.save_note(dict(user_id=user_id, category='Math',
                                       type='text', content=text))
        self.query.data = 'view_cat_Math'
        await self.bot.callback_handler(self.update, self.context)
        self.query.message.reply_text.assert_awaited_once_with('Mine')

    async def test_application_builds_without_contacting_telegram(self):
        application = self.bot.build_application()
        self.assertIn(-1, application.handlers)
        conversations = [handler for handler in application.handlers[0]
                         if isinstance(handler, ConversationHandler)]
        self.assertEqual(len(conversations), 2)
        self.assertEqual(application.concurrent_updates, 1)


if __name__ == '__main__':
    unittest.main()
