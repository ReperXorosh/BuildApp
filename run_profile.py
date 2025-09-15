#!/usr/bin/env python3
"""
Запуск Flask приложения с профилированием времени запуска
Помогает определить узкие места в инициализации
"""

import os
import sys
import time
from app import create_app

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env')

def profile_startup():
    """Профилирует время запуска приложения"""
    print("🔍 Профилирование времени запуска Flask приложения...")
    print("=" * 60)
    
    # Измеряем время импорта модулей
    start_time = time.time()
    
    print("📦 Импорт модулей...")
    import_start = time.time()
    
    # Импортируем основные модули
    from flask import Flask
    from app.extensions import db, login_manager, migrate
    from app.config import Config
    
    import_time = time.time() - import_start
    print(f"   ✅ Импорт модулей: {import_time:.3f} сек")
    
    # Измеряем время создания приложения
    print("🏗️  Создание приложения...")
    app_start = time.time()
    
    application = create_app()
    
    app_time = time.time() - app_start
    print(f"   ✅ Создание приложения: {app_time:.3f} сек")
    
    # Общее время
    total_time = time.time() - start_time
    print("=" * 60)
    print(f"⏱️  Общее время запуска: {total_time:.3f} сек")
    print(f"📊 Детализация:")
    print(f"   - Импорт модулей: {import_time:.3f} сек ({import_time/total_time*100:.1f}%)")
    print(f"   - Создание приложения: {app_time:.3f} сек ({app_time/total_time*100:.1f}%)")
    print("=" * 60)
    
    return application

if __name__ == '__main__':
    application = profile_startup()
    
    print("🚀 Запуск приложения...")
    print("📱 Доступно по адресу: http://localhost:5000")
    print("🔄 Автоперезагрузка включена")
    print("-" * 50)
    
    try:
        application.run(
            debug=True, 
            host='127.0.0.1',
            port=5000,
            use_reloader=True,
            threaded=True,
            processes=1
        )
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
