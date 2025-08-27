import os


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
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # Babel configuration
    LANGUAGES = ['ru', 'en']
    BABEL_DEFAULT_LOCALE = 'ru'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Moscow'
    BABEL_TRANSLATION_DIRECTORIES = 'babel/translations'
    
    # Upload folder for avatars
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'avatars')