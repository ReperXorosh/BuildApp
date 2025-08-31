import os
from datetime import datetime
import pytz

from flask import Flask, request, session
from .extensions import db, login_manager
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Настройка для работы за прокси
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1, x_prefix=1)
    
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
    from .routes.objects import objects_bp
    
    app.register_blueprint(main)
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(activity_log, url_prefix='/admin')
    app.register_blueprint(supply, url_prefix='/supply')
    app.register_blueprint(objects_bp, url_prefix='/objects')
    
    # Регистрируем фильтр для московского времени
    @app.template_filter('moscow_time')
    def moscow_time_filter(dt):
        """Фильтр для отображения времени в московском часовом поясе"""
        if dt is None:
            return 'Не указано'
        
        moscow_tz = pytz.timezone('Europe/Moscow')
        
        # Если время без часового пояса, считаем его UTC и конвертируем в московское
        if dt.tzinfo is None:
            # Предполагаем, что время в UTC (как сохраняется в базе данных)
            utc_tz = pytz.UTC
            dt = utc_tz.localize(dt)
            dt = dt.astimezone(moscow_tz)
        else:
            # Если время уже с часовым поясом, конвертируем в московское
            dt = dt.astimezone(moscow_tz)
        
        return dt.strftime('%d.%m.%Y %H:%M:%S')
    
    return app

