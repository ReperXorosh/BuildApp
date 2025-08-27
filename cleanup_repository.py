#!/usr/bin/env python3
"""
Скрипт для очистки временных файлов перед загрузкой в репозиторий
"""

import os
import shutil
import glob

def cleanup_repository():
    """Очищает временные файлы и папки"""
    print("=== ОЧИСТКА РЕПОЗИТОРИЯ ===\n")
    
    # Список файлов и папок для удаления
    items_to_remove = [
        # Отчеты
        "MOSCOW_TIME_REPORT.md",
        "ACTIVITY_LOGGING_UPDATE_REPORT.md",
        "ACTIVITY_LOG_REPORT.md",
        "BLUE_ALERT_REMOVAL_REPORT.md",
        "DATA_PROTECTION_GUIDE.md",
        "DBeaver_Integration_Guide.md",
        "DBeaver_Setup_Guide.md",
        "LOGIN_FIX_REPORT.md",
        "DATABASE_FIX_REPORT.md",
        "AVATAR_EDITOR_REPORT.md",
        "AVATAR_FIX_REPORT.md",
        "REGISTRATION_DATES_REPORT.md",
        "UPDATED_ACCESS_REPORT.md",
        "ROLES_UPDATE_REPORT.md",
        "UUID_SECURITY_REPORT.md",
        
        # Тестовые скрипты
        "test_moscow_time.py",
        "fix_moscow_time.py",
        "test_activity_logging.py",
        "create_activity_log_table.py",
        "test_activity_log.py",
        "test_no_blue_alert.py",
        "database_protection_system_simple.py",
        "start_simple_protection.py",
        "check_database_details.py",
        "safe_database_operations.py",
        "test_app.py",
        "fix_admin2_password.py",
        "test_login.py",
        "backup_database.py",
        "fix_database.py",
        "verify_database.py",
        "test_phone_numbers.py",
        "test_avatar_editor_hidden.py",
        "test_clean_page.py",
        "test_minimal_padding.py",
        "test_fixed_sidebar.py",
        "test_scrolling_aggressive.py",
        "test_scrolling_final.py",
        "test_scrolling_fix.py",
        "test_page_length.py",
        "test_sidebar_fix.py",
        "test_edit_page_scrolling.py",
        "test_avatar_editor.py",
        "check_avatar_upload.py",
        "test_avatar_upload.py",
        "check_current_users.py",
        "set_moscow_time.py",
        "demo_seconds_display.py",
        "set_today_with_seconds.py",
        "verify_today_dates.py",
        "set_today_registration_dates.py",
        "create_users_with_dates.py",
        "recreate_db_with_registration_dates.py",
        "test_registration_dates.py",
        "migrate_registration_dates.py",
        "update_registration_dates.py",
        "test_user_access.py",
        "test_new_roles.py",
        "update_roles.py",
        "test_admin_functions.py",
        "check_kulikov.py",
        "demo_uuid_security.py",
        "test_add_user.py",
        "create_uuid_db.py",
        "init_db.py",
        "create_user.py",
        
        # Система защиты данных
        "start_protection.py",
        "auto_data_protection.py",
        "database_protection_system.py",
        
        # Папки
        "database_protection/",
        "backups/",
        "babel/",
        "venv/",
        "__pycache__/",
        ".idea/",
        "instance/",
        
        # Конфигурационные файлы
        "babel.cfg",
        ".dockerignore",
        ".flaskenv",
        "app.ini"
    ]
    
    removed_count = 0
    
    for item in items_to_remove:
        if os.path.exists(item):
            try:
                if os.path.isfile(item):
                    os.remove(item)
                    print(f"   ✅ Удален файл: {item}")
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"   ✅ Удалена папка: {item}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Ошибка при удалении {item}: {e}")
    
    # Удаляем все файлы с определенными паттернами
    patterns_to_remove = [
        "test_*.py",
        "check_*.py", 
        "fix_*.py",
        "verify_*.py",
        "create_*.py",
        "update_*.py",
        "set_*.py",
        "demo_*.py",
        "migrate_*.py",
        "recreate_*.py",
        "backup_*.py",
        "safe_*.py",
        "start_*.py",
        "auto_*.py",
        "database_protection_system*.py",
        "*_REPORT.md",
        "*_GUIDE.md"
    ]
    
    for pattern in patterns_to_remove:
        for file_path in glob.glob(pattern):
            if os.path.basename(file_path) != "init_database.py":  # Не удаляем важный файл
                try:
                    os.remove(file_path)
                    print(f"   ✅ Удален файл: {file_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"   ❌ Ошибка при удалении {file_path}: {e}")
    
    print(f"\n✅ Очистка завершена!")
    print(f"✅ Удалено элементов: {removed_count}")
    
    # Показываем оставшиеся файлы
    print(f"\n📁 Оставшиеся файлы в корне проекта:")
    for item in os.listdir('.'):
        if os.path.isfile(item):
            print(f"   📄 {item}")
        elif os.path.isdir(item):
            print(f"   📁 {item}/")
    
    print(f"\n🎯 Репозиторий готов к загрузке!")
    print(f"   Основные файлы сохранены:")
    print(f"   - app/ (основное приложение)")
    print(f"   - requirements.txt (зависимости)")
    print(f"   - run.py (точка входа)")
    print(f"   - init_database.py (инициализация БД)")
    print(f"   - README.md (документация)")
    print(f"   - .gitignore (исключения)")
    print(f"   - Dockerfile, docker-compose.yml (Docker)")
    print(f"   - nginx/ (конфигурация Nginx)")

if __name__ == '__main__':
    cleanup_repository()

