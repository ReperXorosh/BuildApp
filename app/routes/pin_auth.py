from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from app.models.user_pin import UserPIN
from app.models.user import User
from app import db
import json

pin_auth_bp = Blueprint('pin_auth', __name__)

@pin_auth_bp.route('/pin/setup', methods=['GET', 'POST'])
@login_required
def setup_pin():
    """Настройка PIN-кода для пользователя"""
    if request.method == 'POST':
        data = request.get_json()
        pin = data.get('pin')
        confirm_pin = data.get('confirm_pin')
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            return jsonify({'success': False, 'message': 'PIN должен содержать 4 цифры'})
        
        if pin != confirm_pin:
            return jsonify({'success': False, 'message': 'PIN-коды не совпадают'})
        
        # Создаем или обновляем PIN для пользователя
        user_pin = UserPIN.query.filter_by(user_id=current_user.userid).first()
        if not user_pin:
            user_pin = UserPIN(user_id=current_user.userid)
            db.session.add(user_pin)
        
        user_pin.set_pin(pin)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'PIN-код успешно установлен'})
    
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
                    'redirect': url_for('main.dashboard')
                })
        
        return jsonify({'success': False, 'message': 'Неверный PIN-код'})
    
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
