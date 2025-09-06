from flask import Blueprint, request, url_for, redirect, render_template, session, jsonify
from flask_login import login_required, login_user, logout_user, current_user

from ..models.users import Users
from ..models.activity_log import ActivityLog
from ..utils.activity_logger import log_activity

user = Blueprint('user', __name__)

# Простой словарь переводов (дублируем из main.py для простоты)
TRANSLATIONS = {
    'ru': {
        'Список объектов': 'Список объектов',
        'Календарь': 'Календарь',
        'Прочее': 'Прочее',
        'Пользователи': 'Пользователи',
        'Профиль': 'Профиль',
        'Выйти': 'Выйти',
        'Вход в систему': 'Вход в систему',
        'Войдите в аккаунт': 'Войдите в аккаунт',
        'Логин': 'Логин',
        'Пароль': 'Пароль',
        'Войти': 'Войти',
        'Все права защищены': 'Все права защищены',
        'Неверный логин или пароль': 'Неверный логин или пароль',
    },
    'en': {
        'Список объектов': 'Objects List',
        'Календарь': 'Calendar',
        'Прочее': 'Other',
        'Пользователи': 'Users',
        'Профиль': 'Profile',
        'Выйти': 'Sign Out',
        'Вход в систему': 'System Login',
        'Войдите в аккаунт': 'Sign in to your account',
        'Логин': 'Login',
        'Пароль': 'Password',
        'Войти': 'Sign In',
        'Все права защищены': 'All rights reserved',
        'Неверный логин или пароль': 'Invalid login or password',
    }
}

def gettext(text):
    """Простая функция перевода"""
    language = session.get('language', 'ru')
    return TRANSLATIONS.get(language, {}).get(text, text)

@user.context_processor
def inject_gettext():
    """Делает функцию gettext доступной в шаблонах"""
    return dict(gettext=gettext)

from werkzeug.security import check_password_hash

@user.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        user = Users.query.filter_by(login=login).first()
        # if user:
        if user and check_password_hash(user.password, password):
            # Обновляем информацию о входе пользователя
            from ..utils.timezone_utils import get_moscow_now
            user.last_login = get_moscow_now()
            user.mark_online()
            
            login_user(user)
            
            # Логируем успешный вход
            ActivityLog.log_action(
                user_id=user.userid,
                user_login=user.login,
                action="Вход в систему",
                description=f"Пользователь {user.login} успешно вошел в систему",
                ip_address=request.remote_addr,
                page_url=request.url,
                method=request.method
            )
            return redirect(url_for('objects.object_list'))
        else:
            # Логируем неудачную попытку входа
            ActivityLog.log_action(
                user_id=None,
                user_login=None,
                action="Неудачная попытка входа",
                description=f"Неудачная попытка входа с логином: {login}",
                ip_address=request.remote_addr,
                page_url=request.url,
                method=request.method
            )
            return render_template('main/sign-in.html', error=gettext("Неверный логин или пароль"))

    return render_template('main/sign-in.html')

@user.route('/logout')
def logout():
    # Логируем выход из системы
    if current_user.is_authenticated:
        # Отмечаем пользователя как не в сети
        current_user.mark_offline()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Выход из системы",
            description=f"Пользователь {current_user.login} вышел из системы",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
    logout_user()
    return redirect(url_for('user.login'))

@user.route('/set-timezone', methods=['POST'])
@login_required
def set_timezone():
    """Обновляет часовой пояс пользователя"""
    try:
        data = request.get_json()
        timezone = data.get('timezone')
        
        if not timezone:
            return jsonify({'success': False, 'error': 'Часовой пояс не указан'})
        
        # Проверяем, что часовой пояс валидный
        import pytz
        try:
            pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            return jsonify({'success': False, 'error': 'Неверный часовой пояс'})
        
        # Обновляем часовой пояс пользователя
        if current_user.set_timezone(timezone):
            # Логируем изменение часового пояса
            ActivityLog.log_action(
                user_id=current_user.userid,
                user_login=current_user.login,
                action="Изменение часового пояса",
                description=f"Пользователь {current_user.login} изменил часовой пояс на {timezone}",
                ip_address=request.remote_addr,
                page_url=request.url,
                method=request.method
            )
            
            return jsonify({
                'success': True, 
                'message': 'Часовой пояс обновлен',
                'timezone': timezone,
                'reload': True  # Предлагаем перезагрузить страницу
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка обновления часового пояса'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка сервера: {str(e)}'})

