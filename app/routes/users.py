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
        login = request.form['login'].strip()  # Удаляем пробелы в начале и конце
        password = request.form['password'].strip()  # Удаляем пробелы в начале и конце

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
            
            # Проверяем, нужно ли предложить настройку PIN-кода
            from ..utils.mobile_detection import is_mobile_device
            
            is_mobile = is_mobile_device()
            
            # Если это мобильное устройство, проверяем наличие PIN-кода
            if is_mobile:
                try:
                    from ..models.user_pin import UserPIN
                    user_pin = UserPIN.query.filter_by(user_id=user.userid).first()
                    
                    # Если PIN не настроен, предлагаем настройку
                    if not user_pin:
                        return redirect(url_for('pin_auth.setup_pin'))
                except Exception as e:
                    # Если таблица не существует, создаем её и предлагаем настройку PIN
                    print(f"PIN table not found, creating and offering setup: {e}")
                    try:
                        from .. import db
                        db.create_all()
                        db.session.commit()
                    except Exception as e2:
                        print(f"Error creating table: {e2}")
                    
                    return redirect(url_for('pin_auth.setup_pin'))
            
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
            # Определяем, нужно ли использовать мобильный шаблон
            from ..utils.mobile_detection import is_mobile_device
            # Проверяем параметр mobile=1 или определяем по User-Agent
            is_mobile = request.args.get('mobile') == '1' or is_mobile_device()
            if is_mobile:
                return render_template('main/mobile_sign_in.html', error=gettext("Неверный логин или пароль"))
            else:
                return render_template('main/sign-in.html', error=gettext("Неверный логин или пароль"))

    # Определяем, нужно ли использовать мобильный шаблон
    from ..utils.mobile_detection import is_mobile_device
    # Проверяем параметр mobile=1 или определяем по User-Agent
    mobile_param = request.args.get('mobile') == '1'
    device_mobile = is_mobile_device()
    is_mobile = mobile_param or device_mobile
    
    print(f"DEBUG: Параметр mobile=1: {mobile_param}, Устройство мобильное: {device_mobile}, Итоговое решение: {is_mobile}")
    
    if is_mobile:
        print(f"DEBUG: Отображение мобильной страницы входа")
        return render_template('main/mobile_sign_in.html')
    else:
        print(f"DEBUG: Отображение десктопной страницы входа")
        return render_template('main/sign-in.html')

@user.route('/logout')
def logout():
    # Определяем мобильное устройство ДО выхода из системы
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device()
    
    # Логируем выход из системы
    if current_user.is_authenticated:
        # Отмечаем пользователя как не в сети
        current_user.mark_offline()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Выход из системы",
            description=f"Пользователь {current_user.login} вышел из системы (мобильное устройство: {is_mobile})",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
    logout_user()
    
    # Перенаправляем на правильную страницу входа
    if is_mobile:
        print(f"DEBUG: Перенаправление на мобильную страницу входа")
        return redirect(url_for('user.login') + '?mobile=1')
    else:
        print(f"DEBUG: Перенаправление на десктопную страницу входа")
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

