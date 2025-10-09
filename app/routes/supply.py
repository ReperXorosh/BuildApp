from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
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
)
from app.models.users import Users
from app.models.activity_log import ActivityLog
from app.extensions import db
from app.utils.mobile_detection import is_mobile_device
from datetime import datetime, timedelta, timezone
from io import BytesIO

supply = Blueprint('supply', __name__)

@supply.context_processor
def inject_gettext():
    """Внедряет функцию gettext в контекст шаблонов"""
    def gettext(text):
        return text
    return dict(gettext=gettext)

def is_supplier_or_admin():
    """Проверяет, имеет ли пользователь права доступа к разделу снабжения (робастно по роли)"""
    if not current_user.is_authenticated:
        return False
    role = (current_user.role or '').strip().lower()
    # Разрешаем снабженца, ПТО, ген/зам директора (учитываем вариации написания)
    allowed_keywords = ['снабжен', 'пто', 'ген', 'зам']
    return any(k in role for k in allowed_keywords)

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

@supply.route('/supply/warehouse')
@login_required
def warehouse_view():
    """Страница склада: список материалов, последние движения, распределение."""
    if not is_supplier_or_admin():
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

    return render_template('supply/warehouse.html', materials=materials, recent_movements=recent_movements, allocations=allocations)

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
    """API для получения списка материалов"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    materials = Material.query.all()
    return jsonify([material.to_dict() for material in materials])

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

    # Обновление остатков материала (простая логика)
    if movement_type == 'add':
        material.current_quantity = (material.current_quantity or 0.0) + quantity
    elif movement_type in ('move', 'return'):
        # при перемещении со склада к пользователю уменьшаем склад
        material.current_quantity = (material.current_quantity or 0.0) - quantity
    elif movement_type == 'writeoff':
        material.current_quantity = (material.current_quantity or 0.0) - quantity

    # Обновляем распределение по пользователям
    if to_user_id:
        alloc = UserMaterialAllocation.query.filter_by(user_id=to_user_id, material_id=material.id).first()
        if not alloc:
            alloc = UserMaterialAllocation(user_id=to_user_id, material_id=material.id, quantity=0.0)
            db.session.add(alloc)
        alloc.quantity = (alloc.quantity or 0.0) + quantity
    if from_user_id:
        alloc_from = UserMaterialAllocation.query.filter_by(user_id=from_user_id, material_id=material.id).first()
        if alloc_from:
            alloc_from.quantity = max(0.0, (alloc_from.quantity or 0.0) - quantity)

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

    return jsonify({
        'movement': movement.to_dict(),
        'material': material.to_dict(),
    }), 201

@supply.route('/api/supply/movements', methods=['GET'])
@login_required
def api_list_movements():
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    q = WarehouseMovement.query.order_by(WarehouseMovement.created_at.desc()).limit(200).all()
    return jsonify([m.to_dict() for m in q])

@supply.route('/api/supply/users/search', methods=['GET'])
@login_required
def api_search_users():
    """Поиск пользователей по имени/фамилии/логину"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    # Поиск по имени, фамилии, логину
    users = Users.query.filter(
        db.or_(
            Users.first_name.ilike(f'%{query}%'),
            Users.last_name.ilike(f'%{query}%'),
            Users.login.ilike(f'%{query}%'),
            db.func.concat(Users.first_name, ' ', Users.last_name).ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': str(user.userid),
        'name': f"{user.first_name} {user.last_name}".strip(),
        'login': user.login,
        'display': f"{user.first_name} {user.last_name} ({user.login})".strip()
    } for user in users])

@supply.route('/api/supply/users/all', methods=['GET'])
@login_required
def api_get_all_users():
    """Получение всех пользователей для аккордеона"""
    if not is_supplier_or_admin():
        return jsonify({'error': 'Недостаточно прав'}), 403
    
    try:
        # Получаем всех пользователей, отсортированных по фамилии
        users = Users.query.order_by(Users.last_name, Users.first_name).all()
        
        print(f"API: Найдено {len(users)} пользователей в БД")
        
        result = []
        for user in users:
            user_data = {
                'id': str(user.userid),
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
                'login': user.login or '',
                'display': f"{user.first_name or ''} {user.last_name or ''} ({user.login or ''})".strip(),
                'role': user.role or 'Не указана'
            }
            result.append(user_data)
            print(f"API: Пользователь - {user_data['display']}")
        
        print(f"API: Возвращаем {len(result)} пользователей")
        return jsonify(result)
        
    except Exception as e:
        print(f"API: Ошибка при получении пользователей: {e}")
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
