#!/usr/bin/env python3
"""
Скрипт для исправления времени регистрации пользователей
Устанавливает московское время для всех существующих пользователей
"""

from app import create_app
from app.extensions import db
from app.models.users import Users
from datetime import datetime
import pytz

def fix_registration_dates():
    """Исправляет время регистрации для всех пользователей"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== ИСПРАВЛЕНИЕ ВРЕМЕНИ РЕГИСТРАЦИИ ===\n")
            
            # Получаем всех пользователей
            users = Users.query.all()
            
            if not users:
                print("✅ Пользователей не найдено")
                return
            
            print(f"📋 Найдено {len(users)} пользователей")
            
            # Московское время
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz)
            
            # Обновляем время регистрации для всех пользователей
            updated_count = 0
            for user in users:
                old_date = user.registration_date
                user.registration_date = current_time
                updated_count += 1
                print(f"  ✅ {user.login}: {old_date} → {current_time}")
            
            # Сохраняем изменения
            db.session.commit()
            
            print(f"\n✅ Обновлено {updated_count} пользователей")
            print(f"🕐 Новое время регистрации: {current_time}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_registration_dates()
