from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from app.models.supply import (
    Material,
    Equipment,
    SupplyOrder,
    SupplyOrderItem,
    WarehouseMovement,
    WarehouseAttachment,
    UserMaterialAllocation,
    SupplyRequest,
    SupplyRequestItem,
    MaterialGroup,
    MaterialGroupItem,
)
from app.models.users import Users
from app.models.activity_log import ActivityLog
from app.extensions import db
from app.utils.mobile_detection import is_mobile_device
from app.utils.timezone_utils import get_moscow_now
from datetime import datetime, timedelta, timezone
from io import BytesIO
import os
from werkzeug.utils import secure_filename

supply = Blueprint('supply', __name__)

@supply.context_processor
def inject_gettext():
    """Внедряет функцию gettext в контекст шаблонов"""
    def gettext(text):
        return text
    return dict(gettext=gettext)

def is_supplier_or_admin():
    """Права на ИЗМЕНЕНИЯ в снабжении (операции): только Снабженец и Инженер ПТО."""
    if not current_user.is_authenticated:
        return False
    role = (current_user.role or '').strip().lower()
    allowed_keywords = ['снабжен', 'пто']
    return any(k in role for k in allowed_keywords)

def has_warehouse_read_access():
    """Право на ПРОСМОТР склада (читательский доступ). Добавляем роль прораба."""
    if not current_user.is_authenticated:
        return False
    role = (current_user.role or '').strip().lower()
    # разрешаем все роли из is_supplier_or_admin + прораб
    return any(k in role for k in ['снабжен', 'пто', 'ген', 'зам', 'прораб'])

@supply.route('/')
@login_required
def supply_dashboard():
    """Главная страница системы снабжения"""
    # Разрешаем просмотр дашборда всем с правом чтения склада,
    # чтобы избежать редирект-петли с /objects
    if not has_warehouse_read_access():
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

@supply.route('/supply/warehouse')
@login_required
def warehouse_view():
    """Страница склада: список материалов, последние движения, распределение."""
    if not has_warehouse_read_access():
        flash('У вас нет прав для доступа к складу', 'error')
        return redirect(url_for('objects.object_list'))

    materials = Material.query.order_by(Material.name).all()
    recent_movements = WarehouseMovement.query.order_by(WarehouseMovement.created_at.desc()).limit(20).all()
    allocations = UserMaterialAllocation.query.all()

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр склада",
        description=f"Материалов: {len(materials)}, движений: {len(recent_movements)}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/warehouse.html', materials=materials, recent_movements=recent_movements, allocations=allocations, current_user=current_user)

@supply.route('/supply/warehouse/mobile')
@login_required
def mobile_warehouse_view():
    """Мобильная страница склада с современным дизайном"""
    if not has_warehouse_read_access():
        flash('У вас нет прав для доступа к складу', 'error')
        return redirect(url_for('objects.object_list'))

    # Получаем статистику
    materials = Material.query.filter_by(is_active=True).all()
    materials_count = len(materials)
    active_materials_count = len([m for m in materials if m.is_active])
    low_stock_materials = [m for m in materials if m.current_quantity <= m.min_quantity]
    low_stock_count = len(low_stock_materials)
    
    # Простой расчет общей стоимости (можно улучшить)
    total_value = sum(m.current_quantity * (m.price_per_unit or 0) for m in materials if m.price_per_unit)

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр мобильного склада",
        description=f"Материалов: {materials_count}, низкий запас: {low_stock_count}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/mobile_warehouse.html', 
                         materials_count=materials_count,
                         active_materials_count=active_materials_count,
                         low_stock_count=low_stock_count,
                         total_value=total_value,
                         low_stock_materials=low_stock_materials[:5],  # Показываем только первые 5
                         current_user=current_user)

@supply.route('/supply/warehouse/allocations/mobile')
@login_required
def mobile_warehouse_allocations():
    """Мобильная страница распределения позиций"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к распределению', 'error')
        return redirect(url_for('objects.object_list'))

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр мобильного распределения",
        description="Просмотр списка пользователей для распределения",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/mobile_allocations.html', current_user=current_user)

@supply.route('/supply/warehouse/movements/mobile')
@login_required
def mobile_warehouse_movements():
    """Мобильная страница истории движений"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к истории движений', 'error')
        return redirect(url_for('objects.object_list'))

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр мобильной истории движений",
        description="Просмотр истории движений по складу",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/mobile_movements.html', current_user=current_user)

@supply.route('/supply/warehouse/receipt/mobile')
@login_required
def mobile_warehouse_receipt():
    """Мобильная страница поступления на склад"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к поступлению на склад', 'error')
        return redirect(url_for('objects.object_list'))

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр мобильной страницы поступления",
        description="Просмотр страницы поступления на склад",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/mobile_receipt.html', current_user=current_user)

@supply.route('/supply/warehouse/add-material/mobile')
@login_required
def mobile_warehouse_add_material():
    """Мобильная страница добавления позиции на склад"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для добавления позиций на склад', 'error')
        return redirect(url_for('objects.object_list'))

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр мобильной страницы добавления позиции",
        description="Просмотр страницы добавления позиции на склад",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/mobile_add_material.html', current_user=current_user)

@supply.route('/supply/warehouse/movement/mobile')
@login_required
def mobile_warehouse_movement():
    """Мобильная страница перемещения материалов"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для перемещения материалов', 'error')
        return redirect(url_for('objects.object_list'))

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр мобильной страницы перемещения",
        description="Просмотр страницы перемещения материалов",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/mobile_movement.html', current_user=current_user)

@supply.route('/supply/warehouse/materials/mobile')
@login_required
def mobile_warehouse_materials():
    """Мобильная страница просмотра материалов склада"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к материалам склада', 'error')
        return redirect(url_for('objects.object_list'))

    # Получаем все активные материалы
    materials = Material.query.filter_by(is_active=True).order_by(Material.name).all()
    
    # Подсчитываем статистику
    materials_count = len(materials)
    low_stock_materials = [m for m in materials if m.current_quantity <= m.min_quantity]
    low_stock_count = len(low_stock_materials)

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр мобильной страницы материалов",
        description="Просмотр материалов склада",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    return render_template('supply/mobile_materials.html', 
                         materials=materials,
                         materials_count=materials_count,
                         low_stock_count=low_stock_count,
                         current_user=current_user)

@supply.route('/supply/warehouse/movements')
@login_required
def warehouse_movements():
    """Страница истории перемещений"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к истории перемещений', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Логируем просмотр страницы истории перемещений
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр страницы",
        description=f"Пользователь {current_user.login} просмотрел историю перемещений",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('supply/movements_history.html')

@supply.route('/supply/warehouse/allocations')
@login_required
def warehouse_allocations():
    """Страница распределения позиций по пользователям"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к распределению позиций', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Логируем просмотр страницы распределения
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр страницы",
        description=f"Пользователь {current_user.login} просмотрел распределение позиций",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('supply/allocations.html')

@supply.route('/supply/warehouse/user/<uuid:user_id>')
@login_required
def warehouse_user_detail(user_id):
    """Страница детального просмотра пользователя с его позициями"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для доступа к распределению позиций', 'error')
        return redirect(url_for('objects.object_list'))
    
    # Получаем информацию о пользователе
    user = Users.query.get_or_404(user_id)
    
    # Логируем просмотр страницы пользователя
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр страницы",
        description=f"Пользователь {current_user.login} просмотрел позиции пользователя {user.login}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('supply/user_detail.html', user=user)

@supply.route('/user/<uuid:user_id>/material/<uuid:material_id>/movements')
@login_required
def user_material_movements(user_id, material_id):
    """Страница истории движений конкретного материала с конкретным пользователем"""
    if not is_supplier_or_admin():
        return redirect(url_for('supply.warehouse_view'))
    
    try:
        # Получаем информацию о пользователе
        user = Users.query.get_or_404(user_id)
        
        # Получаем информацию о материале
        material = Material.query.get_or_404(material_id)
        
        return render_template('supply/user_material_movements.html', 
                             user=user, material=material)
    except Exception as e:
        print(f"Ошибка в user_material_movements: {e}")
        return redirect(url_for('supply.warehouse_view'))

@supply.route('/warehouse/material/<uuid:material_id>')
@login_required
def material_detail(material_id):
    """Страница детальной информации о материале"""
    try:
        print(f"DEBUG: Попытка доступа к материалу {material_id} пользователем {current_user.login} с ролью {current_user.role}")
        
        # Временно отключаем проверку прав для тестирования
        # if not is_supplier_or_admin():
        #     return redirect(url_for('objects.object_list'))
        
        # Получаем информацию о материале
        material = Material.query.get_or_404(material_id)
        print(f"DEBUG: Материал найден: {material.name}")
        
        # Получаем историю движений по материалу с загрузкой связанных пользователей
        movements = db.session.query(WarehouseMovement).options(
            db.joinedload(WarehouseMovement.to_user),
            db.joinedload(WarehouseMovement.from_user),
            db.joinedload(WarehouseMovement.attachments)
        ).filter_by(material_id=material_id).order_by(WarehouseMovement.created_at.desc()).limit(20).all()
        
        # Создаем виртуальную запись для первоначального создания материала
        from datetime import datetime
        from app.utils.timezone_utils import get_moscow_now
        
        # Создаем объект для отображения операции создания
        class VirtualMovement:
            def __init__(self, movement_type, quantity, created_at, note="", user=None):
                self.movement_type = movement_type
                self.quantity = quantity
                self.created_at = created_at
                self.note = note
                self.to_user = user
                self.from_user = None
                self.attachments = []
        
        # Добавляем виртуальную запись о создании материала
        creation_movement = VirtualMovement(
            movement_type='creation',
            quantity=material.current_quantity,
            created_at=material.created_at,
            note="Создание материала",
            user=None
        )
        
        # Объединяем реальные движения с виртуальным созданием
        all_actions = [creation_movement] + list(movements)
        
        # Сортируем по дате (новые сверху)
        all_actions.sort(key=lambda x: x.created_at, reverse=True)
        
        # Получаем распределения материала по пользователям с загрузкой пользователей
        allocations = db.session.query(UserMaterialAllocation).options(
            db.joinedload(UserMaterialAllocation.user)
        ).filter_by(material_id=material_id).all()
        
        # Логируем просмотр страницы материала
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Просмотр материала",
            description=f"Пользователь {current_user.login} просмотрел детальную информацию о материале '{material.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        print(f"DEBUG: Рендерим шаблон material_detail.html")
        return render_template('supply/material_detail.html', material=material, movements=all_actions, allocations=allocations)
    
    except Exception as e:
        print(f"Ошибка в material_detail: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('supply.warehouse_view'))

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

@supply.route('/supply/requests')
@login_required
def requests_list():
    """Список заявок"""
    if not is_supplier_or_admin():
        flash('У вас нет прав для просмотра заявок', 'error')
        return redirect(url_for('objects.object_list'))
    requests_q = SupplyRequest.query.order_by(SupplyRequest.created_at.desc()).all()
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр списка заявок",
        description=f"Просмотрено заявок: {len(requests_q)}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    return render_template('supply/requests.html', requests=requests_q)

# API маршруты для AJAX запросов
@supply.route('/api/supply/materials', methods=['GET'])
@login_required
def api_materials():
    """API для получения списка активных материалов"""
    if not has_warehouse_read_access():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    materials = Material.query.filter_by(is_active=True).all()
    return jsonify([material.to_dict() for material in materials])

@supply.route('/api/supply/groups', methods=['GET', 'POST'])
@login_required
def api_groups():
    """Список групп (GET — всем), создание группы (POST — только снабженец/ПТО)."""
    if request.method == 'GET':
        groups = MaterialGroup.query.order_by(MaterialGroup.name).all()
        return jsonify([g.to_dict() for g in groups])
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip() or None
    if not name:
        return jsonify({'error': 'Название обязательно'}), 400
    if MaterialGroup.query.filter(db.func.lower(MaterialGroup.name) == name.lower()).first():
        return jsonify({'error': 'Группа уже существует'}), 409
    group = MaterialGroup(name=name, description=description, created_by=current_user.userid)
    db.session.add(group)
    db.session.commit()
    return jsonify(group.to_dict()), 201

@supply.route('/api/supply/groups/<uuid:group_id>', methods=['DELETE'])
@login_required
def api_groups_delete(group_id):
    """Удаление группы с каскадным удалением её элементов (только Снабженец/Инженер ПТО)."""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    group = MaterialGroup.query.get(group_id)
    if not group:
        return jsonify({'error': 'Группа не найдена'}), 404
    try:
        # Логируем действие
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Удаление группы материалов",
            description=f"Удалена группа '{group.name}' и все её элементы",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )

        # Удаляем элементы группы, затем саму группу
        MaterialGroupItem.query.filter_by(group_id=group.id).delete()
        db.session.delete(group)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка удаления группы: {str(e)}'}), 500

@supply.route('/api/supply/groups/<uuid:group_id>/items', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_group_items(group_id):
    group = MaterialGroup.query.get_or_404(group_id)
    if request.method == 'GET':
        items = MaterialGroupItem.query.filter_by(group_id=group.id).all()
        return jsonify([i.to_dict() for i in items])
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    data = request.get_json() or {}
    material_id = data.get('material_id')
    if request.method == 'POST':
        if not material_id:
            return jsonify({'error': 'material_id обязателен'}), 400
        if MaterialGroupItem.query.filter_by(group_id=group.id, material_id=material_id).first():
            return jsonify({'error': 'Материал уже в группе'}), 409
        link = MaterialGroupItem(group_id=group.id, material_id=material_id)
        db.session.add(link)
        db.session.commit()
        return jsonify(link.to_dict()), 201
    # DELETE
    if not material_id:
        return jsonify({'error': 'material_id обязателен'}), 400
    link = MaterialGroupItem.query.filter_by(group_id=group.id, material_id=material_id).first()
    if not link:
        return jsonify({'error': 'Связь не найдена'}), 404
    db.session.delete(link)
    db.session.commit()
    return jsonify({'success': True})

@supply.route('/api/supply/materials/all', methods=['GET'])
@login_required
def api_materials_all():
    """API для получения всех материалов (включая скрытые) - только для админов"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Проверяем, что пользователь - админ
    if current_user.role not in ['Инженер ПТО', 'Снабженец']:
        return jsonify({'error': 'Просмотр скрытых материалов доступен только администраторам'}), 403
    
    materials = Material.query.all()
    return jsonify([material.to_dict() for material in materials])

@supply.route('/api/supply/materials/check', methods=['POST'])
@login_required
def api_materials_check():
    """Проверка существующего материала по названию с учетом регистра и опечаток"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    data = request.get_json()
    name = (data.get('name') or '').strip()
    
    if not name:
        return jsonify({'error': 'Требуется название материала'}), 400
    
    # Получаем все активные материалы
    all_materials = Material.query.filter_by(is_active=True).all()
    
    # 1. Точное совпадение (с учетом регистра)
    exact_match = next((m for m in all_materials if m.name == name), None)
    if exact_match:
        return jsonify({
            'exists': True,
            'exact_match': True,
            'material': {
                'name': exact_match.name,
                'unit': exact_match.unit,
                'min_quantity': exact_match.min_quantity,
                'current_quantity': exact_match.current_quantity,
                'description': exact_match.description or ''
            }
        })
    
    # 2. Совпадение без учета регистра
    case_insensitive_match = next((m for m in all_materials if m.name.lower() == name.lower()), None)
    if case_insensitive_match:
        return jsonify({
            'exists': True,
            'exact_match': False,
            'case_corrected': True,
            'corrected_name': case_insensitive_match.name,
            'material': {
                'name': case_insensitive_match.name,
                'unit': case_insensitive_match.unit,
                'min_quantity': case_insensitive_match.min_quantity,
                'current_quantity': case_insensitive_match.current_quantity,
                'description': case_insensitive_match.description or ''
            }
        })
    
    # 3. Поиск похожих названий (простой алгоритм Левенштейна)
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # Ищем похожие названия
    similar_materials = []
    for material in all_materials:
        distance = levenshtein_distance(name.lower(), material.name.lower())
        # Если расстояние меньше 30% от длины более короткой строки
        max_distance = min(len(name), len(material.name)) * 0.3
        if distance <= max_distance and distance > 0:
            similar_materials.append({
                'name': material.name,
                'distance': distance,
                'unit': material.unit,
                'min_quantity': material.min_quantity,
                'current_quantity': material.current_quantity,
                'description': material.description or ''
            })
    
    # Сортируем по расстоянию (более похожие сначала)
    similar_materials.sort(key=lambda x: x['distance'])
    
    if similar_materials:
        return jsonify({
            'exists': False,
            'similar_found': True,
            'similar_materials': similar_materials[:3]  # Возвращаем до 3 похожих
        })
    
    return jsonify({'exists': False, 'similar_found': False})

@supply.route('/api/supply/materials', methods=['POST'])
@login_required
def api_materials_create():
    """Создание материала"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403

    data = request.get_json(force=True, silent=True) or {}
    name = (data.get('name') or '').strip()
    unit = (data.get('unit') or '').strip()
    if not name or not unit:
        return jsonify({'error': 'Требуются name и unit'}), 400

    # Сначала проверяем, есть ли активный материал с таким же именем
    active_material = Material.query.filter_by(name=name, is_active=True).first()
    
    if active_material:
        # Пополняем существующий активный материал
        new_quantity = float(data.get('current_quantity') or 0.0)
        addition_reason = data.get('addition_reason', '').strip()
        
        # Создаем запись о пополнении в истории движений
        movement = WarehouseMovement(
            material_id=active_material.id,
            quantity=new_quantity,
            movement_type='replenishment',
            note=f"Пополнение материала. Причина: {addition_reason}" if addition_reason else "Пополнение материала",
            created_by=current_user.userid,
        )
        db.session.add(movement)
        
        # Обновляем количество материала
        active_material.current_quantity = (active_material.current_quantity or 0.0) + new_quantity
        active_material.updated_at = get_moscow_now()
        
        db.session.commit()
        
        # Логируем действие
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Пополнение материала",
            description=f'Пополнен материал "{name}" на {new_quantity} {active_material.unit}. Причина: {addition_reason}' if addition_reason else f'Пополнен материал "{name}" на {new_quantity} {active_material.unit}',
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        # Возвращаем информацию о пополнении
        return jsonify({
            'success': True,
            'material': active_material.to_dict(),
            'message': f'Материал "{name}" пополнен на {new_quantity} {active_material.unit}. Текущее количество: {active_material.current_quantity} {active_material.unit}'
        }), 201
    
    # Проверяем, есть ли неактивный материал с таким же именем
    existing_material = Material.query.filter_by(name=name, is_active=False).first()
    
    if existing_material:
        # Восстанавливаем существующий материал
        existing_material.is_active = True
        existing_material.current_quantity = float(data.get('current_quantity') or 0.0)
        existing_material.min_quantity = float(data.get('min_quantity') or 0.0)
        existing_material.description = data.get('description')
        existing_material.supplier = data.get('supplier')
        existing_material.price_per_unit = float(data.get('price_per_unit') or 0.0) if data.get('price_per_unit') is not None else None
        existing_material.updated_at = get_moscow_now()
        
        db.session.commit()
        
        # Возвращаем предупреждение о восстановлении
        return jsonify({
            'success': True,
            'material': existing_material.to_dict(),
            'warning': f'Материал "{name}" уже существовал ранее и был восстановлен. Все предыдущие перемещения и история будут сохранены и объединены с новыми операциями.'
        }), 201
    else:
        # Создаем новый материал
        material = Material(
            name=name,
            unit=unit,
            description=data.get('description'),
            current_quantity=float(data.get('current_quantity') or 0.0),
            min_quantity=float(data.get('min_quantity') or 0.0),
            supplier=data.get('supplier'),
            price_per_unit=float(data.get('price_per_unit') or 0.0) if data.get('price_per_unit') is not None else None,
        )
        db.session.add(material)
        db.session.commit()
        return jsonify(material.to_dict()), 201

@supply.route('/api/supply/materials/<uuid:material_id>', methods=['PUT'])
@login_required
def api_materials_update(material_id):
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403

    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Материал не найден'}), 404

    data = request.get_json(force=True, silent=True) or {}
    for field in ['name', 'description', 'unit', 'supplier']:
        if field in data and data[field] is not None:
            setattr(material, field, data[field])
    for fnum in ['current_quantity', 'min_quantity', 'price_per_unit']:
        if fnum in data and data[fnum] is not None:
            try:
                setattr(material, fnum, float(data[fnum]))
            except Exception:
                return jsonify({'error': f'Неверное значение {fnum}'}), 400
    db.session.commit()
    return jsonify(material.to_dict())

@supply.route('/api/supply/materials/<uuid:material_id>', methods=['DELETE'])
@login_required
def api_materials_delete(material_id):
    """Удаление материала (только для админов)"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Проверяем, что пользователь - админ
    if current_user.role not in ['Инженер ПТО', 'Ген.Директор']:
        return jsonify({'error': 'Удаление материалов доступно только администраторам'}), 403
    
    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Материал не найден'}), 404
    
    material_name = material.name
    
    # Логируем действие перед удалением
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Удаление материала",
        description=f"Удален материал: {material_name}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Мягкое удаление - помечаем как неактивный
    material.is_active = False
    material.updated_at = get_moscow_now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Материал "{material_name}" успешно удален'})

@supply.route('/api/supply/materials/<uuid:material_id>/restore', methods=['POST'])
@login_required
def api_materials_restore(material_id):
    """Восстановление скрытого материала (только для админов)"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Проверяем, что пользователь - админ
    if current_user.role not in ['Инженер ПТО', 'Ген.Директор']:
        return jsonify({'error': 'Восстановление материалов доступно только администраторам'}), 403
    
    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Материал не найден'}), 404
    
    if material.is_active:
        return jsonify({'error': 'Материал уже активен'}), 400
    
    material_name = material.name
    
    # Логируем действие
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Восстановление материала",
        description=f"Восстановлен материал: {material_name}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Восстанавливаем материал
    material.is_active = True
    material.updated_at = get_moscow_now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Материал "{material_name}" успешно восстановлен'})

@supply.route('/api/supply/materials/<uuid:material_id>/hard-delete', methods=['DELETE'])
@login_required
def api_materials_hard_delete(material_id):
    """Полное удаление материала со всеми связанными записями (только для админов)"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Проверяем, что пользователь - админ
    if current_user.role not in ['Инженер ПТО', 'Ген.Директор']:
        return jsonify({'error': 'Полное удаление материалов доступно только администраторам'}), 403
    
    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Материал не найден'}), 404
    
    material_name = material.name
    
    try:
        # Логируем действие перед удалением
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Полное удаление материала",
            description=f"Полностью удален материал: {material_name} со всеми связанными записями",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        # Получаем все связанные записи для логирования
        movements_count = WarehouseMovement.query.filter_by(material_id=material_id).count()
        allocations_count = UserMaterialAllocation.query.filter_by(material_id=material_id).count()
        request_items_count = SupplyRequestItem.query.filter_by(material_id=material_id).count()
        
        # Удаляем все вложения к движениям этого материала
        movements = WarehouseMovement.query.filter_by(material_id=material_id).all()
        for movement in movements:
            WarehouseAttachment.query.filter_by(movement_id=movement.id).delete()
        
        # Удаляем все движения по материалу
        WarehouseMovement.query.filter_by(material_id=material_id).delete()
        
        # Удаляем все распределения материала по пользователям
        UserMaterialAllocation.query.filter_by(material_id=material_id).delete()
        
        # Удаляем все элементы заявок, связанные с материалом
        SupplyRequestItem.query.filter_by(material_id=material_id).delete()
        
        # Удаляем сам материал
        db.session.delete(material)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Материал "{material_name}" полностью удален. Удалено: {movements_count} движений, {allocations_count} распределений, {request_items_count} элементов заявок.'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка полного удаления материала: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка удаления: {str(e)}'}), 500

@supply.route('/api/supply/movements', methods=['POST'])
@login_required
def api_create_movement():
    """Создание движения по складу с опциональным прикреплением файла."""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403

    # Поддерживаем multipart/form-data (для файла) и JSON
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        form = request.form
        files = request.files
        payload = form
    else:
        payload = request.get_json(force=True, silent=True) or {}
        files = {}

    material_id = payload.get('material_id')
    quantity = payload.get('quantity')
    movement_type = (payload.get('movement_type') or '').strip()
    note = payload.get('note')
    from_user_id = payload.get('from_user_id')
    to_user_id = payload.get('to_user_id')

    if not material_id or not quantity or not movement_type:
        return jsonify({'error': 'material_id, quantity и movement_type обязательны'}), 400

    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Материал не найден'}), 404

    try:
        quantity = float(quantity)
    except Exception:
        return jsonify({'error': 'quantity должен быть числом'}), 400

    # Проверяем достаточность количества
    if movement_type == 'move':
        # Для выдачи проверяем наличие на складе
        if material.current_quantity < quantity:
            return jsonify({
                'error': f'Недостаточно материала на складе. Доступно: {material.current_quantity} {material.unit}, требуется: {quantity} {material.unit}'
            }), 400
    elif movement_type == 'return':
        # Для возврата проверяем наличие у пользователя
        if from_user_id:
            user_alloc = UserMaterialAllocation.query.filter_by(user_id=from_user_id, material_id=material.id).first()
            user_quantity = user_alloc.quantity if user_alloc else 0.0
            if user_quantity < quantity:
                return jsonify({
                    'error': f'У пользователя недостаточно материала. Доступно: {user_quantity} {material.unit}, требуется: {quantity} {material.unit}'
                }), 400
    elif movement_type == 'writeoff':
        # Для списания проверяем наличие на складе
        if material.current_quantity < quantity:
            return jsonify({
                'error': f'Недостаточно материала на складе. Доступно: {material.current_quantity} {material.unit}, требуется: {quantity} {material.unit}'
            }), 400

    movement = WarehouseMovement(
        material_id=material.id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        quantity=quantity,
        movement_type=movement_type,
        note=note,
        created_by=current_user.userid,
    )
    db.session.add(movement)

    # Отслеживаем, был ли материал восстановлен
    material_restored = False
    
    # Обновление остатков материала
    if movement_type == 'add':
        # Поступление на склад - увеличиваем количество
        material.current_quantity = (material.current_quantity or 0.0) + quantity
        # Если материал был неактивен, восстанавливаем его
        if not material.is_active:
            material.is_active = True
            material.updated_at = get_moscow_now()
            material_restored = True
            print(f"DEBUG: Материал '{material.name}' автоматически восстановлен при поступлении")
    elif movement_type == 'move':
        # Выдача со склада пользователю - уменьшаем склад, увеличиваем у пользователя
        material.current_quantity = (material.current_quantity or 0.0) - quantity
    elif movement_type == 'return':
        # Возврат от пользователя на склад - увеличиваем склад, уменьшаем у пользователя
        material.current_quantity = (material.current_quantity or 0.0) + quantity
        # Если материал был неактивен, восстанавливаем его
        if not material.is_active:
            material.is_active = True
            material.updated_at = get_moscow_now()
            material_restored = True
            print(f"DEBUG: Материал '{material.name}' автоматически восстановлен при возврате")
    elif movement_type == 'writeoff':
        # Списание - только уменьшаем склад
        material.current_quantity = (material.current_quantity or 0.0) - quantity

    # Обновляем распределение по пользователям
    if movement_type == 'move' and to_user_id:
        # Выдача: увеличиваем количество у получателя
        alloc = UserMaterialAllocation.query.filter_by(user_id=to_user_id, material_id=material.id).first()
        if not alloc:
            alloc = UserMaterialAllocation(user_id=to_user_id, material_id=material.id, quantity=0.0)
            db.session.add(alloc)
        alloc.quantity = (alloc.quantity or 0.0) + quantity
        alloc.updated_at = get_moscow_now()  # Обновляем время изменения
        
    elif movement_type == 'return' and from_user_id:
        # Возврат: уменьшаем количество у возвращающего
        alloc_from = UserMaterialAllocation.query.filter_by(user_id=from_user_id, material_id=material.id).first()
        if alloc_from:
            new_quantity = max(0.0, (alloc_from.quantity or 0.0) - quantity)
            alloc_from.quantity = new_quantity
            alloc_from.updated_at = get_moscow_now()  # Обновляем время изменения
            
            # Если количество стало 0, удаляем запись
            if new_quantity == 0:
                db.session.delete(alloc_from)
        else:
            # Если у пользователя нет этого материала, но он пытается его вернуть
            # Это может быть ошибка, но мы не блокируем операцию
            pass

    # Обработка вложения
    upload = files.get('file') if hasattr(files, 'get') else None
    if upload and upload.filename:
        data = upload.read()
        attachment = WarehouseAttachment(
            movement=movement,
            filename=upload.filename,
            content_type=upload.mimetype,
            data=data,
            size_bytes=len(data),
            uploaded_by=current_user.userid,
        )
        db.session.add(attachment)

    db.session.commit()

    # Проверяем, нужно ли скрыть материал (если количество стало 0 или меньше)
    if material.current_quantity <= 0 and material.is_active:
        material.is_active = False
        material.updated_at = get_moscow_now()
        db.session.commit()
        print(f"DEBUG: Материал '{material.name}' автоматически скрыт (количество: {material.current_quantity})")

    # Логируем действие с деталями
    action_description = f"Создано движение: {movement_type}, материал: {material.name}, количество: {quantity}"
    if movement_type == 'move' and to_user_id:
        user = Users.query.get(to_user_id)
        if user:
            action_description += f", выдано пользователю: {user.login}"
    elif movement_type == 'return' and from_user_id:
        user = Users.query.get(from_user_id)
        if user:
            action_description += f", возвращено от пользователя: {user.login}"

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Движение по складу",
        description=action_description,
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    response_data = {
        'movement': movement.to_dict(),
        'material': material.to_dict(),
    }
    
    # Добавляем предупреждение, если материал был восстановлен
    if material_restored:
        response_data['warning'] = f'Материал "{material.name}" был автоматически восстановлен, так как ранее был скрыт. Все предыдущие перемещения и история сохранены.'
    
    return jsonify(response_data), 201

@supply.route('/api/supply/movements', methods=['GET'])
@login_required
def api_list_movements():
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Получаем движения с информацией о материалах
    movements = db.session.query(
        WarehouseMovement,
        Material.name.label('material_name')
    ).join(
        Material, WarehouseMovement.material_id == Material.id
    ).order_by(
        WarehouseMovement.created_at.desc()
    ).limit(200).all()
    
    result = []
    for movement, material_name in movements:
        movement_dict = movement.to_dict()
        movement_dict['material_name'] = material_name
        
        # Определяем пользователя в зависимости от типа движения
        user_name = "Не указан"
        if movement.movement_type == 'return' and movement.from_user_id:
            # Для возврата ищем пользователя по from_user_id
            user = Users.query.get(movement.from_user_id)
            if user:
                user_name = f"{user.secondname or ''} {user.firstname or ''}".strip() or user.login
        elif movement.movement_type in ['move', 'add'] and movement.to_user_id:
            # Для выдачи и поступления ищем пользователя по to_user_id
            user = Users.query.get(movement.to_user_id)
            if user:
                user_name = f"{user.secondname or ''} {user.firstname or ''}".strip() or user.login
        
        movement_dict['to_user_name'] = user_name
        
        # Получаем вложения для этого движения
        attachments = WarehouseAttachment.query.filter_by(movement_id=movement.id).all()
        movement_dict['attachments'] = [{
            'id': str(att.id),
            'filename': att.filename,
            'original_filename': att.filename,  # В текущей модели нет отдельного поля
            'file_size': att.size_bytes,
            'mime_type': att.content_type
        } for att in attachments]
        
        result.append(movement_dict)
    
    return jsonify(result)

@supply.route('/api/supply/allocations', methods=['GET'])
@login_required
def api_list_allocations():
    """Получение списка распределений позиций по пользователям"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Получаем распределения с информацией о материалах и пользователях
    allocations = db.session.query(
        UserMaterialAllocation,
        Material.name.label('material_name'),
        Material.unit.label('material_unit'),
        Users.secondname.label('user_last_name'),
        Users.firstname.label('user_first_name'),
        Users.login.label('user_login')
    ).join(
        Material, UserMaterialAllocation.material_id == Material.id
    ).join(
        Users, UserMaterialAllocation.user_id == Users.userid
    ).order_by(
        UserMaterialAllocation.updated_at.desc()
    ).all()
    
    result = []
    for allocation, material_name, material_unit, user_last_name, user_first_name, user_login in allocations:
        allocation_dict = allocation.to_dict()
        allocation_dict['material_name'] = material_name
        allocation_dict['material_unit'] = material_unit
        allocation_dict['user_name'] = f"{user_last_name or ''} {user_first_name or ''}".strip() or user_login
        allocation_dict['user_login'] = user_login
        result.append(allocation_dict)
    
    return jsonify(result)

@supply.route('/api/supply/material-allocations', methods=['GET'])
@login_required
def api_material_allocations():
    """Получение пользователей, у которых есть конкретный материал"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    material_id = request.args.get('material_id')
    if not material_id:
        return jsonify({'error': 'material_id обязателен'}), 400
    
    # Получаем пользователей, у которых есть этот материал
    allocations = db.session.query(
        UserMaterialAllocation,
        Users.secondname.label('user_last_name'),
        Users.firstname.label('user_first_name'),
        Users.thirdname.label('user_third_name'),
        Users.login.label('user_login'),
        Material.unit.label('material_unit')
    ).join(
        Users, UserMaterialAllocation.user_id == Users.userid
    ).join(
        Material, UserMaterialAllocation.material_id == Material.id
    ).filter(
        UserMaterialAllocation.material_id == material_id,
        UserMaterialAllocation.quantity > 0
    ).order_by(
        Users.secondname, Users.firstname
    ).all()
    
    result = []
    for allocation, user_last_name, user_first_name, user_third_name, user_login, material_unit in allocations:
        result.append({
            'id': str(allocation.user_id),
            'name': f"{user_last_name or ''} {user_first_name or ''} {user_third_name or ''}".strip(),
            'login': user_login,
            'quantity': allocation.quantity,
            'material_unit': material_unit
        })
    
    return jsonify(result)

@supply.route('/api/supply/users-with-allocations', methods=['GET'])
@login_required
def api_users_with_allocations():
    """Получение списка пользователей с их позициями"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Получаем всех пользователей, у которых есть распределения
    users_with_allocations = db.session.query(
        Users.userid,
        Users.secondname,
        Users.firstname,
        Users.thirdname,
        Users.login,
        Users.role,
        Users.avatar,
        db.func.count(UserMaterialAllocation.id).label('allocations_count'),
        db.func.sum(UserMaterialAllocation.quantity).label('total_quantity')
    ).join(
        UserMaterialAllocation, Users.userid == UserMaterialAllocation.user_id
    ).group_by(
        Users.userid, Users.secondname, Users.firstname, Users.thirdname, Users.login, Users.role, Users.avatar
    ).order_by(
        Users.secondname, Users.firstname
    ).all()
    
    result = []
    for user in users_with_allocations:
        user_dict = {
            'id': str(user.userid),
            'name': f"{user.secondname or ''} {user.firstname or ''} {user.thirdname or ''}".strip(),
            'login': user.login,
            'role': user.role,
            'avatar': user.avatar,
            'allocations_count': user.allocations_count,
            'total_quantity': float(user.total_quantity or 0)
        }
        result.append(user_dict)
    
    return jsonify(result)

@supply.route('/api/supply/user/<uuid:user_id>/allocations', methods=['GET'])
@login_required
def api_user_allocations(user_id):
    """Получение позиций конкретного пользователя"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Получаем распределения конкретного пользователя
    allocations = db.session.query(
        UserMaterialAllocation,
        Material.name.label('material_name'),
        Material.unit.label('material_unit'),
        Material.current_quantity.label('warehouse_quantity')
    ).join(
        Material, UserMaterialAllocation.material_id == Material.id
    ).filter(
        UserMaterialAllocation.user_id == user_id
    ).order_by(
        UserMaterialAllocation.updated_at.desc()
    ).all()
    
    result = []
    for allocation, material_name, material_unit, warehouse_quantity in allocations:
        allocation_dict = allocation.to_dict()
        allocation_dict['material_name'] = material_name
        allocation_dict['material_unit'] = material_unit
        allocation_dict['warehouse_quantity'] = warehouse_quantity
        result.append(allocation_dict)
    
    return jsonify(result)

@supply.route('/api/supply/materials-for-return', methods=['GET'])
@login_required
def api_materials_for_return():
    """Получение всех материалов, которые можно вернуть (есть у пользователей)"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    try:
        # Сначала проверим, что вообще есть в базе данных
        total_materials = Material.query.filter_by(is_active=True).count()
        total_allocations = UserMaterialAllocation.query.count()
        total_movements = WarehouseMovement.query.count()
        move_movements = WarehouseMovement.query.filter_by(movement_type='move').count()
        
        print(f"DEBUG: Всего активных материалов: {total_materials}")
        print(f"DEBUG: Всего записей в UserMaterialAllocation: {total_allocations}")
        print(f"DEBUG: Всего записей в WarehouseMovement: {total_movements}")
        print(f"DEBUG: Записей о выдаче (move): {move_movements}")
        
        # Получаем все материалы, которые когда-либо были выданы пользователям
        # (даже если текущее количество у пользователей = 0)
        # Для возврата показываем ВСЕ материалы, независимо от is_active
        materials = db.session.query(
            Material,
            db.func.sum(UserMaterialAllocation.quantity).label('total_allocated')
        ).join(
            UserMaterialAllocation, Material.id == UserMaterialAllocation.material_id
        ).group_by(
            Material.id
        ).all()
        
        print(f"DEBUG: Найдено материалов для возврата через UserMaterialAllocation: {len(materials)}")
        
        result = []
        for material, total_allocated in materials:
            material_dict = material.to_dict()
            material_dict['total_allocated'] = float(total_allocated or 0)
            result.append(material_dict)
            print(f"DEBUG: Материал {material.name}, у пользователей: {total_allocated}")
        
        # Если нет материалов через UserMaterialAllocation, попробуем через WarehouseMovement
        if not result:
            print("DEBUG: Нет материалов в UserMaterialAllocation, проверяем WarehouseMovement")
            # Получаем материалы, которые были выданы (movement_type = 'move')
            # Для возврата показываем ВСЕ материалы, независимо от is_active
            materials_with_movements = db.session.query(
                Material,
                db.func.sum(WarehouseMovement.quantity).label('total_moved')
            ).join(
                WarehouseMovement, Material.id == WarehouseMovement.material_id
            ).filter(
                WarehouseMovement.movement_type == 'move'
            ).group_by(
                Material.id
            ).all()
            
            print(f"DEBUG: Найдено материалов через WarehouseMovement: {len(materials_with_movements)}")
            
            for material, total_moved in materials_with_movements:
                material_dict = material.to_dict()
                material_dict['total_allocated'] = float(total_moved or 0)
                result.append(material_dict)
                print(f"DEBUG: Материал {material.name}, было выдано: {total_moved}")
        
        # Если все еще нет результатов, покажем все материалы (включая неактивные)
        if not result:
            print("DEBUG: Все еще нет результатов, показываем все материалы")
            all_materials = Material.query.all()  # Убираем фильтр is_active
            print(f"DEBUG: Всего материалов (включая неактивные): {len(all_materials)}")
            
            for material in all_materials:
                material_dict = material.to_dict()
                material_dict['total_allocated'] = 0.0  # Показываем как 0, но материал доступен
                result.append(material_dict)
                print(f"DEBUG: Показываем материал {material.name} (is_active={material.is_active}) с количеством 0")
        
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: Ошибка в api_materials_for_return: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@supply.route('/api/supply/user/<uuid:user_id>/material/<uuid:material_id>/movements', methods=['GET'])
@login_required
def api_user_material_movements(user_id, material_id):
    """Получение истории движений конкретного материала с конкретным пользователем"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    # Получаем движения материала с пользователем
    movements = db.session.query(
        WarehouseMovement,
        Material.name.label('material_name'),
        Material.unit.label('material_unit'),
        Users.firstname.label('user_firstname'),
        Users.secondname.label('user_secondname'),
        Users.login.label('user_login')
    ).join(
        Material, WarehouseMovement.material_id == Material.id
    ).outerjoin(
        Users, WarehouseMovement.to_user_id == Users.userid
    ).filter(
        WarehouseMovement.material_id == material_id,
        db.or_(
            WarehouseMovement.to_user_id == user_id,
            WarehouseMovement.from_user_id == user_id
        )
    ).order_by(
        WarehouseMovement.created_at.desc()
    ).all()
    
    result = []
    for movement, material_name, material_unit, user_firstname, user_secondname, user_login in movements:
        movement_dict = movement.to_dict()
        movement_dict['material_name'] = material_name
        movement_dict['material_unit'] = material_unit
        movement_dict['user_name'] = f"{user_secondname or ''} {user_firstname or ''}".strip()
        movement_dict['user_login'] = user_login
        
        # Добавляем информацию о файлах
        if movement.attachments:
            movement_dict['attachments'] = [att.to_dict() for att in movement.attachments]
        else:
            movement_dict['attachments'] = []
            
        result.append(movement_dict)
    
    return jsonify(result)

@supply.route('/api/supply/users/search', methods=['GET'])
@login_required
def api_search_users():
    """Поиск пользователей по имени/фамилии/логину"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    # Поиск по имени, фамилии, логину (используем правильные названия полей)
    users = Users.query.filter(
        db.or_(
            Users.firstname.ilike(f'%{query}%'),
            Users.secondname.ilike(f'%{query}%'),
            Users.thirdname.ilike(f'%{query}%'),
            Users.login.ilike(f'%{query}%'),
            db.func.concat(Users.secondname, ' ', Users.firstname, ' ', Users.thirdname).ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    result = []
    for user in users:
        firstname = user.firstname or ''
        secondname = user.secondname or ''
        thirdname = user.thirdname or ''
        login = user.login or ''
        
        # Формируем полное имя
        full_name = f"{secondname} {firstname} {thirdname}".strip()
        if not full_name:
            full_name = login
        
        result.append({
            'id': str(user.userid),
            'name': full_name,
            'login': login,
            'display': f"{full_name} ({login})"
        })
    
    return jsonify(result)

@supply.route('/api/supply/users/all', methods=['GET'])
@login_required
def api_get_all_users():
    """Получение всех пользователей для аккордеона"""
    try:
        # Получаем всех пользователей, отсортированных по фамилии
        users = Users.query.order_by(Users.secondname, Users.firstname).all()
        
        result = []
        for user in users:
            # Используем правильные названия полей из модели Users
            firstname = user.firstname or ''
            secondname = user.secondname or ''
            thirdname = user.thirdname or ''
            login = user.login or ''
            role = user.role or 'Не указана'
            userid = user.userid
            
            # Формируем полное имя
            full_name = f"{secondname} {firstname} {thirdname}".strip()
            if not full_name:
                full_name = login  # Если нет имени, используем логин
            
            user_data = {
                'id': str(userid),
                'name': full_name,
                'login': login,
                'display': f"{full_name} ({login})",
                'role': role
            }
            result.append(user_data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API: Ошибка при получении пользователей: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@supply.route('/api/supply/users/simple', methods=['GET'])
@login_required
def api_get_users_simple():
    """Простое получение пользователей без сложной логики"""
    try:
        # Простой запрос без сортировки
        users = Users.query.all()
        
        result = []
        for user in users:
            # Используем правильные названия полей
            firstname = user.firstname or ''
            secondname = user.secondname or ''
            thirdname = user.thirdname or ''
            login = user.login or ''
            role = user.role or 'Не указана'
            
            # Формируем полное имя
            full_name = f"{secondname} {firstname} {thirdname}".strip()
            if not full_name:
                full_name = login
            
            result.append({
                'id': str(user.userid),
                'name': full_name,
                'login': login,
                'display': f"{full_name} ({login})",
                'role': role
            })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API Simple: Ошибка при получении пользователей: {e}")
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@supply.route('/api/supply/receipt', methods=['POST'])
@login_required
def api_create_receipt():
    """Создание поступления на склад с накладной"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    try:
        # Получаем данные из формы
        name = request.form.get('name', '').strip()
        unit = request.form.get('unit', '').strip()
        quantity = float(request.form.get('quantity', 0))
        file = request.files.get('file')
        
        if not name or not unit or quantity <= 0:
            return jsonify({'error': 'Заполните все обязательные поля'}), 400
        
        if not file or file.filename == '':
            return jsonify({'error': 'Прикрепите накладную'}), 400
        
        # Проверяем, существует ли уже такой материал
        existing_material = Material.query.filter_by(name=name, unit=unit).first()
        
        if existing_material:
            # Обновляем количество существующего материала
            existing_material.current_quantity += quantity
            material = existing_material
        else:
            # Создаем новый материал
            material = Material(
                name=name,
                unit=unit,
                current_quantity=quantity,
                min_quantity=0,
                description='Поступление на склад'
            )
            db.session.add(material)
            db.session.flush()  # Получаем ID
        
        # Получаем имя файла для записи в движение
        filename = secure_filename(file.filename) if file else 'Без файла'
        
        # Создаем движение поступления
        movement = WarehouseMovement(
            material_id=material.id,
            movement_type='add',
            quantity=quantity,
            to_user_id=current_user.userid,
            note=f'Поступление на склад. Накладная: {filename}',
            created_by=current_user.userid
        )
        db.session.add(movement)
        db.session.flush()
        
        # Создаем вложение с накладной
        if file:
            # Читаем файл в память для хранения в БД
            file.seek(0)  # Возвращаемся к началу файла
            file_data = file.read()
            
            attachment = WarehouseAttachment(
                movement_id=movement.id,
                filename=filename,  # Оригинальное имя файла
                content_type=file.content_type,
                data=file_data,
                size_bytes=len(file_data),
                uploaded_by=current_user.userid
            )
            db.session.add(attachment)
        
        db.session.commit()
        
        # Логируем действие
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Поступление на склад",
            description=f"Поступление материала {name} в количестве {quantity} {unit}",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        return jsonify({'success': True, 'message': 'Поступление успешно проведено'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка создания поступления: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@supply.route('/api/supply/movements/<uuid:movement_id>/attachments/<uuid:attachment_id>/download', methods=['GET'])
@login_required
def api_download_attachment(movement_id, attachment_id):
    if not is_supplier_or_admin():
        flash('Недостаточно прав для скачивания файла', 'error')
        return redirect(url_for('supply.warehouse_view'))
    att = WarehouseAttachment.query.filter_by(id=attachment_id, movement_id=movement_id).first()
    if not att:
        flash('Вложение не найдено', 'error')
        return redirect(url_for('supply.warehouse_view'))
    return send_file(BytesIO(att.data), mimetype=att.content_type or 'application/octet-stream', as_attachment=True, download_name=att.filename)

@supply.route('/api/supply/movements/<uuid:movement_id>/attachments/<uuid:attachment_id>/view', methods=['GET'])
@login_required
def api_view_attachment(movement_id, attachment_id):
    """Просмотр файла в браузере (без скачивания)"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав для просмотра файла'}), 403
    
    att = WarehouseAttachment.query.filter_by(id=attachment_id, movement_id=movement_id).first()
    if not att:
        return jsonify({'error': 'Вложение не найдено'}), 404
    
    # Определяем, можно ли отобразить файл в браузере
    viewable_types = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
        'text/plain', 'text/html', 'text/css', 'text/javascript',
        'application/json', 'application/xml', 'text/xml'
    ]
    
    if att.content_type in viewable_types:
        # Отправляем файл для просмотра в браузере
        return send_file(
            BytesIO(att.data), 
            mimetype=att.content_type or 'application/octet-stream', 
            as_attachment=False
        )
    else:
        # Для неподдерживаемых типов файлов предлагаем скачать
        return send_file(
            BytesIO(att.data), 
            mimetype=att.content_type or 'application/octet-stream', 
            as_attachment=True, 
            download_name=att.filename
        )

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

@supply.route('/api/supply/requests', methods=['GET'])
@login_required
def api_requests_list():
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    reqs = SupplyRequest.query.order_by(SupplyRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reqs])

@supply.route('/api/supply/requests', methods=['POST'])
@login_required
def api_requests_create():
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    data = request.get_json(force=True, silent=True) or {}
    items = data.get('items') or []
    if not items:
        return jsonify({'error': 'Нужен массив items'}), 400
    number = f"REQ-{int(datetime.utcnow().timestamp())}"
    req = SupplyRequest(
        request_number=number,
        requested_by=current_user.userid,
        notes=data.get('notes')
    )
    db.session.add(req)
    for it in items:
        material_id = it.get('material_id')
        quantity = it.get('quantity')
        unit = it.get('unit')
        if not material_id or not quantity or not unit:
            db.session.rollback()
            return jsonify({'error': 'Каждый item должен содержать material_id, quantity, unit'}), 400
        try:
            quantity = float(quantity)
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'quantity должен быть числом'}), 400
        db.session.add(SupplyRequestItem(request=req, material_id=material_id, quantity=quantity, unit=unit, note=it.get('note')))
    db.session.commit()
    return jsonify(req.to_dict()), 201

@supply.route('/api/supply/requests/<uuid:req_id>/status', methods=['PUT'])
@login_required
def api_requests_update_status(req_id):
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    req = SupplyRequest.query.get(req_id)
    if not req:
        return jsonify({'error': 'Заявка не найдена'}), 404
    data = request.get_json(force=True, silent=True) or {}
    status = (data.get('status') or '').strip()
    if status not in ('new', 'approved', 'rejected', 'fulfilled', 'cancelled'):
        return jsonify({'error': 'Недопустимый статус'}), 400
    req.status = status
    if status == 'approved':
        req.approver_id = current_user.userid
    db.session.commit()
    return jsonify(req.to_dict())
