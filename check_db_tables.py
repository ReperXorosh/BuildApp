#!/usr/bin/env python3
"""
Скрипт для проверки существующих таблиц в базе данных
"""

import os
import sys

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db

def check_database_tables():
    """Проверка существующих таблиц в базе данных"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Проверка таблиц в базе данных...")
        
        try:
            # Получаем список всех таблиц
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"📋 Найдено таблиц: {len(tables)}")
            
            for table in tables:
                print(f"   - {table}")
                
                # Получаем информацию о колонках
                columns = inspector.get_columns(table)
                print(f"     Колонки ({len(columns)}):")
                for column in columns:
                    print(f"       - {column['name']}: {column['type']}")
                print()
                
        except Exception as e:
            print(f"❌ Ошибка при проверке таблиц: {e}")

if __name__ == "__main__":
    check_database_tables()

