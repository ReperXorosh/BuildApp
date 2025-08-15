from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view='user.login'

@login_manager.user_loader
def load_user(user_id):
    from .models.users import Users
    return Users.query.get(int(user_id))