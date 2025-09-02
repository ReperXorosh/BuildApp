#!/usr/bin/env python3
"""
Скрипт для исправления структуры базы данных чек-листов
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_checklist_database():
    """Исправляет структуру базы данных для чек-листов"""
    
    # Получаем строку подключения из переменных окружения
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/buildapp')
    
    try:
        # Создаем подключение к базе данных
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Проверяем, существует ли таблица checklists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'checklists'
                );
            """))
            
            if not result.scalar():
                print("Таблица checklists не существует. Создаем...")
                # Создаем таблицу с правильной структурой
                conn.execute(text("""
                    CREATE TABLE checklists (
                        id VARCHAR(36) PRIMARY KEY,
                        object_id VARCHAR(36) NOT NULL UNIQUE,
                        checklist_number VARCHAR(50) NOT NULL,
                        title VARCHAR(255) DEFAULT 'Чек-лист объекта',
                        status VARCHAR(50) DEFAULT 'pending',
                        total_items INTEGER DEFAULT 0,
                        completed_items INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR(36)
                    );
                """))
                print("Таблица checklists создана успешно!")
            else:
                print("Таблица checklists существует. Проверяем структуру...")
                
                # Проверяем, есть ли поле checklist_number
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'checklists' 
                    AND column_name = 'checklist_number';
                """))
                
                if not result.fetchone():
                    print("Добавляем поле checklist_number...")
                    # Добавляем поле checklist_number
                    conn.execute(text("""
                        ALTER TABLE checklists 
                        ADD COLUMN checklist_number VARCHAR(50);
                    """))
                    
                    # Заполняем существующие записи
                    conn.execute(text("""
                        UPDATE checklists 
                        SET checklist_number = 'ЧЛ-' || EXTRACT(EPOCH FROM created_at)::BIGINT::TEXT
                        WHERE checklist_number IS NULL;
                    """))
                    
                    # Делаем поле NOT NULL
                    conn.execute(text("""
                        ALTER TABLE checklists 
                        ALTER COLUMN checklist_number SET NOT NULL;
                    """))
                    
                    print("Поле checklist_number добавлено и заполнено!")
                else:
                    print("Поле checklist_number уже существует.")
                
                # Проверяем, есть ли поле created_by
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'checklists' 
                    AND column_name = 'created_by';
                """))
                
                if not result.fetchone():
                    print("Добавляем поле created_by...")
                    conn.execute(text("""
                        ALTER TABLE checklists 
                        ADD COLUMN created_by VARCHAR(36);
                    """))
                    print("Поле created_by добавлено!")
                else:
                    print("Поле created_by уже существует.")
            
            # Создаем таблицу checklist_items если её нет
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'checklist_items'
                );
            """))
            
            if not result.scalar():
                print("Таблица checklist_items не существует. Создаем...")
                conn.execute(text("""
                    CREATE TABLE checklist_items (
                        id VARCHAR(36) PRIMARY KEY,
                        checklist_id VARCHAR(36) NOT NULL,
                        item_text VARCHAR(500) NOT NULL,
                        is_completed BOOLEAN DEFAULT FALSE,
                        completed_at TIMESTAMP,
                        completed_by VARCHAR(36),
                        notes TEXT,
                        order_index INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
                    );
                """))
                print("Таблица checklist_items создана успешно!")
            else:
                print("Таблица checklist_items уже существует.")
            
            # Фиксируем изменения
            conn.commit()
            print("База данных успешно обновлена!")
            
    except Exception as e:
        print(f"Ошибка при обновлении базы данных: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Начинаем исправление базы данных...")
    if fix_checklist_database():
        print("Исправление завершено успешно!")
    else:
        print("Исправление завершилось с ошибкой!")
        sys.exit(1)
