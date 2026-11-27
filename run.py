"""Start StudyBoost with credentials from the environment or a local config."""
import json
import logging
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_config():
    config_path = BASE_DIR / 'config.json'
    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding='utf-8'))
        if not isinstance(config, dict):
            raise ValueError("config.json должен содержать JSON-объект")
    config['bot_token'] = os.getenv('BOT_TOKEN', config.get('bot_token', '')).strip()
    config['database_path'] = os.getenv(
        'STUDYBOOST_DB', config.get('database', {}).get('name', 'studyboost.db'))
    return config


def validate_config(config):
    return bool(re.fullmatch(r'\d{6,12}:[A-Za-z0-9_-]{30,}', config.get('bot_token', '')))


def main():
    try:
        config = load_config()
    except (OSError, ValueError, TypeError, AttributeError):
        print("Ошибка конфигурации. Проверьте локальный config.json.")
        return 1
    if not validate_config(config):
        print("Укажите действительный BOT_TOKEN в окружении или bot_token в локальном config.json.")
        return 1
    # HTTP request URLs contain the Telegram token.
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    os.chdir(BASE_DIR)
    from studyboost_bot import StudyBoostBot
    try:
        StudyBoostBot(config['bot_token'], config['database_path']).run()
    except KeyboardInterrupt:
        print("StudyBoost остановлен.")
    except Exception:
        # Avoid exposing URLs, credentials or message content in console output.
        print("Не удалось запустить бота. Проверьте сеть и конфигурацию.")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
