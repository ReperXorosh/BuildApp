#!/usr/bin/env python3
"""
Миграция для добавления поля timezone в таблицу users
"""

from app import create_app
from app.extensions import db
from app.models.users import Users
from sqlalchemy import text

def add_timezone_column():
    """Добавляет поле timezone в таблицу users"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== ДОБАВЛЕНИЕ ПОЛЯ TIMEZONE В ТАБЛИЦУ USERS ===\n")
            
            # Проверяем, существует ли уже поле timezone
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'timezone' in columns:
                print("✅ Поле timezone уже существует в таблице users")
                return True
            
            # Добавляем поле timezone
            print("📝 Добавление поля timezone...")
            
            # Для SQLite
            if 'sqlite' in str(db.engine.url):
                db.engine.execute(text("""
                    ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Moscow'
                """))
                print("✅ Поле timezone добавлено в SQLite")
            
            # Для PostgreSQL
            elif 'postgresql' in str(db.engine.url):
                db.engine.execute(text("""
                    ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'Europe/Moscow'
                """))
                print("✅ Поле timezone добавлено в PostgreSQL")
            
            else:
                print("❌ Неподдерживаемая база данных")
                return False
            
            # Обновляем существующих пользователей
            print("🔄 Обновление существующих пользователей...")
            users = Users.query.all()
            updated_count = 0
            
            for user in users:
                if not user.timezone:
                    user.timezone = 'Europe/Moscow'
                    updated_count += 1
            
            db.session.commit()
            print(f"✅ Обновлено пользователей: {updated_count}")
            
            print("\n🎉 Миграция успешно завершена!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении миграции: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    add_timezone_column()
