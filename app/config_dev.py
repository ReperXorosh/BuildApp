"""
Конфигурация для режима разработки
Оптимизирована для быстрого запуска и отладки
"""

import os
from datetime import timedelta
from .config import Config

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    
    # Основные настройки
    DEBUG = True
    TESTING = False
    
    # Оптимизации для быстрого запуска
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False
    
    # Отключаем кэширование в разработке
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Настройки базы данных для разработки
    SQLALCHEMY_ECHO = False  # Отключаем SQL логи для скорости
    
    # Настройки сессий для разработки
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Отключаем планировщик задач в разработке
    SCHEDULER_ENABLED = False
    
    # Настройки для быстрой перезагрузки
    USE_RELOADER = True
    RELOADER_TYPE = 'auto'
    
    # Оптимизации для статических файлов
    STATIC_FOLDER = 'static'
    STATIC_URL_PATH = '/static'
    
    # Настройки для отладки
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Логирование для разработки
    LOG_LEVEL = 'INFO'
    
    # Отключаем ненужные функции для разработки
    BABEL_TRANSLATION_DIRECTORIES = 'babel/translations'
    
    # Максимальный размер загружаемого файла (5 МБ)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Настройки remember-cookie (Flask-Login) для разработки
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_SAMESITE = 'Lax'
