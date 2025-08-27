#!/usr/bin/env python3
"""
Скрипт для восстановления всех удаленных файлов
Используйте этот скрипт, если нужно вернуть временные файлы
"""

import os
import shutil

def restore_files():
    """Восстанавливает удаленные файлы"""
    print("=== ВОССТАНОВЛЕНИЕ ФАЙЛОВ ===\n")
    
    # Список файлов для восстановления (если есть резервные копии)
    files_to_restore = [
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
        
        # Конфигурационные файлы
        "babel.cfg",
        ".dockerignore",
        ".flaskenv",
        "app.ini"
    ]
    
    restored_count = 0
    
    print("📋 Способы восстановления файлов:")
    print("1. Из Git истории:")
    print("   git log --oneline")
    print("   git checkout <commit-hash> -- filename.py")
    print()
    print("2. Из резервной копии:")
    print("   Скопируйте файлы из backup_folder/")
    print()
    print("3. Из корзины Windows:")
    print("   Проверьте корзину Windows")
    print()
    print("4. Из облачного хранилища:")
    print("   Если файлы были синхронизированы")
    print()
    
    # Проверяем, есть ли резервные копии
    backup_folders = ["backup", "backup_files", "old_files", "temp_backup"]
    
    for folder in backup_folders:
        if os.path.exists(folder):
            print(f"✅ Найдена папка резервных копий: {folder}")
            for file in files_to_restore:
                backup_path = os.path.join(folder, file)
                if os.path.exists(backup_path):
                    try:
                        shutil.copy2(backup_path, file)
                        print(f"   ✅ Восстановлен: {file}")
                        restored_count += 1
                    except Exception as e:
                        print(f"   ❌ Ошибка восстановления {file}: {e}")
    
    if restored_count == 0:
        print("❌ Резервные копии не найдены")
        print()
        print("🔧 Ручное восстановление:")
        print("1. Создайте папку backup/")
        print("2. Поместите туда нужные файлы")
        print("3. Запустите этот скрипт снова")
    else:
        print(f"\n✅ Восстановлено файлов: {restored_count}")

if __name__ == '__main__':
    restore_files()

