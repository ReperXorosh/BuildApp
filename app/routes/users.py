from flask import Blueprint, request, url_for, redirect, render_template, session
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

