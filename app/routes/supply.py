from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.supply import Material, Equipment, SupplyOrder, SupplyOrderItem
from app.models.activity_log import ActivityLog
from app.extensions import db
from app.utils.mobile_detection import is_mobile_device
from datetime import datetime, timedelta, timezone

supply = Blueprint('supply', __name__)

@supply.context_processor
def inject_gettext():
    """Внедряет функцию gettext в контекст шаблонов"""
    def gettext(text):
        return text
    return dict(gettext=gettext)

def is_supplier_or_admin():
    """Проверяет, имеет ли пользователь права снабженца или администратора"""
    return current_user.is_authenticated and current_user.role in ['Снабженец', 'Инженер ПТО']

@supply.route('/supply')
@login_required
def supply_dashboard():
    """Главная страница системы снабжения"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к системе снабжения', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Логируем просмотр страницы
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр системы снабжения",
        description="Открыта главная страница системы снабжения",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Получаем статистику
    materials_count = Material.query.count()
    equipment_count = Equipment.query.count()
    pending_orders = SupplyOrder.query.filter_by(status='pending').count()
    delivered_orders = SupplyOrder.query.filter_by(status='delivered').count()
    
    # Получаем материалы с низким запасом
    low_stock_materials = Material.query.filter(
        Material.current_quantity <= Material.min_quantity
    ).limit(5).all()
    
    # Получаем последние заказы
    recent_orders = SupplyOrder.query.order_by(
        SupplyOrder.created_at.desc()
    ).limit(5).all()
    
    # Проверяем мобильное устройство
    if is_mobile_device():
        return render_template('supply/mobile_dashboard.html',
                             materials_count=materials_count,
                             equipment_count=equipment_count,
                             pending_orders=pending_orders,
                             delivered_orders=delivered_orders,
                             low_stock_materials=low_stock_materials,
                             recent_orders=recent_orders)
    
    return render_template('supply/dashboard.html',
                         materials_count=materials_count,
                         equipment_count=equipment_count,
                         pending_orders=pending_orders,
                         delivered_orders=delivered_orders,
                         low_stock_materials=low_stock_materials,
                         recent_orders=recent_orders)

@supply.route('/supply/materials')
@login_required
def materials_list():
    """Список материалов"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для просмотра материалов', 'error')
        return redirect(url_for('objects.object_list'))
    
    materials = Material.query.order_by(Material.name).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр списка материалов",
        description=f"Просмотрено материалов: {len(materials)}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('supply/materials.html', materials=materials)

@supply.route('/supply/equipment')
@login_required
def equipment_list():
    """Список техники"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для просмотра техники', 'error')
        return redirect(url_for('objects.object_list'))
    
    equipment = Equipment.query.order_by(Equipment.name).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр списка техники",
        description=f"Просмотрено единиц техники: {len(equipment)}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('supply/equipment.html', equipment=equipment)

@supply.route('/supply/orders')
@login_required
def orders_list():
    """Список заказов на снабжение"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для просмотра заказов', 'error')
        return redirect(url_for('objects.object_list'))
    
    orders = SupplyOrder.query.order_by(SupplyOrder.created_at.desc()).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр списка заказов",
        description=f"Просмотрено заказов: {len(orders)}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('supply/orders.html', orders=orders)

# API маршруты для AJAX запросов
@supply.route('/api/supply/materials', methods=['GET'])
@login_required
def api_materials():
    """API для получения списка материалов"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    materials = Material.query.all()
    return jsonify([material.to_dict() for material in materials])

@supply.route('/api/supply/equipment', methods=['GET'])
@login_required
def api_equipment():
    """API для получения списка техники"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    equipment = Equipment.query.all()
    return jsonify([eq.to_dict() for eq in equipment])

@supply.route('/api/supply/orders', methods=['GET'])
@login_required
def api_orders():
    """API для получения списка заказов"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    orders = SupplyOrder.query.all()
    return jsonify([order.to_dict() for order in orders])
