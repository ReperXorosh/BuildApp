#!/usr/bin/env python3
"""
Комплексный скрипт для исправления всех временных меток в базе данных
Приводит все время к московскому часовому поясу
"""

from app import create_app
from app.extensions import db
from app.models.users import Users
from app.models.activity_log import ActivityLog
from app.models.supply import Material, Equipment, SupplyOrder
from datetime import datetime
import pytz
from app.utils.timezone_utils import to_moscow_time, get_moscow_now

def fix_all_timezones():
    """Исправляет все временные метки в базе данных"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ ВРЕМЕННЫХ МЕТОК ===\n")
            
            # Часовые пояса
            utc_tz = pytz.UTC
            moscow_tz = pytz.timezone('Europe/Moscow')
            
            total_updated = 0
            
            # 1. Исправляем пользователей
            print("1. Исправление времени регистрации пользователей...")
            users = Users.query.all()
            users_updated = 0
            
            for user in users:
                if user.registration_date:
                    old_date = user.registration_date
                    moscow_date = to_moscow_time(old_date)
                    
                    if moscow_date != old_date:
                        user.registration_date = moscow_date
                        users_updated += 1
                        print(f"   ✅ {user.login}: {old_date} → {moscow_date}")
            
            print(f"   📊 Обновлено пользователей: {users_updated}")
            total_updated += users_updated
            
            # 2. Исправляем журнал действий
            print("\n2. Исправление времени в журнале действий...")
            logs = ActivityLog.query.all()
            logs_updated = 0
            
            for log in logs:
                if log.created_at:
                    old_date = log.created_at
                    moscow_date = to_moscow_time(old_date)
                    
                    if moscow_date != old_date:
                        log.created_at = moscow_date
                        logs_updated += 1
                        print(f"   ✅ {log.action} ({log.user_login}): {old_date} → {moscow_date}")
            
            print(f"   📊 Обновлено записей журнала: {logs_updated}")
            total_updated += logs_updated
            
            # 3. Исправляем материалы
            print("\n3. Исправление времени создания/обновления материалов...")
            materials = Material.query.all()
            materials_updated = 0
            
            for material in materials:
                updated = False
                
                if material.created_at:
                    old_date = material.created_at
                    moscow_date = to_moscow_time(old_date)
                    if moscow_date != old_date:
                        material.created_at = moscow_date
                        updated = True
                
                if material.updated_at:
                    old_date = material.updated_at
                    moscow_date = to_moscow_time(old_date)
                    if moscow_date != old_date:
                        material.updated_at = moscow_date
                        updated = True
                
                if updated:
                    materials_updated += 1
                    print(f"   ✅ {material.name}: обновлено время")
            
            print(f"   📊 Обновлено материалов: {materials_updated}")
            total_updated += materials_updated
            
            # 4. Исправляем оборудование
            print("\n4. Исправление времени создания/обновления оборудования...")
            equipment = Equipment.query.all()
            equipment_updated = 0
            
            for item in equipment:
                updated = False
                
                if item.created_at:
                    old_date = item.created_at
                    moscow_date = to_moscow_time(old_date)
                    if moscow_date != old_date:
                        item.created_at = moscow_date
                        updated = True
                
                if item.updated_at:
                    old_date = item.updated_at
                    moscow_date = to_moscow_time(old_date)
                    if moscow_date != old_date:
                        item.updated_at = moscow_date
                        updated = True
                
                if updated:
                    equipment_updated += 1
                    print(f"   ✅ {item.name}: обновлено время")
            
            print(f"   📊 Обновлено оборудования: {equipment_updated}")
            total_updated += equipment_updated
            
            # 5. Исправляем заказы на снабжение
            print("\n5. Исправление времени создания/обновления заказов...")
            orders = SupplyOrder.query.all()
            orders_updated = 0
            
            for order in orders:
                updated = False
                
                if order.created_at:
                    old_date = order.created_at
                    moscow_date = to_moscow_time(old_date)
                    if moscow_date != old_date:
                        order.created_at = moscow_date
                        updated = True
                
                if order.updated_at:
                    old_date = order.updated_at
                    moscow_date = to_moscow_time(old_date)
                    if moscow_date != old_date:
                        order.updated_at = moscow_date
                        updated = True
                
                if updated:
                    orders_updated += 1
                    print(f"   ✅ Заказ {order.order_number}: обновлено время")
            
            print(f"   📊 Обновлено заказов: {orders_updated}")
            total_updated += orders_updated
            
            # Сохраняем все изменения
            if total_updated > 0:
                db.session.commit()
                print(f"\n✅ УСПЕШНО ОБНОВЛЕНО!")
                print(f"📊 Всего обновлено записей: {total_updated}")
            else:
                print(f"\n✅ Все записи уже имеют правильное московское время!")
            
            # Показываем текущее московское время
            current_moscow_time = get_moscow_now()
            print(f"🕐 Текущее московское время: {current_moscow_time}")
            
            # Статистика
            print(f"\n📈 СТАТИСТИКА:")
            print(f"   👥 Пользователей: {len(users)}")
            print(f"   📝 Записей журнала: {len(logs)}")
            print(f"   📦 Материалов: {len(materials)}")
            print(f"   🔧 Оборудования: {len(equipment)}")
            print(f"   📋 Заказов: {len(orders)}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            db.session.rollback()

def test_timezone_system():
    """Тестирует систему работы с часовыми поясами"""
    print("=== ТЕСТИРОВАНИЕ СИСТЕМЫ ЧАСОВЫХ ПОЯСОВ ===\n")
    
    from app.utils.timezone_utils import get_moscow_now, to_moscow_time, format_moscow_time
    
    # Текущее время
    moscow_now = get_moscow_now()
    print(f"🕐 Текущее московское время: {moscow_now}")
    
    # Тест конвертации
    utc_time = datetime.now(pytz.UTC)
    print(f"🌍 UTC время: {utc_time}")
    
    converted = to_moscow_time(utc_time)
    print(f"🔄 Конвертировано в Москву: {converted}")
    
    # Тест форматирования
    formatted = format_moscow_time(utc_time)
    print(f"📅 Отформатировано: {formatted}")
    
    # Тест времени без часового пояса (как в базе данных)
    naive_time = datetime.now()
    print(f"📅 Наивное время: {naive_time}")
    
    converted_naive = to_moscow_time(naive_time)
    print(f"🔄 Конвертировано наивное время: {converted_naive}")
    
    formatted_naive = format_moscow_time(naive_time)
    print(f"📅 Отформатировано наивное время: {formatted_naive}")

if __name__ == '__main__':
    test_timezone_system()
    print("\n" + "="*60 + "\n")
    fix_all_timezones()
