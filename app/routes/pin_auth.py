from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from app.models.user_pin import UserPIN
from app.models.users import Users
from app import db
from sqlalchemy import text
import json

pin_auth_bp = Blueprint('pin_auth', __name__)

@pin_auth_bp.context_processor
def inject_gettext():
    """Делает функцию gettext доступной в шаблонах"""
    def gettext(text):
        return text
    return dict(gettext=gettext)

@pin_auth_bp.route('/pin/setup', methods=['GET', 'POST'])
@login_required
def setup_pin():
    """Настройка PIN-кода для пользователя"""
    if request.method == 'POST':
        print("=== PIN SETUP REQUEST ===")
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Raw data: {request.get_data()}")
        
        try:
            data = request.get_json()
            print(f"Parsed JSON data: {data}")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return jsonify({'success': False, 'message': 'Ошибка при обработке данных'})
        
        if not data:
            print("No data received")
            return jsonify({'success': False, 'message': 'Данные не получены'})
        
        pin = data.get('pin')
        confirm_pin = data.get('confirm_pin')
        
        print(f"PIN setup request:")
        print(f"  pin: '{pin}' (type: {type(pin)}, len: {len(pin) if pin else 'None'})")
        print(f"  confirm_pin: '{confirm_pin}' (type: {type(confirm_pin)}, len: {len(confirm_pin) if confirm_pin else 'None'})")
        print(f"  user_id: {current_user.userid}")
        
        if not pin:
            print("PIN is None or empty")
            return jsonify({'success': False, 'message': 'PIN не указан'})
        
        if not isinstance(pin, str):
            print(f"PIN is not string: {type(pin)}")
            return jsonify({'success': False, 'message': 'PIN должен быть строкой'})
        
        if len(pin) != 4 or not pin.isdigit():
            print(f"Invalid PIN format: '{pin}' (len: {len(pin)}, isdigit: {pin.isdigit()})")
            return jsonify({'success': False, 'message': 'PIN должен содержать 4 цифры'})
        
        if pin != confirm_pin:
            print(f"PIN mismatch: '{pin}' != '{confirm_pin}'")
            print(f"  pin repr: {repr(pin)}")
            print(f"  confirm_pin repr: {repr(confirm_pin)}")
            return jsonify({'success': False, 'message': 'PIN-коды не совпадают'})
        
        try:
            # Простое создание PIN без сложной логики
            print(f"Creating PIN for user: {current_user.userid}")
            
            # Удаляем существующий PIN если есть
            existing_pin = UserPIN.query.filter_by(user_id=str(current_user.userid)).first()
            if existing_pin:
                db.session.delete(existing_pin)
                db.session.commit()
                print("Deleted existing PIN")
            
            # Создаем новый PIN
            user_pin = UserPIN(user_id=str(current_user.userid))
            user_pin.set_pin(pin)
            db.session.add(user_pin)
            db.session.commit()
            print("PIN saved successfully")
            
            return jsonify({'success': True, 'message': 'PIN-код успешно установлен'})
            
        except Exception as e:
            print(f"Error saving PIN: {e}")
            # Пробуем создать таблицу и повторить
            try:
                print("Trying to create table and retry...")
                db.create_all()
                db.session.commit()
                
                # Повторяем попытку
                user_pin = UserPIN(user_id=str(current_user.userid))
                user_pin.set_pin(pin)
                db.session.add(user_pin)
                db.session.commit()
                print("PIN saved after table creation")
                
                return jsonify({'success': True, 'message': 'PIN-код успешно установлен'})
                
            except Exception as e2:
                print(f"Error after table creation: {e2}")
                return jsonify({'success': False, 'message': f'Ошибка при создании PIN: {str(e2)}'})
    
    return render_template('pin/setup_pin.html')

@pin_auth_bp.route('/pin/login', methods=['GET', 'POST'])
def pin_login():
    """Вход по PIN-коду"""
    if request.method == 'POST':
        data = request.get_json()
        pin = data.get('pin')
        biometric = data.get('biometric', False)
        
        if biometric:
            # Обработка биометрического входа
            # Пока что просто находим первого пользователя с включенной биометрией
            user_pin = UserPIN.query.filter_by(is_biometric_enabled=True).first()
            if user_pin:
                print(f"Biometric login for user: {user_pin.user_id}")
                login_user(user_pin.user)
                session['pin_authenticated'] = True
                return jsonify({
                    'success': True, 
                    'message': 'Успешный вход по Face ID',
                    'redirect': url_for('objects.object_list')
                })
            else:
                return jsonify({'success': False, 'message': 'Face ID не настроен'})
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            return jsonify({'success': False, 'message': 'Введите корректный PIN-код'})
        
        # Ищем пользователя по PIN-коду
        user_pins = UserPIN.query.all()
        print(f"Found {len(user_pins)} PIN records")
        for user_pin in user_pins:
            print(f"Checking PIN for user: {user_pin.user_id}")
            if user_pin.check_pin(pin):
                print(f"PIN match found for user: {user_pin.user_id}")
                # Входим в систему
                login_user(user_pin.user)
                session['pin_authenticated'] = True
                return jsonify({
                    'success': True, 
                    'message': 'Успешный вход',
                    'redirect': url_for('objects.object_list')
                })
        
        return jsonify({'success': False, 'message': 'Неверный PIN-код'})
    
    # Проверяем, есть ли настроенные PIN-коды
    try:
        pin_count = UserPIN.query.count()
        if pin_count == 0:
            # Если PIN-кодов нет, перенаправляем на настройку
            return redirect(url_for('pin_auth.setup_pin'))
        
        # Проверяем, есть ли пользователи с настроенным Face ID
        biometric_users = UserPIN.query.filter_by(is_biometric_enabled=True).count()
        print(f"Found {biometric_users} users with biometric enabled")
        
    except Exception as e:
        # Если таблица не существует, перенаправляем на настройку
        print(f"PIN table not found: {e}")
        return redirect(url_for('pin_auth.setup_pin'))
    
    return render_template('pin/pin_login.html', has_biometric_users=biometric_users > 0)

@pin_auth_bp.route('/pin/verify', methods=['POST'])
@login_required
def verify_pin():
    """Проверка PIN-кода для доступа к функциям"""
    data = request.get_json()
    pin = data.get('pin')
    
    if not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({'success': False, 'message': 'Введите корректный PIN-код'})
    
    user_pin = UserPIN.query.filter_by(user_id=current_user.userid).first()
    if not user_pin:
        return jsonify({'success': False, 'message': 'PIN-код не настроен'})
    
    if user_pin.check_pin(pin):
        session['pin_authenticated'] = True
        return jsonify({'success': True, 'message': 'PIN-код подтвержден'})
    
    return jsonify({'success': False, 'message': 'Неверный PIN-код'})

@pin_auth_bp.route('/pin/change', methods=['GET', 'POST'])
@login_required
def change_pin():
    """Изменение PIN-кода"""
    if request.method == 'POST':
        data = request.get_json()
        current_pin = data.get('current_pin')
        new_pin = data.get('new_pin')
        confirm_pin = data.get('confirm_pin')
        
        user_pin = UserPIN.query.filter_by(user_id=current_user.userid).first()
        if not user_pin:
            return jsonify({'success': False, 'message': 'PIN-код не настроен'})
        
        if not user_pin.check_pin(current_pin):
            return jsonify({'success': False, 'message': 'Неверный текущий PIN-код'})
        
        if not new_pin or len(new_pin) != 4 or not new_pin.isdigit():
            return jsonify({'success': False, 'message': 'Новый PIN должен содержать 4 цифры'})
        
        if new_pin != confirm_pin:
            return jsonify({'success': False, 'message': 'Новые PIN-коды не совпадают'})
        
        user_pin.set_pin(new_pin)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'PIN-код успешно изменен'})
    
    return render_template('pin/change_pin.html')

@pin_auth_bp.route('/pin/biometric/status', methods=['GET'])
@login_required
def biometric_status():
    """Получить статус биометрической аутентификации"""
    user_pin = UserPIN.query.filter_by(user_id=current_user.userid).first()
    if not user_pin:
        return jsonify({'enabled': False})
    
    return jsonify({'enabled': user_pin.is_biometric_enabled})

@pin_auth_bp.route('/pin/biometric/toggle', methods=['POST'])
@login_required
def toggle_biometric():
    """Включить/отключить биометрическую аутентификацию"""
    data = request.get_json()
    enabled = data.get('enabled', False)
    
    user_pin = UserPIN.query.filter_by(user_id=current_user.userid).first()
    if not user_pin:
        return jsonify({'success': False, 'message': 'Сначала настройте PIN-код'})
    
    if enabled:
        user_pin.enable_biometric()
    else:
        user_pin.disable_biometric()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Биометрическая аутентификация {"включена" if enabled else "отключена"}'})

@pin_auth_bp.route('/pin/logout', methods=['POST'])
@login_required
def pin_logout():
    """Выход из системы"""
    session.pop('pin_authenticated', None)
    logout_user()
    return jsonify({'success': True, 'redirect': url_for('pin_auth.pin_login')})
