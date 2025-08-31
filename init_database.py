#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Создает таблицы и добавляет пользователей по умолчанию
"""

from app import create_app
from app.extensions import db
from app.models.users import Users
from app.models.activity_log import ActivityLog
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone, timedelta
import pytz

def init_database():
    """Инициализирует базу данных"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ===\n")
            
            # Создаем все таблицы
            db.create_all()
            print("✅ Таблицы созданы успешно")
            
            # Проверяем, есть ли уже пользователи
            existing_users = Users.query.count()
            if existing_users > 0:
                print(f"✅ В базе данных уже есть {existing_users} пользователей")
                return
            
            # Московское время
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz)
            
            # Создаем пользователей по умолчанию
            default_users = [
                {
                    'login': 'admin',
                    'password': 'admin123',
                    'firstname': 'Администратор',
                    'secondname': 'Системы',
                    'thirdname': '',
                    'phonenumber': '+7 (999) 123-45-67',
                    'role': 'Инженер ПТО',
                    'registration_date': current_time
                },
                {
                    'login': 'admin2',
                    'password': 'admin123',
                    'firstname': 'Второй',
                    'secondname': 'Администратор',
                    'thirdname': '',
                    'phonenumber': '+7 (999) 234-56-78',
                    'role': 'Инженер ПТО',
                    'registration_date': current_time
                },
                {
                    'login': 'krasnov',
                    'password': 'krasnov123',
                    'firstname': 'Краснов',
                    'secondname': 'Александр',
                    'thirdname': 'Петрович',
                    'phonenumber': '+7 (999) 345-67-89',
                    'role': 'Ген.Директор',
                    'registration_date': current_time
                },
                {
                    'login': 'kulikov',
                    'password': 'kulikov123',
                    'firstname': 'Куликов',
                    'secondname': 'Дмитрий',
                    'thirdname': 'Иванович',
                    'phonenumber': '+7 (999) 456-78-90',
                    'role': 'Зам.Директор',
                    'registration_date': current_time
                },
                {
                    'login': 'ceremisin',
                    'password': 'ceremisin123',
                    'firstname': 'Черемисин',
                    'secondname': 'Сергей',
                    'thirdname': 'Александрович',
                    'phonenumber': '+7 (999) 567-89-01',
                    'role': 'Прораб',
                    'registration_date': current_time
                },
                {
                    'login': 'bovin',
                    'password': 'bovin123',
                    'firstname': 'Бовин',
                    'secondname': 'Михаил',
                    'thirdname': 'Сергеевич',
                    'phonenumber': '+7 (999) 678-90-12',
                    'role': 'Прораб',
                    'registration_date': current_time
                },
                {
                    'login': 'supplier',
                    'password': 'supplier123',
                    'firstname': 'Снабженец',
                    'secondname': 'Анна',
                    'thirdname': 'Владимировна',
                    'phonenumber': '+7 (999) 789-01-23',
                    'role': 'Снабженец',
                    'registration_date': current_time
                }
            ]
            
            # Добавляем пользователей
            for user_data in default_users:
                user = Users(
                    login=user_data['login'],
                    password=generate_password_hash(user_data['password']),
                    firstname=user_data['firstname'],
                    secondname=user_data['secondname'],
                    thirdname=user_data['thirdname'],
                    phonenumber=user_data['phonenumber'],
                    role=user_data['role'],
                    registration_date=user_data['registration_date']
                )
                db.session.add(user)
                print(f"   ✅ Добавлен пользователь: {user_data['login']} ({user_data['role']})")
            
            # Создаем запись в журнале действий
            init_log = ActivityLog(
                user_id=None,
                user_login="Система",
                action="Инициализация базы данных",
                description="База данных инициализирована с пользователями по умолчанию",
                ip_address="127.0.0.1",
                page_url="init_database.py",
                method="SCRIPT"
            )
            db.session.add(init_log)
            
            # Сохраняем изменения
            db.session.commit()
            
            print(f"\n✅ База данных инициализирована успешно!")
            print(f"✅ Добавлено пользователей: {len(default_users)}")
            print(f"✅ Время инициализации: {current_time.strftime('%d.%m.%Y %H:%M:%S')}")
            
            print(f"\n🔐 Пользователи для входа:")
            for user_data in default_users:
                print(f"   - {user_data['login']} / {user_data['password']} ({user_data['role']})")
            
            print(f"\n🌐 Приложение готово к запуску!")
            print(f"   Запустите: python run.py")
            print(f"   Откройте: http://localhost:5000")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации базы данных: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_database()

