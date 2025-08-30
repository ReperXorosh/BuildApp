import os
from uuid import uuid4

from flask import Blueprint, render_template, session, redirect, url_for, request, current_app, flash
from ..extensions import db
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db

main = Blueprint('main', __name__)

# Простой словарь переводов
TRANSLATIONS = {
    'ru': {
        'Список объектов': 'Список объектов',
        'Календарь': 'Календарь',
        'Прочее': 'Прочее',
        'Пользователи': 'Пользователи',
        'Профиль': 'Профиль',
        'Отчёты': 'Отчёты',
        'Выйти': 'Выйти',
        'Вход в систему': 'Вход в систему',
        'Войдите в аккаунт': 'Войдите в аккаунт',
        'Логин': 'Логин',
        'Пароль': 'Пароль',
        'Войти': 'Войти',
        'Все права защищены': 'Все права защищены',
    },
    'en': {
        'Список объектов': 'Objects List',
        'Календарь': 'Calendar',
        'Прочее': 'Other',
        'Пользователи': 'Users',
        'Профиль': 'Profile',
        'Отчёты': 'Reports',
        'Выйти': 'Sign Out',
        'Вход в систему': 'System Login',
        'Войдите в аккаунт': 'Sign in to your account',
        'Логин': 'Login',
        'Пароль': 'Password',
        'Войти': 'Sign In',
        'Все права защищены': 'All rights reserved',
    }
}

def gettext(text):
    """Простая функция перевода"""
    language = session.get('language', 'ru')
    return TRANSLATIONS.get(language, {}).get(text, text)

@main.context_processor
def inject_gettext():
    """Делает функцию gettext доступной в шаблонах"""
    return dict(gettext=gettext)

@main.route('/language/<language>')
def set_language(language):
    session['language'] = language
    
    # Логируем смену языка
    if current_user.is_authenticated:
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Смена языка",
            description=f"Пользователь {current_user.login} сменил язык интерфейса на {language}",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
    else:
        ActivityLog.log_action(
            user_id=None,
            user_login=None,
            action="Смена языка",
            description=f"Неавторизованный пользователь сменил язык интерфейса на {language}",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
    
    return redirect(request.referrer or url_for('objects.object_list'))

@main.route('/log-theme-change', methods=['POST'])
@login_required
def log_theme_change():
    """Логирует смену темы интерфейса"""
    data = request.get_json()
    new_theme = data.get('theme', 'unknown')
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Смена темы",
        description=f"Пользователь {current_user.login} сменил тему интерфейса на {new_theme}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return jsonify({'status': 'success'})

@main.route('/sign-in')
@main.route('/')
def sign_in():
    return render_template('main/sign-in.html')

from ..models.users import Users
from ..models.activity_log import ActivityLog
from ..models.objects import Object, Report

import re

def validate_russian_phone(phone_number):
    """Валидация российского номера телефона"""
    if not phone_number:
        return True  # Пустой номер разрешен
    
    # Убираем все не-цифры
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Если номер начинается с 7 и имеет 11 цифр, убираем первую 7
    if len(digits_only) == 11 and digits_only.startswith('7'):
        digits_only = digits_only[1:]
    
    # Если номер начинается с 7 и имеет 10 цифр, убираем первую 7
    if len(digits_only) == 10 and digits_only.startswith('7'):
        digits_only = digits_only[1:]
    
    # Проверяем, что номер содержит ровно 10 цифр (без учета +7)
    if len(digits_only) != 10:
        return False
    
    # Проверяем, что номер начинается с 9 (для мобильных) или 4, 8 (для городских)
    first_digit = digits_only[0]
    if first_digit not in ['9', '4', '8']:
        return False
    
    return True

def clean_phone_for_edit(phone_number):
    """Очищает номер телефона для отображения в форме редактирования"""
    if not phone_number:
        return ""
    
    # Убираем все не-цифры
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Если номер начинается с 7 и имеет 11 цифр, убираем первую 7
    if len(digits_only) == 11 and digits_only.startswith('7'):
        digits_only = digits_only[1:]
    
    # Если номер начинается с 7 и имеет 10 цифр, убираем первую 7
    if len(digits_only) == 10 and digits_only.startswith('7'):
        digits_only = digits_only[1:]
    
    # Возвращаем только если есть ровно 10 цифр
    if len(digits_only) == 10:
        return digits_only
    else:
        return ""

def format_phone_for_display(phone_number):
    """Форматирует номер телефона для отображения"""
    if not phone_number:
        return ""
    
    # Проверяем, если номер уже отформатирован (содержит +7 и скобки)
    if phone_number.startswith('+7 (') and ')' in phone_number:
        return phone_number
    
    # Убираем все не-цифры
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Если номер начинается с 7 и имеет 11 цифр, убираем первую 7
    if len(digits_only) == 11 and digits_only.startswith('7'):
        digits_only = digits_only[1:]
    
    # Если номер начинается с 7 и имеет 10 цифр, убираем первую 7
    if len(digits_only) == 10 and digits_only.startswith('7'):
        digits_only = digits_only[1:]
    
    if len(digits_only) == 9:
        formatted = f"+7 ({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:8]}-{digits_only[8:9]}"
        return formatted
    
    if len(digits_only) == 10:
        formatted = f"+7 ({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:8]}-{digits_only[8:10]}"
        return formatted
    
    return phone_number




@main.route('/calendar')
@login_required
def calendar():
    # Логируем просмотр страницы календаря
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр календаря",
        description=f"Пользователь {current_user.login} открыл страницу календаря",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    return render_template('main/calendar.html')

@main.route('/others')
@login_required
def others():
    # Логируем просмотр страницы "Другое"
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр страницы 'Другое'",
        description=f"Пользователь {current_user.login} открыл страницу 'Другое'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    return render_template('main/others.html')

@main.route('/users')
@login_required
def users():
    # Проверяем права администратора (Инженер ПТО)
    if current_user.role != 'Инженер ПТО':
        flash('У вас нет прав для просмотра пользователей', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Логируем просмотр страницы пользователей
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр страницы",
        description=f"Пользователь {current_user.login} просмотрел страницу управления пользователями",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Получаем всех пользователей из базы данных
    all_users = Users.query.all()
    return render_template('main/users.html', users=all_users)

@main.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    # Проверяем права администратора (Инженер ПТО)
    if current_user.role != 'Инженер ПТО':
        flash('У вас нет прав для добавления пользователей', 'error')
        return redirect(url_for('main.users'))
    
    # Логируем открытие страницы добавления пользователя
    if request.method == 'GET':
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Открытие страницы добавления пользователя",
            description=f"Пользователь {current_user.login} открыл страницу добавления нового пользователя",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
    if request.method == 'POST':
        # Получаем данные из формы
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '').strip()
        firstname = request.form.get('firstname', '').strip()
        secondname = request.form.get('secondname', '').strip()
        thirdname = request.form.get('thirdname', '').strip()
        phonenumber = request.form.get('phonenumber', '').strip()
        role = request.form.get('role', '').strip()
        
        # Валидация обязательных полей
        errors = []
        if not login:
            errors.append('Логин обязателен для заполнения')
        if not password:
            errors.append('Пароль обязателен для заполнения')
        if not role:
            errors.append('Роль обязательна для выбора')
        
        if errors:
            flash('Ошибки в форме: ' + ', '.join(errors), 'error')
            return render_template('main/add_user.html', 
                                 form_data={
                                     'login': login,
                                     'firstname': firstname,
                                     'secondname': secondname,
                                     'thirdname': thirdname,
                                     'phonenumber': phonenumber,
                                     'role': role
                                 })
        
        # Валидация номера телефона
        if phonenumber and not validate_russian_phone(phonenumber):
            flash('Некорректный номер телефона. Используйте формат +7 (999) 123-45-67. Номер должен содержать 10 цифр и начинаться с 9, 4 или 8.', 'error')
            return render_template('main/add_user.html', 
                                 form_data={
                                     'login': login,
                                     'firstname': firstname,
                                     'secondname': secondname,
                                     'thirdname': thirdname,
                                     'phonenumber': phonenumber,
                                     'role': role
                                 })
        
        # Сохраняем номер телефона в базу данных (ровно 10 цифр без +7)
        if phonenumber:
            # Убираем все не-цифры
            digits_only = re.sub(r'\D', '', phonenumber)
            # Убираем первую 7 если она есть
            if len(digits_only) >= 10 and digits_only.startswith('7'):
                digits_only = digits_only[1:]
            # Сохраняем только если есть ровно 10 цифр
            if len(digits_only) == 10:
                phonenumber = digits_only
            else:
                phonenumber = ""  # Неверный формат
        
        # Проверяем, что пользователь с таким логином не существует
        existing_user = Users.query.filter_by(login=login).first()
        if existing_user:
            flash('Пользователь с таким логином уже существует', 'error')
            return render_template('main/add_user.html', 
                                 form_data={
                                     'login': login,
                                     'firstname': firstname,
                                     'secondname': secondname,
                                     'thirdname': thirdname,
                                     'phonenumber': phonenumber,
                                     'role': role
                                 })
        
        # Создаем нового пользователя
        new_user = Users(
            login=login,
            password=password,
            firstname=firstname,
            secondname=secondname,
            thirdname=thirdname,
            phonenumber=phonenumber,
            role=role
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Проверяем, была ли ошибка связана с дублированием логина
            if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e).lower():
                flash('Пользователь с таким логином уже существует', 'error')
            else:
                flash('Ошибка при создании пользователя. Попробуйте еще раз.', 'error')
            return render_template('main/add_user.html', 
                                 form_data={
                                     'login': login,
                                     'firstname': firstname,
                                     'secondname': secondname,
                                     'thirdname': thirdname,
                                     'phonenumber': phonenumber,
                                     'role': role
                                 })
        
        # Обрабатываем загрузку аватара
        file = request.files.get('avatar')
        edited_image_data = request.form.get('edited_avatar')
        
        if file and file.filename and allowed_file(file.filename):
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)

            ext = '.' + file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"{new_user.userid}_{uuid4().hex}{ext}")
            fullpath = os.path.join(upload_dir, filename)
            
            # Если есть отредактированное изображение, сохраняем его
            if edited_image_data and edited_image_data.startswith('data:image'):
                import base64
                # Убираем префикс data:image/jpeg;base64,
                image_data = edited_image_data.split(',')[1]
                with open(fullpath, 'wb') as f:
                    f.write(base64.b64decode(image_data))
            else:
                # Сохраняем оригинальный файл
                file.save(fullpath)

            new_user.avatar = filename
            db.session.commit()
        
        # Логируем создание пользователя
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Создание пользователя",
            description=f"Администратор {current_user.login} создал нового пользователя {new_user.login} (ID: {new_user.userid})",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Пользователь успешно добавлен', 'success')
        return redirect(url_for('main.users'))
    
    return render_template('main/add_user.html')


@main.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Проверяем права администратора (Инженер ПТО)
    if current_user.role != 'Инженер ПТО':
        flash('У вас нет прав для редактирования пользователей', 'error')
        return redirect(url_for('main.users'))
    
    user = Users.query.get(user_id)
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('main.users'))
    
    # Логируем открытие страницы редактирования пользователя
    if request.method == 'GET':
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Открытие страницы редактирования пользователя",
            description=f"Пользователь {current_user.login} открыл страницу редактирования пользователя {user.login}",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
    
    if request.method == 'POST':
        # Получаем данные из формы
        login = request.form.get('login')
        firstname = request.form.get('firstname')
        secondname = request.form.get('secondname')
        thirdname = request.form.get('thirdname')
        phonenumber = request.form.get('phonenumber')
        role = request.form.get('role')
        password = request.form.get('password')
        
        # Валидация номера телефона
        if phonenumber and not validate_russian_phone(phonenumber):
            flash('Некорректный номер телефона. Используйте формат +7 (999) 123-45-67', 'error')
            return redirect(url_for('main.edit_user', user_id=user_id))
        
        # Сохраняем номер телефона в базу данных (ровно 10 цифр без +7)
        if phonenumber:
            # Убираем все не-цифры
            digits_only = re.sub(r'\D', '', phonenumber)
            # Убираем первую 7 если она есть
            if len(digits_only) >= 10 and digits_only.startswith('7'):
                digits_only = digits_only[1:]
            # Сохраняем только если есть ровно 10 цифр
            if len(digits_only) == 10:
                phonenumber = digits_only
            else:
                phonenumber = ""  # Неверный формат
        
        # Проверяем, что логин не занят другим пользователем
        existing_user = Users.query.filter_by(login=login).first()
        if existing_user and str(existing_user.userid) != str(user_id):
            flash('Пользователь с таким логином уже существует', 'error')
            return redirect(url_for('main.edit_user', user_id=user_id))
        
        # Обновляем данные пользователя
        user.login = login
        user.firstname = firstname
        user.secondname = secondname
        user.thirdname = thirdname
        user.phonenumber = phonenumber
        user.role = role
        
        # Обновляем пароль только если он указан
        if password:
            user.password = password
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Проверяем, была ли ошибка связана с дублированием логина
            if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e).lower():
                flash('Пользователь с таким логином уже существует', 'error')
            else:
                flash('Ошибка при обновлении пользователя. Попробуйте еще раз.', 'error')
            return redirect(url_for('main.edit_user', user_id=user_id))
        
        # Обрабатываем загрузку аватара
        file = request.files.get('avatar')
        edited_image_data = request.form.get('edited_avatar')
        
        if file and file.filename and allowed_file(file.filename):
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)

            ext = '.' + file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"{user.userid}_{uuid4().hex}{ext}")
            fullpath = os.path.join(upload_dir, filename)
            
            # Если есть отредактированное изображение, сохраняем его
            if edited_image_data and edited_image_data.startswith('data:image'):
                import base64
                # Убираем префикс data:image/jpeg;base64,
                image_data = edited_image_data.split(',')[1]
                with open(fullpath, 'wb') as f:
                    f.write(base64.b64decode(image_data))
            else:
                # Сохраняем оригинальный файл
                file.save(fullpath)

            # Удаляем старый аватар, если он есть
            if user.avatar:
                old = os.path.join(upload_dir, user.avatar)
                try:
                    if os.path.exists(old):
                        os.remove(old)
                except Exception:
                    pass

            user.avatar = filename
        
        # Логируем действие редактирования пользователя
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Редактирование пользователя",
            description=f"Администратор {current_user.login} отредактировал пользователя {user.login} (ID: {user.userid})",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        db.session.commit()
        flash('Пользователь успешно обновлен', 'success')
        return redirect(url_for('main.users'))
    
    # Очищаем номер телефона для отображения в форме редактирования
    clean_phone = clean_phone_for_edit(user.phonenumber) if user.phonenumber else ""
    return render_template('main/edit_user.html', user=user, clean_phone=clean_phone)


@main.route('/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Проверяем права администратора (Инженер ПТО)
    if current_user.role != 'Инженер ПТО':
        flash('У вас нет прав для удаления пользователей', 'error')
        return redirect(url_for('main.users'))
    
    # Нельзя удалить самого себя
    if user_id == current_user.userid:
        flash('Вы не можете удалить свой собственный аккаунт', 'error')
        return redirect(url_for('main.users'))
    
    user = Users.query.get(user_id)
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('main.users'))
    
    # Удаляем аватар пользователя, если он есть
    if user.avatar:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        avatar_path = os.path.join(upload_dir, user.avatar)
        try:
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
        except Exception:
            pass
    
    # Логируем действие удаления пользователя
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Удаление пользователя",
        description=f"Администратор {current_user.login} удалил пользователя {user.login} (ID: {user.userid})",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Удаляем пользователя из базы данных
    db.session.delete(user)
    db.session.commit()
    
    flash('Пользователь успешно удален', 'success')
    return redirect(url_for('main.users'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Логируем открытие страницы профиля
    if request.method == 'GET':
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Открытие страницы профиля",
            description=f"Пользователь {current_user.login} открыл страницу своего профиля",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
    
    if request.method == 'POST':
        if not current_user.firstname:
            current_user.firstname = request.form.get('firstname')
        if not current_user.secondname:
            current_user.secondname = request.form.get('secondname')
        if not current_user.thirdname:
            current_user.thirdname = request.form.get('thirdname')
        current_user.phonenumber = request.form.get('phonenumber') or current_user.phonenumber
        current_user.role = request.form.get('role') or current_user.role


        file = request.files.get('avatar')
        if file and file.filename and allowed_file(file.filename):
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)

            ext = '.' + file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"{current_user.userid}_{uuid4().hex}{ext}")
            fullpath = os.path.join(upload_dir, filename)
            file.save(fullpath)


            if current_user.avatar:
                old = os.path.join(upload_dir, current_user.avatar)
                try:
                    if os.path.exists(old):
                        os.remove(old)
                except Exception:
                    pass

            current_user.avatar = filename

        # Логируем обновление профиля
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Обновление профиля",
            description=f"Пользователь {current_user.login} обновил свой профиль",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        db.session.commit()
        flash('Профиль обновлён', 'success')
        return redirect(url_for('main.profile'))
    return render_template('main/profile.html')

@main.route('/reports')
@login_required
def reports():
    # Проверяем, что пользователь не является снабженцем
    if current_user.role == 'Снабженец':
        flash('У вас нет прав для просмотра отчётов', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Получаем список всех объектов
    objects = Object.query.filter_by(status='active').order_by(Object.name).all()
    
    # Логируем просмотр страницы отчётов
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр отчётов",
        description=f"Пользователь {current_user.login} открыл страницу отчётов",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('main/reports.html', objects=objects)

@main.route('/reports/object/<object_id>')
@login_required
def object_reports(object_id):
    # Проверяем, что пользователь не является снабженцем
    if current_user.role == 'Снабженец':
        flash('У вас нет прав для просмотра отчётов', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Получаем объект и его отчёты
    object_obj = Object.query.get_or_404(object_id)
    reports = Report.query.filter_by(object_id=object_id).order_by(Report.report_date.desc()).all()
    
    # Группируем отчёты по дате
    reports_by_date = {}
    for report in reports:
        date_key = report.report_date.strftime('%Y-%m-%d')
        if date_key not in reports_by_date:
            reports_by_date[date_key] = []
        reports_by_date[date_key].append(report)
    
    # Логируем просмотр отчётов объекта
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр отчётов объекта",
        description=f"Пользователь {current_user.login} просматривает отчёты объекта {object_obj.name}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('main/object_reports.html', 
                         object_obj=object_obj, 
                         reports_by_date=reports_by_date)

@main.route('/reports/calendar')
@login_required
def reports_calendar():
    # Проверяем, что пользователь не является снабженцем
    if current_user.role == 'Снабженец':
        flash('У вас нет прав для просмотра отчётов', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Получаем все отчёты с датами
    reports = Report.query.order_by(Report.report_date).all()
    
    # Группируем объекты по датам отчётов
    objects_by_date = {}
    for report in reports:
        date_key = report.report_date.strftime('%Y-%m-%d')
        if date_key not in objects_by_date:
            objects_by_date[date_key] = []
        
        # Добавляем объект, если его еще нет в списке для этой даты
        object_obj = report.object
        if not any(obj.id == object_obj.id for obj in objects_by_date[date_key]):
            objects_by_date[date_key].append(object_obj)
    
    # Логируем просмотр календаря отчётов
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр календаря отчётов",
        description=f"Пользователь {current_user.login} открыл календарь отчётов",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('main/reports_calendar.html', objects_by_date=objects_by_date)

@main.route('/reports/date/<date>')
@login_required
def reports_by_date(date):
    # Проверяем, что пользователь не является снабженцем
    if current_user.role == 'Снабженец':
        flash('У вас нет прав для просмотра отчётов', 'error')
        return redirect(url_for('objects.object_list'))
    
    try:
        # Парсим дату
        from datetime import datetime
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Получаем отчёты за эту дату
        reports = Report.query.filter_by(report_date=report_date).all()
        
        # Группируем объекты с отчётами
        objects_with_reports = {}
        for report in reports:
            object_obj = report.object
            if object_obj.id not in objects_with_reports:
                objects_with_reports[object_obj.id] = {
                    'object': object_obj,
                    'reports': []
                }
            objects_with_reports[object_obj.id]['reports'].append(report)
        
        # Логируем просмотр отчётов по дате
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Просмотр отчётов по дате",
            description=f"Пользователь {current_user.login} просматривает отчёты за {date}",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        return render_template('main/reports_by_date.html', 
                             date=report_date,
                             objects_with_reports=objects_with_reports)
    
    except ValueError:
        flash('Неверный формат даты', 'error')
        return redirect(url_for('main.reports'))

@main.route('/reports/object/<object_id>/date/<date>')
@login_required
def object_report_by_date(object_id, date):
    # Проверяем, что пользователь не является снабженцем
    if current_user.role == 'Снабженец':
        flash('У вас нет прав для просмотра отчётов', 'error')
        return redirect(url_for('objects.object_list'))
    
    try:
        # Парсим дату
        from datetime import datetime
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Получаем объект и отчёты за эту дату
        object_obj = Object.query.get_or_404(object_id)
        reports = Report.query.filter_by(
            object_id=object_id, 
            report_date=report_date
        ).order_by(Report.created_at).all()
        
        # Логируем просмотр отчёта объекта по дате
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Просмотр отчёта объекта по дате",
            description=f"Пользователь {current_user.login} просматривает отчёты объекта {object_obj.name} за {date}",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        return render_template('main/object_report_by_date.html', 
                             object_obj=object_obj,
                             date=report_date,
                             reports=reports)
    
    except ValueError:
        flash('Неверный формат даты', 'error')
        return redirect(url_for('main.object_reports', object_id=object_id))

# @main.route('/layout')
# def layout():
#     return render_template('main/layout.html')