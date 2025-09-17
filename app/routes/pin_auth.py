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
            # Создаем или обновляем PIN для пользователя
            print(f"Looking for existing PIN for user: {current_user.userid}")
            
            # Проверяем подключение к базе данных
            try:
                db.session.execute(text("SELECT 1"))
                print("Database connection OK")
            except Exception as db_e:
                print(f"Database connection error: {db_e}")
                return jsonify({'success': False, 'message': f'Ошибка подключения к базе данных: {str(db_e)}'})
            
            user_pin = UserPIN.query.filter_by(user_id=current_user.userid).first()
            if not user_pin:
                print("Creating new PIN record")
                user_pin = UserPIN(user_id=current_user.userid)
                db.session.add(user_pin)
            else:
                print("Updating existing PIN record")
            
            print(f"Setting PIN: {pin}")
            user_pin.set_pin(pin)
            print("Committing to database")
            db.session.commit()
            print("PIN saved successfully")
            
            return jsonify({'success': True, 'message': 'PIN-код успешно установлен'})
        except Exception as e:
            # Если таблица не существует, создаем её
            print(f"Creating user_pins table: {e}")
            try:
                # Создаем таблицу напрямую через SQL
                print("Creating user_pins table...")
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS user_pins (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
                    pin_hash VARCHAR(255) NOT NULL,
                    is_biometric_enabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    UNIQUE(user_id)
                );
                """
                print(f"Executing SQL: {create_table_sql}")
                with db.engine.connect() as conn:
                    conn.execute(text(create_table_sql))
                    conn.commit()
                print("Table created successfully")
                db.session.commit()
                
                # Повторяем попытку создания PIN
                user_pin = UserPIN(user_id=current_user.userid)
                db.session.add(user_pin)
                user_pin.set_pin(pin)
                db.session.commit()
                
                return jsonify({'success': True, 'message': 'PIN-код успешно установлен'})
            except Exception as e2:
                print(f"Error creating table or PIN: {e2}")
                return jsonify({'success': False, 'message': f'Ошибка при создании PIN: {str(e2)}'})
    
    return render_template('pin/setup_pin.html')

@pin_auth_bp.route('/pin/login', methods=['GET', 'POST'])
def pin_login():
    """Вход по PIN-коду"""
    if request.method == 'POST':
        data = request.get_json()
        pin = data.get('pin')
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            return jsonify({'success': False, 'message': 'Введите корректный PIN-код'})
        
        # Ищем пользователя по PIN-коду
        user_pins = UserPIN.query.all()
        for user_pin in user_pins:
            if user_pin.check_pin(pin):
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
    except Exception as e:
        # Если таблица не существует, перенаправляем на настройку
        print(f"PIN table not found: {e}")
        return redirect(url_for('pin_auth.setup_pin'))
    
    return render_template('pin/pin_login.html')

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
