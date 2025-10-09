import os
from datetime import datetime
import pytz

from flask import Flask, request, session
from .extensions import db, login_manager, migrate, cache
from .config import Config

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Выбираем конфигурацию в зависимости от режима
    if config_class is None:
        # Автоматически определяем конфигурацию
        if os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1':
            from .config_dev import DevelopmentConfig
            config_class = DevelopmentConfig
        else:
            config_class = Config
    
    app.config.from_object(config_class)
    
    # Настройка для работы за прокси
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1, x_prefix=1)
    
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    # Кэш (простая память по умолчанию; можно заменить на Redis через конфиг)
    cache.init_app(app, config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 60
    })
    
    login_manager.login_view = 'user.login'
    # Убираем сообщение о необходимости входа в систему
    # login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    # login_manager.login_message_category = 'info'
    
    # Кастомный обработчик для перенаправления на страницу входа
    @login_manager.unauthorized_handler
    def unauthorized():
        """Обработчик для неавторизованных пользователей"""
        from flask import redirect, url_for
        from .utils.mobile_detection import is_mobile_device
        
        # Определяем мобильное устройство
        if is_mobile_device():
            return redirect(url_for('user.login') + '?mobile=1')
        else:
            return redirect(url_for('user.login'))
    
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
    
    # Инициализация планировщика задач (только в production)
    if not app.debug:
        from .utils.scheduler import scheduler
        scheduler.init_app(app)
    
    # Регистрируем фильтры и контекстные процессоры
    _register_template_filters(app)
    _register_context_processors(app)
    
    return app


def _register_template_filters(app):
    """Регистрирует все фильтры шаблонов"""
    from .utils.timezone_utils import format_moscow_time, format_user_time, to_moscow_time, get_moscow_now, to_user_time, get_user_now
    import json
    
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
    
    @app.template_filter('user_time')
    def user_time_filter(dt):
        """Фильтр для отображения времени в часовом поясе пользователя"""
        return format_user_time(dt)
    
    @app.template_filter('user_date')
    def user_date_filter(dt):
        """Фильтр для отображения только даты в часовом поясе пользователя"""
        return format_user_time(dt, '%d.%m.%Y')
    
    @app.template_filter('user_time_short')
    def user_time_short_filter(dt):
        """Фильтр для отображения времени без секунд в часовом поясе пользователя"""
        return format_user_time(dt, '%d.%m.%Y %H:%M')
    
    @app.template_filter('user_time_relative')
    def user_time_relative_filter(dt):
        """Фильтр для относительного времени в часовом поясе пользователя"""
        if dt is None:
            return 'Не указано'
        
        user_time = to_user_time(dt)
        now = get_user_now()
        diff = now - user_time
        
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
    
    @app.template_filter('from_json')
    def from_json_filter(json_string):
        """Фильтр для парсинга JSON строки"""
        if json_string:
            try:
                return json.loads(json_string)
            except (json.JSONDecodeError, TypeError):
                return []
        return []


def _register_context_processors(app):
    """Регистрирует контекстные процессоры"""
    from .utils.timezone_utils import get_moscow_now, get_user_now, get_user_timezone
    
    @app.context_processor
    def inject_time_info():
        """Добавляет информацию о времени в контекст всех шаблонов"""
        return {
            'moscow_now': get_moscow_now(),
            'moscow_timezone': 'Europe/Moscow',
            'user_now': get_user_now(),
            'user_timezone': get_user_timezone()
        }

