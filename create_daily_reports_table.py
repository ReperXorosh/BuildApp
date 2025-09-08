#!/usr/bin/env python3
"""
Миграция для создания таблицы daily_reports
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db

def create_daily_reports_table():
    """Создает таблицу daily_reports"""
    app = create_app()
    
    with app.app_context():
        try:
            # Создаем таблицу
            db.create_all()
            print("✅ Таблица daily_reports успешно создана!")
            
            # Проверяем, что таблица создана
            result = db.engine.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'daily_reports');")
            if result.fetchone()[0]:
                print("✅ Таблица daily_reports существует в базе данных")
            else:
                print("❌ Таблица daily_reports не найдена в базе данных")
                
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы: {e}")
            return False
    
    return True

if __name__ == "__main__":
    create_daily_reports_table()
