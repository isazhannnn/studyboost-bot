import json
import os
import sys
from studyboost_bot import StudyBoostBot

def load_config():
    config_path = 'config.json'
    
    if not os.path.exists(config_path):
        print("❌ Файл config.json не найден!")
        print("📝 Создайте config.json на основе config.json.example")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config

def validate_config(config):
    if not config.get('bot_token') or config['bot_token'] == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Ошибка: Не указан токен бота!")
        print("📝 Получите токен у @BotFather в Telegram")
        print("⚙️ Укажите токен в файле config.json")
        return False
    
    return True

def print_banner():
    banner = """
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║       🎓 StudyBoost Bot 🎓           ║
    ║                                       ║
    ║   Твой персональный помощник в учебе  ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    """
    print(banner)

def print_status(config):
    print("\n📊 Статус бота:")
    print(f"  ✅ База данных: {config['database']['name']}")
    print(f"  {'✅' if config['features']['quiz_enabled'] else '❌'} Викторины: {'Включены' if config['features']['quiz_enabled'] else 'Выключены'}")
    print(f"  {'✅' if config['features']['pdf_generation'] else '❌'} PDF генерация: {'Включена' if config['features']['pdf_generation'] else 'Выключена'}")
    print(f"  {'✅' if config['features']['gamification'] else '❌'} Геймификация: {'Включена' if config['features']['gamification'] else 'Выключена'}")
    print(f"  {'✅' if config['features']['cloud_sync'] else '❌'} Облачная синхронизация: {'Включена' if config['features']['cloud_sync'] else 'Выключена'}")
    print()

def main():
    print_banner()
    
    print("🔧 Загрузка конфигурации...")
    config = load_config()
    
    if not validate_config(config):
        sys.exit(1)
    
    print("✅ Конфигурация загружена")
    
    print_status(config)
    
    print("🚀 Запуск бота...")
    print("💡 Для остановки нажмите Ctrl+C\n")
    
    try:
        bot = StudyBoostBot(config['bot_token'])
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")
        print("📊 Спасибо за использование StudyBoost!")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
