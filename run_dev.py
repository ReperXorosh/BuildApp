#!/usr/bin/env python3
"""
Быстрый запуск Flask приложения в режиме разработки
Оптимизирован для максимальной скорости запуска
"""

import os
import sys
from app import create_app

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env')

# Создаем приложение
application = create_app()

if __name__ == '__main__':
    print("🚀 Запуск Flask приложения в режиме разработки...")
    print("📱 Доступно по адресу: http://localhost:5000")
    print("🔄 Автоперезагрузка включена")
    print("⚡ Оптимизировано для быстрого запуска")
    print("-" * 50)
    
    try:
        application.run(
            debug=True, 
            host='127.0.0.1',  # localhost для быстрого доступа
            port=5000,
            use_reloader=True,
            threaded=True,
            processes=1,
            use_debugger=True,
            extra_files=None  # Отключаем отслеживание дополнительных файлов
        )
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
