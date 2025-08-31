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
                
                # Если время без часового пояса, добавляем московский часовой пояс
                if old_date and old_date.tzinfo is None:
                    # Предполагаем, что существующее время уже в московском времени
                    user.registration_date = moscow_tz.localize(old_date)
                else:
                    # Если время уже с часовым поясом, обновляем на текущее
                    user.registration_date = current_time
                
                updated_count += 1
                print(f"  ✅ {user.login}: {old_date} → {user.registration_date}")
            
            # Сохраняем изменения
            db.session.commit()
            
            print(f"\n✅ Обновлено {updated_count} пользователей")
            print(f"🕐 Текущее московское время: {current_time}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            db.session.rollback()

def test_timezone():
    """Тестирует работу с часовыми поясами"""
    print("=== ТЕСТИРОВАНИЕ ЧАСОВЫХ ПОЯСОВ ===\n")
    
    # Московское время
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow_tz)
    
    # UTC время
    utc_tz = pytz.UTC
    utc_time = datetime.now(utc_tz)
    
    # Локальное время системы
    local_time = datetime.now()
    
    print(f"🕐 Московское время: {moscow_time}")
    print(f"🌍 UTC время: {utc_time}")
    print(f"💻 Локальное время: {local_time}")
    print(f"📊 Разница UTC-Москва: {utc_time.astimezone(moscow_tz) - moscow_time}")

if __name__ == '__main__':
    test_timezone()
    print("\n" + "="*50 + "\n")
    fix_registration_dates()
