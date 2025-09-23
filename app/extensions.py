from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    from .models.users import Users
    # Flask-Login хранит user_id как строку; в БД первичный ключ UUID
    try:
        import uuid
        uuid_val = uuid.UUID(str(user_id))
    except Exception:
        # Если приведение не удалось, пробуем как есть
        uuid_val = user_id
    return Users.query.get(uuid_val)