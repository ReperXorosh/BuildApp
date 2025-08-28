#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с новыми таблицами объектов
"""

import os
import sys
from datetime import datetime

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.objects import Object, Support, Trench, Report, Checklist, ChecklistItem

def init_objects_database():
    """Инициализация базы данных с таблицами объектов"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Инициализация базы данных объектов...")
        
        try:
            # Создаем все таблицы
            db.create_all()
            print("✅ Таблицы объектов успешно созданы")
            
            # Создаем тестовые данные
            create_sample_data()
            
            print("✅ База данных объектов инициализирована успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации базы данных: {e}")
            return False
    
    return True

def create_sample_data():
    """Создание тестовых данных"""
    
    print("📝 Создание тестовых данных...")
    
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
    print("🚀 Запуск инициализации базы данных объектов...")
    print("=" * 50)
    
    success = init_objects_database()
    
    print("=" * 50)
    if success:
        print("🎉 Инициализация завершена успешно!")
        print("\n📋 Что было создано:")
        print("   - Таблица 'objects' - основные объекты")
        print("   - Таблица 'supports' - опоры")
        print("   - Таблица 'trenches' - траншеи")
        print("   - Таблица 'reports' - отчёты")
        print("   - Таблица 'checklists' - чек-листы")
        print("   - Таблица 'checklist_items' - элементы чек-листов")
        print("\n🔗 Теперь вы можете:")
        print("   - Открыть приложение и перейти к 'Список объектов'")
        print("   - Создавать новые объекты и их подпункты")
        print("   - Управлять опорами, траншеями, отчётами и чек-листами")
    else:
        print("💥 Инициализация завершилась с ошибками!")
        sys.exit(1)

