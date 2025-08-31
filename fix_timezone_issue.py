#!/usr/bin/env python3
"""
Скрипт для исправления проблемы с часовыми поясами
Исправляет время регистрации пользователей, считая их UTC и конвертируя в московское время
"""

from app import create_app
from app.extensions import db
from app.models.users import Users
from datetime import datetime
import pytz

def fix_timezone_issue():
    """Исправляет проблему с часовыми поясами"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С ЧАСОВЫМИ ПОЯСАМИ ===\n")
            
            # Получаем всех пользователей
            users = Users.query.all()
            
            if not users:
                print("✅ Пользователей не найдено")
                return
            
            print(f"📋 Найдено {len(users)} пользователей")
            
            # Часовые пояса
            utc_tz = pytz.UTC
            moscow_tz = pytz.timezone('Europe/Moscow')
            
            # Обновляем время регистрации для всех пользователей
            updated_count = 0
            for user in users:
                old_date = user.registration_date
                
                if old_date:
                    # Если время без часового пояса, считаем его UTC и конвертируем в московское
                    if old_date.tzinfo is None:
                        # Предполагаем, что время в UTC (как сохраняется в базе данных)
                        utc_time = utc_tz.localize(old_date)
                        moscow_time = utc_time.astimezone(moscow_tz)
                        user.registration_date = moscow_time
                        updated_count += 1
                        print(f"  ✅ {user.login}: {old_date} (UTC) → {moscow_time} (Moscow)")
                    else:
                        # Если время уже с часовым поясом, просто конвертируем в московское
                        moscow_time = old_date.astimezone(moscow_tz)
                        if moscow_time != old_date:
                            user.registration_date = moscow_time
                            updated_count += 1
                            print(f"  ✅ {user.login}: {old_date} → {moscow_time} (Moscow)")
                        else:
                            print(f"  ⏭️ {user.login}: {old_date} (уже московское время)")
            
            # Сохраняем изменения
            if updated_count > 0:
                db.session.commit()
                print(f"\n✅ Обновлено {updated_count} пользователей")
            else:
                print(f"\n✅ Все записи уже имеют правильное московское время")
            
            # Показываем текущее московское время
            current_moscow_time = datetime.now(moscow_tz)
            print(f"🕐 Текущее московское время: {current_moscow_time}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            db.session.rollback()

def test_current_users():
    """Тестирует текущее время пользователей"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== ТЕСТИРОВАНИЕ ТЕКУЩИХ ПОЛЬЗОВАТЕЛЕЙ ===\n")
            
            users = Users.query.all()
            
            if not users:
                print("✅ Пользователей не найдено")
                return
            
            print(f"📋 Найдено {len(users)} пользователей\n")
            
            for user in users:
                if user.registration_date:
                    print(f"👤 {user.login}: {user.registration_date}")
                    if user.registration_date.tzinfo:
                        print(f"   📍 Часовой пояс: {user.registration_date.tzinfo}")
                    else:
                        print(f"   ⚠️ Без часового пояса")
                else:
                    print(f"👤 {user.login}: Нет даты регистрации")
                print()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_current_users()
    print("\n" + "="*50 + "\n")
    fix_timezone_issue()
