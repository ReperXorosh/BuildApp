from functools import wraps
from flask import request, current_app
from flask_login import current_user
from app.models.activity_log import ActivityLog

def log_activity(action="", description=""):
    """Декоратор для логирования действий пользователей"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Выполняем оригинальную функцию
            result = f(*args, **kwargs)
            
            # Логируем действие
            try:
                ActivityLog.log_action(
                    user=current_user if current_user.is_authenticated else None,
                    action=action,
                    description=description,
                    request=request
                )
            except Exception as e:
                # Не прерываем выполнение функции из-за ошибки логирования
                current_app.logger.error(f"Ошибка логирования действия: {e}")
            
            return result
        return decorated_function
    return decorator

def log_page_view(page_name=""):
    """Декоратор для логирования просмотра страниц"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Выполняем оригинальную функцию
            result = f(*args, **kwargs)
            
            # Логируем просмотр страницы
            try:
                user_info = current_user.login if current_user.is_authenticated else "Неавторизованный пользователь"
                ActivityLog.log_action(
                    user=current_user if current_user.is_authenticated else None,
                    action="Просмотр страницы",
                    description=f"Пользователь {user_info} просмотрел страницу: {page_name}",
                    request=request
                )
            except Exception as e:
                current_app.logger.error(f"Ошибка логирования просмотра страницы: {e}")
            
            return result
        return decorated_function
    return decorator

def log_user_action(action="", description_template=""):
    """Декоратор для логирования действий с пользователями"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Выполняем оригинальную функцию
            result = f(*args, **kwargs)
            
            # Логируем действие с пользователем
            try:
                user_info = current_user.login if current_user.is_authenticated else "Неавторизованный пользователь"
                description = description_template.format(
                    user=user_info,
                    **kwargs
                )
                
                ActivityLog.log_action(
                    user=current_user if current_user.is_authenticated else None,
                    action=action,
                    description=description,
                    request=request
                )
            except Exception as e:
                current_app.logger.error(f"Ошибка логирования действия пользователя: {e}")
            
            return result
        return decorated_function
    return decorator

# Предопределенные действия для часто используемых операций
def log_login():
    """Логирование входа в систему"""
    return log_activity(
        action="Вход в систему",
        description="Пользователь вошел в систему"
    )

def log_logout():
    """Логирование выхода из системы"""
    return log_activity(
        action="Выход из системы", 
        description="Пользователь вышел из системы"
    )

def log_user_creation():
    """Логирование создания пользователя"""
    return log_user_action(
        action="Создание пользователя",
        description_template="Пользователь {user} создал нового пользователя"
    )

def log_user_edit():
    """Логирование редактирования пользователя"""
    return log_user_action(
        action="Редактирование пользователя",
        description_template="Пользователь {user} отредактировал данные пользователя"
    )

def log_user_deletion():
    """Логирование удаления пользователя"""
    return log_user_action(
        action="Удаление пользователя",
        description_template="Пользователь {user} удалил пользователя"
    )

def log_profile_update():
    """Логирование обновления профиля"""
    return log_activity(
        action="Обновление профиля",
        description="Пользователь обновил свой профиль"
    )

def log_password_change():
    """Логирование смены пароля"""
    return log_activity(
        action="Смена пароля",
        description="Пользователь сменил пароль"
    )

def log_avatar_upload():
    """Логирование загрузки аватара"""
    return log_activity(
        action="Загрузка аватара",
        description="Пользователь загрузил новый аватар"
    )

