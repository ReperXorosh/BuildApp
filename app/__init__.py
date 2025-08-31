import os
from datetime import datetime
import pytz

from flask import Flask, request, session
from .extensions import db, login_manager
from .config import Config
from .utils.timezone_utils import format_moscow_time

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
    
    # Регистрируем фильтры для московского времени
    @app.template_filter('moscow_time')
    def moscow_time_filter(dt):
        """Фильтр для отображения времени в московском часовом поясе"""
        return format_moscow_time(dt)
    
    @app.template_filter('moscow_date')
    def moscow_date_filter(dt):
        """Фильтр для отображения только даты в московском часовом поясе"""
        return format_moscow_time(dt, '%d.%m.%Y')
    
    @app.template_filter('moscow_time_short')
    def moscow_time_short_filter(dt):
        """Фильтр для отображения времени без секунд в московском часовом поясе"""
        return format_moscow_time(dt, '%d.%m.%Y %H:%M')
    
    @app.template_filter('moscow_time_relative')
    def moscow_time_relative_filter(dt):
        """Фильтр для относительного времени в московском часовом поясе"""
        if dt is None:
            return 'Не указано'
        
        from app.utils.timezone_utils import to_moscow_time, get_moscow_now
        moscow_time = to_moscow_time(dt)
        now = get_moscow_now()
        
        diff = now - moscow_time
        
        if diff.days > 0:
            return f"{diff.days} дн. назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ч. назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} мин. назад"
        else:
            return "Только что"
    
    # Контекстный процессор для автоматического добавления московского времени
    @app.context_processor
    def inject_moscow_time():
        """Добавляет московское время в контекст всех шаблонов"""
        from app.utils.timezone_utils import get_moscow_now
        return {
            'moscow_now': get_moscow_now(),
            'moscow_timezone': 'Europe/Moscow'
        }
    
    return app

