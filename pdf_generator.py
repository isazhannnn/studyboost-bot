"""
Модуль для генерации PDF конспектов из заметок
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from typing import List, Dict
import os
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape


class PDFGenerator:
    def __init__(self):
        self.output_dir = 'pdf_exports'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.russian_font = None
        candidates = [
            os.getenv('STUDYBOOST_FONT', ''),
            'DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            str(Path(os.getenv('WINDIR', 'C:/Windows')) / 'Fonts' / 'arial.ttf'),
            '/System/Library/Fonts/Supplemental/Arial.ttf',
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                try:
                    pdfmetrics.registerFont(TTFont('StudyBoostUnicode', candidate))
                    self.russian_font = 'StudyBoostUnicode'
                    break
                except Exception:
                    continue

    def create_notes_pdf(self, user_id: int, notes: List[Dict], 
                        category: str = None, username: str = 'Студент') -> str:
        """
        Создание PDF конспекта из заметок
        
        Args:
            user_id: ID пользователя
            notes: Список заметок
            category: Категория для фильтрации (опционально)
            username: Имя пользователя
        
        Returns:
            Путь к созданному PDF файлу
        """
        if not self.russian_font:
            raise RuntimeError('Install a Cyrillic font or set STUDYBOOST_FONT')
        # Фильтрация по категории если указана
        if category:
            notes = [n for n in notes if n.get('category') == category]
            filename = f"{self.output_dir}/conspect_{user_id}_{uuid4().hex}.pdf"
            title = f"Конспект по предмету: {category}"
        else:
            filename = f"{self.output_dir}/conspect_{user_id}_{uuid4().hex}.pdf"
            title = "Общий конспект"
        
        # Создание документа
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Стили
        styles = getSampleStyleSheet()
        
        # Настройка стилей для русского текста
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=self.russian_font,
            fontSize=24,
            textColor=HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=1  # Центрирование
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontName=self.russian_font,
            fontSize=16,
            textColor=HexColor('#3498DB'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=self.russian_font,
            fontSize=11,
            leading=14,
            spaceAfter=10
        )
        
        meta_style = ParagraphStyle(
            'CustomMeta',
            parent=styles['Normal'],
            fontName=self.russian_font,
            fontSize=9,
            textColor=HexColor('#7F8C8D'),
            spaceAfter=6
        )
        
        # Содержимое документа
        content = []
        
        # Заголовок
        content.append(Paragraph(escape(title), title_style))
        content.append(Paragraph(f"Автор: {escape(username)}", meta_style))
        content.append(Paragraph(
            f"Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}", 
            meta_style
        ))
        content.append(Paragraph(
            f"Всего заметок: {len(notes)}", 
            meta_style
        ))
        content.append(Spacer(1, 0.5*cm))
        
        # Группировка заметок по категориям
        categories = {}
        for note in notes:
            cat = note.get('category', 'Без категории')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(note)
        
        # Добавление заметок
        for cat_name, cat_notes in sorted(categories.items()):
            # Заголовок категории
            content.append(PageBreak())
            content.append(Paragraph(f"📚 {escape(cat_name)}", heading_style))
            content.append(Paragraph(
                f"Заметок в разделе: {len(cat_notes)}", 
                meta_style
            ))
            content.append(Spacer(1, 0.3*cm))
            
            # Заметки в категории
            for i, note in enumerate(cat_notes, 1):
                # Дата создания
                created = datetime.strptime(note['created_at'], '%Y-%m-%d %H:%M:%S')
                date_str = created.strftime('%d.%m.%Y %H:%M')
                
                # Теги
                tags = note.get('tags', [])
                tags_str = ' '.join(tags) if tags else 'Без тегов'
                
                # Метаинформация
                content.append(Paragraph(
                    f"<b>Заметка #{i}</b> | {date_str} | {escape(tags_str)}",
                    meta_style
                ))
                
                # Содержимое заметки
                note_type = note.get('note_type', 'text')
                note_content = note.get('content', '')
                
                if note_type == 'text':
                    # Обработка текста для PDF (экранирование спецсимволов)
                    safe_content = note_content.replace('&', '&amp;')\
                                               .replace('<', '&lt;')\
                                               .replace('>', '&gt;')
                    content.append(Paragraph(safe_content, normal_style))
                
                elif note_type == 'photo':
                    content.append(Paragraph(
                        f"📷 <i>Заметка с фотографией</i>", 
                        normal_style
                    ))
                    if note_content:
                        safe_content = note_content.replace('&', '&amp;')\
                                                   .replace('<', '&lt;')\
                                                   .replace('>', '&gt;')
                        content.append(Paragraph(
                            f"Описание: {safe_content}", 
                            normal_style
                        ))
                
                elif note_type == 'voice':
                    duration = note.get('duration', 0)
                    content.append(Paragraph(
                        f"🎤 <i>Голосовая заметка ({duration} сек.)</i>", 
                        normal_style
                    ))
                
                content.append(Spacer(1, 0.5*cm))
        
        # Футер
        content.append(PageBreak())
        content.append(Paragraph("📊 Статистика", heading_style))
        
        # Подсчет статистики
        total_notes = len(notes)
        text_notes = len([n for n in notes if n.get('note_type') == 'text'])
        photo_notes = len([n for n in notes if n.get('note_type') == 'photo'])
        voice_notes = len([n for n in notes if n.get('note_type') == 'voice'])
        
        # Все уникальные теги
        all_tags = set()
        for note in notes:
            all_tags.update(note.get('tags', []))
        
        stats_data = [
            ['Показатель', 'Значение'],
            ['Всего заметок', str(total_notes)],
            ['Текстовых', str(text_notes)],
            ['С фотографиями', str(photo_notes)],
            ['Голосовых', str(voice_notes)],
            ['Категорий', str(len(categories))],
            ['Уникальных тегов', str(len(all_tags))]
        ]
        
        stats_table = Table(stats_data, colWidths=[8*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.russian_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ECF0F1')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
        ]))
        
        content.append(stats_table)
        content.append(Spacer(1, 1*cm))
        
        # Подпись
        content.append(Paragraph(
            f"<i>Конспект создан в StudyBoost 🎓</i>", 
            meta_style
        ))
        
        # Генерация PDF
        doc.build(content)
        
        return filename
    
    def create_schedule_pdf(self, user_id: int, schedule: List[Dict], 
                           username: str = 'Студент') -> str:
        """
        Создание PDF расписания занятий
        
        Args:
            user_id: ID пользователя
            schedule: Список занятий
            username: Имя пользователя
        
        Returns:
            Путь к созданному PDF файлу
        """
        filename = f"{self.output_dir}/schedule_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=self.russian_font,
            fontSize=24,
            textColor=HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=1
        )
        
        content = []
        
        # Заголовок
        content.append(Paragraph("📅 Расписание занятий", title_style))
        content.append(Paragraph(f"Студент: {escape(username)}", styles['Normal']))
        content.append(Spacer(1, 1*cm))
        
        # Дни недели
        days = {
            0: 'Понедельник',
            1: 'Вторник',
            2: 'Среда',
            3: 'Четверг',
            4: 'Пятница',
            5: 'Суббота',
            6: 'Воскресенье'
        }
        
        # Группировка по дням
        schedule_by_day = {}
        for item in schedule:
            day = item['day_of_week']
            if day not in schedule_by_day:
                schedule_by_day[day] = []
            schedule_by_day[day].append(item)
        
        # Таблица расписания по дням
        for day_num in sorted(schedule_by_day.keys()):
            day_name = days.get(day_num, f"День {day_num}")
            day_schedule = sorted(schedule_by_day[day_num], 
                                key=lambda x: x['start_time'])
            
            content.append(Paragraph(f"<b>{day_name}</b>", styles['Heading2']))
            
            table_data = [['Время', 'Предмет', 'Аудитория']]
            for item in day_schedule:
                time_str = f"{item['start_time']} - {item['end_time']}"
                table_data.append([
                    time_str,
                    item['subject'],
                    item.get('location', '-')
                ])
            
            schedule_table = Table(table_data, colWidths=[4*cm, 7*cm, 4*cm])
            schedule_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), self.russian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7'))
            ]))
            
            content.append(schedule_table)
            content.append(Spacer(1, 0.5*cm))
        
        doc.build(content)
        
        return filename
