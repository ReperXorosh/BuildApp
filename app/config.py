import os
from datetime import timedelta


class Config(object):
    USER = os.environ.get('POSTGRES_USER', 'sankficeba')
    PASSWORD = os.environ.get("POSTGRES_PASSWORD", '12345678')
    HOST = os.environ.get("POSTGRES_HOST", "localhost")
    PORT = os.environ.get("POSTGRES_PORT", '54321')
    DATABASE = os.environ.get("POSTGRES_DB", 'mydb')

    # Use SQLite for local development by default
    if os.environ.get('USE_POSTGRES') == 'true':
        SQLALCHEMY_DATABASE_URI = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    
    # SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SECRET_KEY = "aaafafhjahfjdhsafjkhsjvhajskhvjkshajhdjkhshk"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # Настройки для работы за прокси
    PREFERRED_URL_SCHEME = 'http'
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_FOR = True
    USE_X_FORWARDED_PROTO = True
    
    # Настройки сессий
    SESSION_COOKIE_SECURE = False  # Установить True только для HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Babel configuration
    LANGUAGES = ['ru', 'en']
    BABEL_DEFAULT_LOCALE = 'ru'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Moscow'
    BABEL_TRANSLATION_DIRECTORIES = 'babel/translations'
    
    # Upload folder for avatars
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'avatars')
    
    # Максимальный размер загружаемого файла (5 МБ)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
    # Оптимизации для разработки
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False
    
    # Кэширование для ускорения
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Отключаем кэширование в разработке

    # Настройки remember-cookie (Flask-Login)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False  # В проде на HTTPS установить True
    REMEMBER_COOKIE_SAMESITE = 'Lax'