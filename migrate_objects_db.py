#!/usr/bin/env python3
"""
Скрипт для миграции базы данных объектов
"""

import os
import sys
from datetime import datetime

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db

def migrate_objects_database():
    """Миграция базы данных объектов"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Миграция базы данных объектов...")
        
        try:
            # Удаляем старые таблицы
            print("🗑️ Удаление старых таблиц...")
            
            # Удаляем старые таблицы в правильном порядке (из-за внешних ключей)
            with db.engine.connect() as conn:
                conn.execute(db.text("DROP TABLE IF EXISTS checklist_items"))
                conn.execute(db.text("DROP TABLE IF EXISTS checklists"))
                conn.execute(db.text("DROP TABLE IF EXISTS supports"))
                conn.execute(db.text("DROP TABLE IF EXISTS trenches"))
                conn.execute(db.text("DROP TABLE IF EXISTS reports"))
                conn.execute(db.text("DROP TABLE IF EXISTS objects"))
                conn.execute(db.text("DROP TABLE IF EXISTS columns"))
                conn.execute(db.text("DROP TABLE IF EXISTS models"))
                conn.execute(db.text("DROP TABLE IF EXISTS types"))
                conn.commit()
            
            print("✅ Старые таблицы удалены")
            
            # Создаем новые таблицы
            print("🏗️ Создание новых таблиц...")
            from app.models.objects import Object, Support, Trench, Report, Checklist, ChecklistItem
            
            db.create_all()
            print("✅ Новые таблицы созданы")
            
            # Создаем тестовые данные
            create_sample_data()
            
            print("✅ Миграция завершена успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка при миграции: {e}")
            return False
    
    return True

def create_sample_data():
    """Создание тестовых данных"""
    
    print("📝 Создание тестовых данных...")
    
    from app.models.objects import Object, Support, Trench, Report, Checklist, ChecklistItem
    
    # Создаем тестовый объект
    test_object = Object(
        id="test-object-001",
        name="Тестовый объект №1",
        description="Это тестовый объект для демонстрации функциональности системы управления объектами",
        location="г. Москва, ул. Тестовая, д. 1",
        status="active",
        created_by="admin"
    )
    
    db.session.add(test_object)
    
    # Создаем тестовую опору
    test_support = Support(
        id="test-support-001",
        object_id="test-object-001",
        support_number="ОП-001",
        support_type="Железобетонная",
        height=12.5,
        material="Железобетон",
        installation_date=datetime.now().date(),
        status="completed",
        notes="Тестовая опора для демонстрации",
        created_by="admin"
    )
    
    db.session.add(test_support)
    
    # Создаем тестовую траншею
    test_trench = Trench(
        id="test-trench-001",
        object_id="test-object-001",
        trench_number="ТР-001",
        length=150.0,
        width=1.2,
        depth=2.5,
        soil_type="Глина",
        excavation_date=datetime.now().date(),
        status="in_progress",
        notes="Тестовая траншея для демонстрации",
        created_by="admin"
    )
    
    db.session.add(test_trench)
    
    # Создаем тестовый отчёт
    test_report = Report(
        id="test-report-001",
        object_id="test-object-001",
        report_number="ОТ-001",
        report_type="Технический отчёт",
        title="Отчёт о выполненных работах",
        content="Выполнены работы по установке опоры и рытью траншеи",
        report_date=datetime.now().date(),
        status="submitted",
        notes="Тестовый отчёт для демонстрации",
        created_by="admin"
    )
    
    db.session.add(test_report)
    
    # Создаем тестовый чек-лист
    test_checklist = Checklist(
        id="test-checklist-001",
        object_id="test-object-001",
        checklist_number="ЧЛ-001",
        title="Чек-лист проверки качества",
        checklist_type="Контроль качества",
        completion_date=datetime.now().date(),
        status="completed",
        total_items=5,
        completed_items=5,
        notes="Тестовый чек-лист для демонстрации",
        created_by="admin"
    )
    
    db.session.add(test_checklist)
    
    # Создаем элементы чек-листа
    checklist_items = [
        "Проверка качества бетона",
        "Контроль геометрии опоры",
        "Проверка глубины траншеи",
        "Контроль ширины траншеи",
        "Проверка документации"
    ]
    
    for i, item_text in enumerate(checklist_items):
        checklist_item = ChecklistItem(
            id=f"test-item-{i+1:03d}",
            checklist_id="test-checklist-001",
            item_text=item_text,
            is_completed=True,
            completed_at=datetime.now(),
            completed_by="admin",
            order_index=i+1
        )
        db.session.add(checklist_item)
    
    # Создаем второй тестовый объект
    test_object2 = Object(
        id="test-object-002",
        name="Тестовый объект №2",
        description="Второй тестовый объект для демонстрации",
        location="г. Санкт-Петербург, ул. Примерная, д. 10",
        status="active",
        created_by="admin"
    )
    
    db.session.add(test_object2)
    
    # Сохраняем все изменения
    db.session.commit()
    
    print("✅ Тестовые данные созданы:")
    print(f"   - 2 объекта")
    print(f"   - 1 опора")
    print(f"   - 1 траншея")
    print(f"   - 1 отчёт")
    print(f"   - 1 чек-лист с 5 элементами")

if __name__ == "__main__":
    print("🚀 Запуск миграции базы данных объектов...")
    print("=" * 50)
    print("⚠️  ВНИМАНИЕ: Этот скрипт удалит старые таблицы объектов!")
    print("=" * 50)
    
    response = input("Продолжить? (y/N): ")
    if response.lower() != 'y':
        print("❌ Миграция отменена")
        sys.exit(0)
    
    success = migrate_objects_database()
    
    print("=" * 50)
    if success:
        print("🎉 Миграция завершена успешно!")
        print("\n📋 Что было сделано:")
        print("   - Удалены старые таблицы объектов")
        print("   - Созданы новые таблицы с правильной структурой")
        print("   - Добавлены тестовые данные")
        print("\n🔗 Теперь вы можете:")
        print("   - Открыть приложение и перейти к 'Список объектов'")
        print("   - Создавать новые объекты и их подпункты")
        print("   - Управлять опорами, траншеями, отчётами и чек-листами")
    else:
        print("💥 Миграция завершилась с ошибками!")
        sys.exit(1)
