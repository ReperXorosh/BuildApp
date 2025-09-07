#!/usr/bin/env python3
"""
Скрипт для создания таблиц ЗДФ, Кронштейнов и Светильников
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.objects import ZDF, Bracket, Luminaire

def create_tables():
    """Создает таблицы для новых моделей"""
    app = create_app()
    
    with app.app_context():
        try:
            # Создаем таблицы
            db.create_all()
            print("✅ Таблицы для ЗДФ, Кронштейнов и Светильников успешно созданы!")
            
            # Проверяем, что таблицы созданы
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'zdf' in tables:
                print("✅ Таблица 'zdf' создана")
            if 'brackets' in tables:
                print("✅ Таблица 'brackets' создана")
            if 'luminaires' in tables:
                print("✅ Таблица 'luminaires' создана")
                
        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
            return False
    
    return True

if __name__ == '__main__':
    create_tables()
