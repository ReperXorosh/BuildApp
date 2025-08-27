import os

from flask import Flask, request, session
from .extensions import db, login_manager
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'user.login'
    # Убираем сообщение о необходимости входа в систему
    # login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    # login_manager.login_message_category = 'info'
    
    from .routes.main import main
    from .routes.users import user
    from .routes.activity_log import activity_log
    from .routes.supply import supply
    
    app.register_blueprint(main)
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(activity_log, url_prefix='/admin')
    app.register_blueprint(supply, url_prefix='/supply')
    
    return app

