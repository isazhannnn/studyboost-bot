import random
from typing import List, Dict, Tuple


class QuizSystem:
    def __init__(self):
        self.quizzes = {
            'math': [
                {
                    'question': 'Чему равен корень из 144?',
                    'options': ['10', '11', '12', '14'],
                    'correct': 2,
                    'explanation': 'Правильный ответ: 12, потому что 12 × 12 = 144'
                },
                {
                    'question': 'Что такое производная функции x²?',
                    'options': ['x', '2x', 'x²', '2'],
                    'correct': 1,
                    'explanation': 'Производная x² = 2x по правилу степенной функции'
                },
                {
                    'question': 'Сколько градусов в сумме углов треугольника?',
                    'options': ['90°', '180°', '270°', '360°'],
                    'correct': 1,
                    'explanation': 'Сумма углов любого треугольника всегда равна 180°'
                },
                {
                    'question': 'Чему равен sin(90°)?',
                    'options': ['0', '0.5', '1', '√2/2'],
                    'correct': 2,
                    'explanation': 'sin(90°) = 1, это максимальное значение синуса'
                },
                {
                    'question': 'Формула площади круга?',
                    'options': ['2πr', 'πr²', 'πd', '4πr'],
                    'correct': 1,
                    'explanation': 'Площадь круга = πr², где r - радиус'
                }
            ],
            'physics': [
                {
                    'question': 'Какая единица измерения силы в СИ?',
                    'options': ['Джоуль', 'Ньютон', 'Ватт', 'Паскаль'],
                    'correct': 1,
                    'explanation': 'Ньютон (Н) - единица измерения силы в системе СИ'
                },
                {
                    'question': 'Формула второго закона Ньютона?',
                    'options': ['F = ma', 'E = mc²', 'P = mv', 'W = Fs'],
                    'correct': 0,
                    'explanation': 'F = ma - сила равна произведению массы на ускорение'
                },
                {
                    'question': 'Скорость света в вакууме примерно равна?',
                    'options': ['300 км/с', '3000 км/с', '300000 км/с', '30000 км/с'],
                    'correct': 2,
                    'explanation': 'Скорость света ≈ 300000 км/с или 3×10⁸ м/с'
                },
                {
                    'question': 'Что изучает термодинамика?',
                    'options': ['Движение', 'Теплоту', 'Свет', 'Звук'],
                    'correct': 1,
                    'explanation': 'Термодинамика изучает тепловые явления и энергию'
                },
                {
                    'question': 'Единица измерения электрического напряжения?',
                    'options': ['Ампер', 'Вольт', 'Ом', 'Кулон'],
                    'correct': 1,
                    'explanation': 'Вольт (В) - единица измерения напряжения'
                }
            ],
            'chemistry': [
                {
                    'question': 'Химический символ воды?',
                    'options': ['HO', 'H₂O', 'H₃O', 'OH'],
                    'correct': 1,
                    'explanation': 'H₂O - молекула воды состоит из 2 атомов водорода и 1 кислорода'
                },
                {
                    'question': 'Сколько элементов в периодической таблице Менделеева?',
                    'options': ['92', '103', '118', '120'],
                    'correct': 2,
                    'explanation': 'На данный момент известно 118 химических элементов'
                },
                {
                    'question': 'pH нейтрального раствора равен?',
                    'options': ['0', '7', '14', '1'],
                    'correct': 1,
                    'explanation': 'pH = 7 означает нейтральную среду (чистая вода)'
                },
                {
                    'question': 'Какой газ составляет большую часть атмосферы Земли?',
                    'options': ['Кислород', 'Углекислый газ', 'Азот', 'Водород'],
                    'correct': 2,
                    'explanation': 'Азот (N₂) составляет около 78% атмосферы'
                },
                {
                    'question': 'Формула поваренной соли?',
                    'options': ['KCl', 'NaCl', 'CaCl₂', 'MgCl₂'],
                    'correct': 1,
                    'explanation': 'NaCl - хлорид натрия, поваренная соль'
                }
            ],
            'cs': [
                {
                    'question': 'Что такое алгоритм?',
                    'options': ['Язык программирования', 'Последовательность действий', 
                               'Тип данных', 'Функция'],
                    'correct': 1,
                    'explanation': 'Алгоритм - четкая последовательность действий для решения задачи'
                },
                {
                    'question': 'Какая система счисления используется в компьютерах?',
                    'options': ['Десятичная', 'Двоичная', 'Восьмеричная', 'Шестнадцатеричная'],
                    'correct': 1,
                    'explanation': 'Компьютеры работают в двоичной системе (0 и 1)'
                },
                {
                    'question': 'Что такое переменная в программировании?',
                    'options': ['Константа', 'Хранилище данных', 'Функция', 'Класс'],
                    'correct': 1,
                    'explanation': 'Переменная - именованная область памяти для хранения данных'
                },
                {
                    'question': 'Сколько бит в одном байте?',
                    'options': ['4', '8', '16', '32'],
                    'correct': 1,
                    'explanation': '1 байт = 8 бит'
                },
                {
                    'question': 'Что делает цикл while?',
                    'options': ['Выполняет код один раз', 'Повторяет код пока условие истинно',
                               'Прерывает выполнение', 'Ничего'],
                    'correct': 1,
                    'explanation': 'while повторяет код пока условие истинно'
                }
            ]
        }
    
    def get_random_quiz(self, subject: str = None) -> Tuple[str, List[Dict]]:
        if subject and subject in self.quizzes:
            selected_subject = subject
        else:
            selected_subject = random.choice(list(self.quizzes.keys()))
        
        questions = random.sample(self.quizzes[selected_subject], 
                                min(5, len(self.quizzes[selected_subject])))
        
        return selected_subject, questions
    
    def check_answer(self, question: Dict, user_answer: int) -> Tuple[bool, str]:
        is_correct = user_answer == question['correct']
        explanation = question['explanation']
        
        return is_correct, explanation
    
    def get_subject_name(self, subject_key: str) -> str:
        names = {
            'math': 'Математика',
            'physics': 'Физика',
            'chemistry': 'Химия',
            'cs': 'Информатика'
        }
        return names.get(subject_key, subject_key)
