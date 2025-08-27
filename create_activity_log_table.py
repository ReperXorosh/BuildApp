#!/usr/bin/env python3
"""
Скрипт для создания таблицы журнала действий в базе данных
"""

from app import create_app
from app.extensions import db
from app.models.activity_log import ActivityLog

def create_activity_log_table():
    """Создает таблицу журнала действий"""
    app = create_app()
    
    with app.app_context():
        try:
            # Создаем таблицу
            db.create_all()
            print("✅ Таблица журнала действий создана успешно!")
            
            # Проверяем, что таблица создана
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'activity_logs' in tables:
                print("✅ Таблица 'activity_logs' найдена в базе данных")
                
                # Показываем структуру таблицы
                columns = inspector.get_columns('activity_logs')
                print("\n📋 Структура таблицы 'activity_logs':")
                for column in columns:
                    print(f"   - {column['name']}: {column['type']}")
                
                # Создаем тестовую запись
                test_log = ActivityLog(
                    user_id=None,
                    user_login="Система",
                    action="Инициализация",
                    description="Таблица журнала действий создана",
                    ip_address="127.0.0.1",
                    page_url="create_activity_log_table.py",
                    method="SCRIPT"
                )
                
                db.session.add(test_log)
                db.session.commit()
                print("✅ Тестовая запись создана успешно!")
                
            else:
                print("❌ Таблица 'activity_logs' не найдена в базе данных")
                
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("=== СОЗДАНИЕ ТАБЛИЦЫ ЖУРНАЛА ДЕЙСТВИЙ ===")
    create_activity_log_table()
    print("\n=== ГОТОВО ===")

