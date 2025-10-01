from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db, cache
from app.models.objects import Object, Support, Trench, Report, Checklist, ChecklistItem, PlannedWork, WorkExecution, WorkComparison, ZDF, Bracket, Luminaire, DailyReport
from app.models.activity_log import ActivityLog
from datetime import datetime
import uuid
import os
import json
from werkzeug.utils import secure_filename

objects_bp = Blueprint('objects', __name__)

def is_pto_engineer(user):
    """Проверяет, является ли пользователь инженером ПТО"""
    return user and user.role and 'ПТО' in user.role.upper()

def translate_work_type(work_type):
    """Переводит тип работы с английского на русский"""
    translations = {
        'support_installation': 'Установка опоры',
        'trench_excavation': 'Рытье траншеи',
        'cable_laying': 'Укладка кабеля',
        'equipment_installation': 'Монтаж оборудования',
        'testing': 'Тестирование',
        'maintenance': 'Обслуживание',
        'repair': 'Ремонт',
        'inspection': 'Осмотр',
        'other': 'Другое'
    }
    return translations.get(work_type, work_type)

def translate_priority(priority):
    """Переводит приоритет с английского на русский"""
    translations = {
        'low': 'Низкий',
        'medium': 'Средний',
        'high': 'Высокий',
        'urgent': 'Срочно'
    }
    return translations.get(priority, priority)

def get_work_type_badge_class(work_type):
    """Возвращает CSS класс для бейджа типа работы"""
    badge_classes = {
        'support_installation': 'bg-primary',
        'trench_excavation': 'bg-warning',
        'cable_laying': 'bg-info',
        'equipment_installation': 'bg-success',
        'testing': 'bg-secondary',
        'maintenance': 'bg-dark',
        'repair': 'bg-danger',
        'inspection': 'bg-light text-dark',
        'other': 'bg-secondary'
    }
    return badge_classes.get(work_type, 'bg-secondary')

def get_priority_badge_class(priority):
    """Возвращает CSS класс для бейджа приоритета"""
    badge_classes = {
        'low': 'bg-success',
        'medium': 'bg-warning',
        'high': 'bg-danger',
        'urgent': 'bg-dark'
    }
    return badge_classes.get(priority, 'bg-secondary')

# Настройки для загрузки файлов
UPLOAD_FOLDER = 'app/static/uploads/planned_works'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'dwg', 'dxf', 'zip', 'rar'}

def allowed_file(filename):
    """Проверяет, разрешен ли тип файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_files(files, planned_work_id):
    """Сохраняет загруженные файлы и возвращает информацию о них"""
    if not files:
        return []
    
    # Создаем папку для файлов, если её нет
    upload_path = os.path.join(UPLOAD_FOLDER, str(planned_work_id))
    os.makedirs(upload_path, exist_ok=True)
    
    saved_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Безопасное имя файла
            filename = secure_filename(file.filename)
            # Добавляем timestamp для уникальности
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}{ext}"
            
            # Сохраняем файл
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            # Сохраняем информацию о файле
            file_info = {
                'original_name': file.filename,
                'saved_name': filename,
                'file_path': f"uploads/planned_works/{planned_work_id}/{filename}",
                'file_size': file.content_length or 0,
                'upload_date': datetime.now().isoformat()
            }
            saved_files.append(file_info)
    
    return saved_files

@objects_bp.context_processor
def inject_gettext():
    """Внедряет функцию gettext в контекст шаблонов"""
    def gettext(text):
        return text
    return dict(
        gettext=gettext,
        translate_work_type=translate_work_type,
        translate_priority=translate_priority,
        get_work_type_badge_class=get_work_type_badge_class,
        get_priority_badge_class=get_priority_badge_class
    )

@objects_bp.route('/')
@login_required
@cache.cached(timeout=30, query_string=True)
def object_list():
    """Список всех объектов"""
    # Пагинация и выбор только нужных полей для ускорения ответа
    from sqlalchemy.orm import load_only
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = max(10, min(per_page, 100))

    query = Object.query.options(
        load_only(Object.id, Object.name, Object.location, Object.status, Object.created_at)
    )
    
    query = query.order_by(Object.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    objects = pagination.items
    
    # Логируем просмотр списка объектов
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр списка объектов",
        description=f"Пользователь {current_user.login} просмотрел список объектов",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Определяем, нужно ли использовать мобильный шаблон
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_object_list.html', objects=objects, active_page='objects', pagination=pagination)
    else:
        return render_template('objects/object_list.html', objects=objects, active_page='objects', pagination=pagination)

@objects_bp.route('/planned-works-overview')
@login_required
@cache.cached(timeout=60, query_string=True)
def planned_works_overview():
    """Обзор всех запланированных работ по объектам"""
    # Обновляем статус просроченных работ
    PlannedWork.update_overdue_works()
    
    # Обновляем статус просроченных траншей
    Trench.update_overdue_trenches()
    
    # Получаем все объекты с их запланированными работами
    objects = Object.query.all()
    
    # Отладочная информация
    print(f"DEBUG: Найдено объектов: {len(objects)}")
    
    # Подсчитываем статистику по каждому объекту
    for obj in objects:
        obj.planned_works_count = len(obj.planned_works)
        obj.completed_works_count = len([w for w in obj.planned_works if w.status == 'completed'])
        obj.pending_works_count = len([w for w in obj.planned_works if w.status == 'planned'])
        obj.in_progress_works_count = len([w for w in obj.planned_works if w.status == 'in_progress'])
        obj.overdue_works_count = len([w for w in obj.planned_works if w.status == 'overdue'])
        
        print(f"DEBUG: Объект '{obj.name}' - запланированных работ: {obj.planned_works_count}")
        for work in obj.planned_works:
            print(f"DEBUG:   - Работа: {work.work_title}, тип: {work.work_type}, статус: {work.status}")
    
    # Логируем просмотр обзора запланированных работ
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр обзора запланированных работ",
        description=f"Пользователь {current_user.login} просмотрел обзор запланированных работ",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Определяем, нужно ли использовать мобильный шаблон
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_planned_works_overview.html', objects=objects, active_page='planned_works')
    else:
        return render_template('objects/planned_works_overview.html', objects=objects)

@objects_bp.route('/all-planned-works')
@login_required
def all_planned_works():
    """Список всех запланированных работ в виде таблицы"""
    # Обновляем статус просроченных работ
    PlannedWork.update_overdue_works()
    
    # Обновляем статус просроченных траншей
    Trench.update_overdue_trenches()
    
    # Получаем параметр фильтра по объекту
    object_filter = request.args.get('object_id', '')
    
    # Получаем все объекты для фильтра
    all_objects = Object.query.order_by(Object.name.asc()).all()
    
    # Вычисляем статистику для каждого объекта
    for obj in all_objects:
        obj.planned_works_count = len(obj.planned_works)
        obj.completed_works_count = len([w for w in obj.planned_works if w.status == 'completed'])
        obj.pending_works_count = len([w for w in obj.planned_works if w.status == 'planned'])
        obj.in_progress_works_count = len([w for w in obj.planned_works if w.status == 'in_progress'])
        obj.overdue_works_count = len([w for w in obj.planned_works if w.status == 'overdue'])
    
    # Базовый запрос
    query = PlannedWork.query.join(Object)
    
    # Применяем фильтр по объекту, если указан
    if object_filter:
        query = query.filter(PlannedWork.object_id == object_filter)
    
    # Получаем отфильтрованные работы
    planned_works = query.order_by(PlannedWork.planned_date.asc()).all()
    
    # Логируем просмотр всех запланированных работ
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр всех запланированных работ",
        description=f"Пользователь {current_user.login} просмотрел список всех запланированных работ" + 
                   (f" (фильтр по объекту: {object_filter})" if object_filter else ""),
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Проверяем, является ли пользователь инженером ПТО
    is_pto = is_pto_engineer(current_user)
    
    # Определяем, нужно ли использовать мобильный шаблон
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_all_planned_works.html', 
                             planned_works=planned_works, 
                             all_objects=all_objects,
                             selected_object_id=object_filter,
                             is_pto=is_pto,
                             active_page='planned_works')
    else:
        return render_template('objects/all_planned_works.html', 
                             planned_works=planned_works, 
                             all_objects=all_objects,
                             selected_object_id=object_filter,
                             is_pto=is_pto)

@objects_bp.route('/debug/planned-works')
@login_required
def debug_planned_works():
    """Отладочный маршрут для проверки запланированных работ"""
    # Получаем все запланированные работы
    all_works = PlannedWork.query.all()
    
    # Получаем все траншеи
    all_trenches = Trench.query.all()
    
    debug_info = {
        'total_planned_works': len(all_works),
        'total_trenches': len(all_trenches),
        'planned_works': [],
        'trenches': []
    }
    
    for work in all_works:
        debug_info['planned_works'].append({
            'id': work.id,
            'work_type': work.work_type,
            'work_title': work.work_title,
            'object_id': work.object_id,
            'status': work.status,
            'planned_date': str(work.planned_date) if work.planned_date else None
        })
    
    for trench in all_trenches:
        debug_info['trenches'].append({
            'id': trench.id,
            'object_id': trench.object_id,
            'planned_work_id': trench.planned_work_id,
            'planned_length': trench.planned_length,
            'current_length': trench.current_length
        })
    
    return jsonify(debug_info)

@objects_bp.route('/debug/db-structure')
@login_required
def debug_db_structure():
    """Отладочный маршрут для проверки структуры базы данных"""
    try:
        # Проверяем существование таблиц
        from sqlalchemy import text
        
        # Проверяем таблицу planned_works
        result = db.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'planned_works'
        """))
        planned_works_exists = result.fetchone() is not None
        
        # Проверяем таблицу trenches
        result = db.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'trenches'
        """))
        trenches_exists = result.fetchone() is not None
        
        # Проверяем колонки в таблице trenches
        result = db.session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'trenches'
            ORDER BY ordinal_position
        """))
        trenches_columns = [dict(row) for row in result.fetchall()]
        
        # Проверяем колонки в таблице planned_works
        planned_works_columns = []
        if planned_works_exists:
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'planned_works'
                ORDER BY ordinal_position
            """))
            planned_works_columns = [dict(row) for row in result.fetchall()]
        
        debug_info = {
            'planned_works_table_exists': planned_works_exists,
            'trenches_table_exists': trenches_exists,
            'trenches_columns': trenches_columns,
            'planned_works_columns': planned_works_columns
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@objects_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_object():
    """Добавление нового объекта"""
    # Мобильный рендер
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        
        if not name:
            flash('Название объекта обязательно для заполнения', 'error')
            return render_template('objects/mobile_add_object.html' if is_mobile else 'objects/add_object.html')
        
        # Создаем новый объект
        new_object = Object(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            location=location,
            created_by=current_user.userid
        )
        
        db.session.add(new_object)
        db.session.commit()
        
        # Логируем создание объекта
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Создание объекта",
            description=f"Пользователь {current_user.login} создал объект '{name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Объект успешно создан', 'success')
        return redirect(url_for('objects.object_list'))
    
    return render_template('objects/mobile_add_object.html' if is_mobile else 'objects/add_object.html')

@objects_bp.route('/<uuid:object_id>')
@login_required
def object_detail(object_id):
    """Детальная информация об объекте"""
    obj = Object.query.get_or_404(object_id)
    
    # Логируем просмотр объекта
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр объекта",
        description=f"Пользователь {current_user.login} просмотрел объект '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_object_detail.html', object=obj)
    else:
        return render_template('objects/object_detail.html', object=obj)

@objects_bp.route('/<uuid:object_id>/elements')
@login_required
@cache.cached(timeout=60, query_string=True)
def elements_list(object_id):
    """Список элементов объекта (ЗДФ, кронштейны, светильники)"""
    obj = Object.query.get_or_404(object_id)
    
    # Загружаем элементы объекта узкой выборкой полей для ускорения
    from ..models.objects import ZDF, Bracket, Luminaire
    from sqlalchemy.orm import load_only
    
    zdf_list = (
        ZDF.query
        .options(load_only(ZDF.id, ZDF.zdf_name, ZDF.status, ZDF.object_id))
        .filter_by(object_id=object_id)
        .order_by(ZDF.zdf_name.asc())
        .all()
    )
    brackets_list = (
        Bracket.query
        .options(load_only(Bracket.id, Bracket.bracket_name, Bracket.status, Bracket.object_id))
        .filter_by(object_id=object_id)
        .order_by(Bracket.bracket_name.asc())
        .all()
    )
    luminaires_list = (
        Luminaire.query
        .options(load_only(Luminaire.id, Luminaire.luminaire_name, Luminaire.status, Luminaire.object_id))
        .filter_by(object_id=object_id)
        .order_by(Luminaire.luminaire_name.asc())
        .all()
    )
    
    # Добавляем списки к объекту для удобства в шаблонах
    obj.zdfs = zdf_list
    obj.brackets = brackets_list
    obj.luminaires = luminaires_list
    
    # Логирование активности
    from ..models.activity_log import ActivityLog
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр элементов объекта",
        description=f"Пользователь {current_user.login} просмотрел элементы объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_elements_list.html', object=obj)
    else:
        return render_template('objects/elements_list.html', object=obj)

# Маршруты для опор
@objects_bp.route('/<uuid:object_id>/supports')
@login_required
def supports_list(object_id):
    """Список опор объекта"""
    obj = Object.query.get_or_404(object_id)
    from sqlalchemy.orm import load_only
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = max(10, min(per_page, 100))
    query = Support.query.options(
        load_only(Support.id, Support.support_number, Support.support_type, Support.status, Support.created_at, Support.object_id)
    ).filter_by(object_id=object_id).order_by(Support.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    supports = pagination.items
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр опор",
        description=f"Пользователь {current_user.login} просмотрел опоры объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_supports_list.html', object=obj, supports=supports, pagination=pagination)
    else:
        return render_template('objects/supports_list.html', object=obj, supports=supports, pagination=pagination)

@objects_bp.route('/<uuid:object_id>/supports/add', methods=['GET', 'POST'])
@login_required
def add_support(object_id):
    """Добавление опоры (только для инженера ПТО)"""
    obj = Object.query.get_or_404(object_id)
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device() or (request.args.get('mobile') == '1')
    
    # Получаем данные о ЗДФ, Кронштейнах и Светильниках для данного объекта
    zdf_list = ZDF.query.filter_by(object_id=object_id).order_by(ZDF.zdf_number.asc()).all()
    brackets_list = Bracket.query.filter_by(object_id=object_id).order_by(Bracket.bracket_number.asc()).all()
    luminaires_list = Luminaire.query.filter_by(object_id=object_id).order_by(Luminaire.luminaire_number.asc()).all()
    
    # Проверяем права доступа - только инженер ПТО может добавлять опоры
    if current_user.role != 'Инженер ПТО':
        flash('У вас нет прав для добавления опор. Только инженер ПТО может добавлять опоры по проекту.', 'error')
        return redirect(url_for('objects.supports_list', object_id=object_id))
    
    if request.method == 'POST':
        support_number = request.form.get('support_number', '').strip()
        support_type = request.form.get('support_type', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not support_number:
            flash('Номер опоры обязателен для заполнения', 'error')
            return render_template('objects/mobile_add_support.html' if is_mobile else 'objects/add_support.html', object=obj, zdf_list=zdf_list, brackets_list=brackets_list, luminaires_list=luminaires_list)
        
        new_support = Support(
            id=str(uuid.uuid4()),
            object_id=object_id,
            support_number=support_number,
            support_type=support_type,
            height=None,  # Убираем высоту
            material=None,  # Убираем материал
            installation_date=None,  # Дата установки будет заполняться при подтверждении
            status='planned',  # Статус по умолчанию - запланировано
            notes=notes,
            created_by=current_user.userid
        )
        
        db.session.add(new_support)
        db.session.flush()  # Получаем ID опоры для создания запланированной работы
        
        # Создаем запланированную работу для установки опоры
        planned_work = PlannedWork(
            id=str(uuid.uuid4()),
            object_id=object_id,
            work_type='support_installation',
            work_title=f'Установка опоры {support_number}',
            description=f'Установка опоры {support_number}' + (f' ({support_type})' if support_type else ''),
            planned_date=None,  # Без конкретной даты - дату можно будет установить позже
            priority='medium',
            status='planned',
            created_by=current_user.userid,
            notes=f'Автоматически создано при добавлении опоры {support_number}'
        )
        
        db.session.add(planned_work)
        db.session.flush()  # Получаем ID запланированной работы
        
        # Связываем опору с запланированной работой
        new_support.planned_work_id = planned_work.id
        
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление опоры по проекту",
            description=f"Инженер ПТО {current_user.login} добавил опору {support_number} к объекту '{obj.name}' и автоматически создал запланированную работу для её установки",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Опора по проекту успешно добавлена. Запланированная работа для установки опоры создана автоматически.', 'success')
        return redirect(url_for('objects.supports_list', object_id=object_id))
    
    return render_template('objects/mobile_add_support.html' if is_mobile else 'objects/add_support.html', object=obj, zdf_list=zdf_list, brackets_list=brackets_list, luminaires_list=luminaires_list)

@objects_bp.route('/<uuid:object_id>/elements/add', methods=['GET', 'POST'])
@login_required
def add_element(object_id):
    """Добавление элемента (ЗДФ, Кронштейн, Светильник) - только для инженера ПТО"""
    obj = Object.query.get_or_404(object_id)
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device()
    
    # Проверяем права доступа - только инженер ПТО может добавлять элементы
    if current_user.role != 'Инженер ПТО':
        flash('У вас нет прав для добавления элементов. Только инженер ПТО может добавлять элементы по проекту.', 'error')
        return redirect(url_for('objects.elements_list', object_id=object_id))
    
    if request.method == 'POST':
        element_type = request.form.get('element_type', '').strip()
        element_name = request.form.get('element_name', '').strip()
        notes = request.form.get('notes', '').strip()
        file_url = None
        # Обработка вложения
        if 'attachment' in request.files:
            from werkzeug.utils import secure_filename
            file = request.files.get('attachment')
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Каталог для элементов
                import os
                upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads', 'elements')
                upload_dir = os.path.normpath(upload_dir)
                os.makedirs(upload_dir, exist_ok=True)
                # Уникализируем имя
                import uuid as _uuid
                name, ext = os.path.splitext(filename)
                safe_name = f"{_uuid.uuid4().hex}{ext.lower()}"
                save_path = os.path.join(upload_dir, safe_name)
                file.save(save_path)
                # URL для доступа из браузера
                file_url = f"/static/uploads/elements/{safe_name}"
        
        if not element_type:
            flash('Тип элемента обязателен для заполнения', 'error')
            return render_template('objects/mobile_add_element.html' if is_mobile else 'objects/add_element.html', object=obj)
        
        # Создаем элемент в зависимости от типа
        if element_type == 'zdf':
            new_element = ZDF(
                id=str(uuid.uuid4()),
                object_id=object_id,
                zdf_number='',
                zdf_name=element_name,
                status='planned',
                notes=notes,
                created_by=current_user.userid
            )
            element_type_name = 'ЗДФ'
        elif element_type == 'bracket':
            new_element = Bracket(
                id=str(uuid.uuid4()),
                object_id=object_id,
                bracket_number='',
                bracket_name=element_name,
                status='planned',
                notes=notes,
                created_by=current_user.userid
            )
            element_type_name = 'Кронштейн'
        elif element_type == 'luminaire':
            new_element = Luminaire(
                id=str(uuid.uuid4()),
                object_id=object_id,
                luminaire_number='',
                luminaire_name=element_name,
                status='planned',
                notes=notes,
                created_by=current_user.userid
            )
            element_type_name = 'Светильник'
        else:
            flash('Неверный тип элемента', 'error')
            return render_template('objects/mobile_add_element.html' if is_mobile else 'objects/add_element.html', object=obj)
        
        # Если есть файл, добавим ссылку в примечания (не теряем введённые заметки)
        if file_url:
            attach_note = f"\nФайл: {file_url}"
            notes = (notes or '') + attach_note
        new_element.notes = notes
        db.session.add(new_element)
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление элемента",
            description=f"Пользователь {current_user.login} добавил {element_type_name} к объекту '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash(f'{element_type_name} успешно добавлен', 'success')
        return redirect(url_for('objects.elements_list', object_id=object_id))
    
    return render_template('objects/mobile_add_element.html' if is_mobile else 'objects/add_element.html', object=obj)

@objects_bp.route('/<uuid:object_id>/supports/<uuid:support_id>')
@login_required
def support_detail(object_id, support_id):
    """Просмотр деталей опоры"""
    obj = Object.query.get_or_404(object_id)
    support = Support.query.get_or_404(support_id)
    
    if support.object_id != object_id:
        abort(404)
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр деталей опоры",
        description=f"Пользователь {current_user.login} просмотрел детали опоры {support.support_number}",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    from ..utils.mobile_detection import is_mobile_device
    # Проверяем параметр mobile=1 или определяем по User-Agent
    mobile_param = request.args.get('mobile') == '1'
    device_mobile = is_mobile_device()
    is_mobile = mobile_param or device_mobile
    
    print(f"DEBUG support_detail: mobile_param = {mobile_param}, device_mobile = {device_mobile}, is_mobile = {is_mobile}")
    print(f"DEBUG support_detail: User-Agent = {request.headers.get('User-Agent', '')}")
    
    if is_mobile:
        print("DEBUG support_detail: Rendering mobile template")
        return render_template('objects/mobile_support_detail.html', object=obj, support=support)
    else:
        print("DEBUG support_detail: Rendering desktop template")
        return render_template('objects/support_detail.html', object=obj, support=support)
# Детальная страница элемента (ЗДФ, Кронштейн, Светильник)
@objects_bp.route('/<uuid:object_id>/elements/<string:element_type>/<uuid:element_id>')
@login_required
def element_detail(object_id, element_type, element_id):
    obj = Object.query.get_or_404(object_id)
    element_type = (element_type or '').lower()

    element = None
    title = 'Элемент'
    if element_type == 'zdf':
        element = ZDF.query.get_or_404(element_id)
        if element.object_id != object_id:
            abort(404)
        title = 'ЗДФ'
    elif element_type == 'bracket':
        element = Bracket.query.get_or_404(element_id)
        if element.object_id != object_id:
            abort(404)
        title = 'Кронштейн'
    elif element_type == 'luminaire':
        element = Luminaire.query.get_or_404(element_id)
        if element.object_id != object_id:
            abort(404)
        title = 'Светильник'
    else:
        abort(404)

    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action=f"Просмотр элемента: {title}",
        description=f"Пользователь {current_user.login} просмотрел элемент '{title}' объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )

    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device() or (request.args.get('mobile') == '1')
    template = 'objects/mobile_element_detail.html' if is_mobile else 'objects/element_detail.html'
    return render_template(template, object=obj, element=element, element_type=title)

@objects_bp.route('/<uuid:object_id>/supports/<uuid:support_id>/confirm-installation', methods=['GET', 'POST'])
@login_required
def confirm_support_installation(object_id, support_id):
    """Подтверждение установки опоры"""
    obj = Object.query.get_or_404(object_id)
    support = Support.query.get_or_404(support_id)
    
    if support.object_id != object_id:
        abort(404)
    
    if support.status == 'completed':
        flash('Эта опора уже установлена', 'info')
        return redirect(url_for('objects.support_detail', object_id=object_id, support_id=support_id))
    
    if request.method == 'POST':
        installation_date = request.form.get('installation_date')
        installation_notes = request.form.get('installation_notes', '').strip()
        
        # Проверяем, что дата указана
        if not installation_date:
            flash('Дата установки обязательна для заполнения', 'error')
            from ..utils.mobile_detection import is_mobile_device
            mobile_param = request.args.get('mobile') == '1'
            device_mobile = is_mobile_device()
            is_mobile = mobile_param or device_mobile
            if is_mobile:
                return render_template('objects/mobile_confirm_support_installation.html', object=obj, support=support, today_date=datetime.now().strftime('%Y-%m-%d'))
            else:
                return render_template('objects/confirm_support_installation.html', object=obj, support=support, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        try:
            installation_date = datetime.strptime(installation_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Некорректный формат даты', 'error')
            from ..utils.mobile_detection import is_mobile_device
            mobile_param = request.args.get('mobile') == '1'
            device_mobile = is_mobile_device()
            is_mobile = mobile_param or device_mobile
            if is_mobile:
                return render_template('objects/mobile_confirm_support_installation.html', object=obj, support=support, today_date=datetime.now().strftime('%Y-%m-%d'))
            else:
                return render_template('objects/confirm_support_installation.html', object=obj, support=support, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # Обновляем статус опоры
        support.status = 'completed'
        support.installation_date = installation_date
        support.notes = (support.notes or '') + f'\n\nУстановка подтверждена: {installation_date.strftime("%d.%m.%Y")}'
        if installation_notes:
            support.notes += f'\nПримечания по установке: {installation_notes}'
        support.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Подтверждение установки опоры",
            description=f"Пользователь {current_user.login} подтвердил установку опоры {support.support_number}",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Установка опоры успешно подтверждена', 'success')
        # Сохраняем параметр mobile при редиректе
        mobile_param = request.args.get('mobile') == '1'
        if mobile_param:
            return redirect(url_for('objects.support_detail', object_id=object_id, support_id=support_id, mobile=1))
        else:
            return redirect(url_for('objects.support_detail', object_id=object_id, support_id=support_id))
    
    from ..utils.mobile_detection import is_mobile_device
    # Проверяем параметр mobile=1 или определяем по User-Agent
    mobile_param = request.args.get('mobile') == '1'
    device_mobile = is_mobile_device()
    is_mobile = mobile_param or device_mobile
    
    print(f"DEBUG confirm_support_installation: mobile_param = {mobile_param}, device_mobile = {device_mobile}, is_mobile = {is_mobile}")
    print(f"DEBUG confirm_support_installation: User-Agent = {request.headers.get('User-Agent', '')}")
    
    if is_mobile:
        print("DEBUG confirm_support_installation: Rendering mobile template")
        return render_template('objects/mobile_confirm_support_installation.html', object=obj, support=support, today_date=datetime.now().strftime('%Y-%m-%d'))
    else:
        print("DEBUG confirm_support_installation: Rendering desktop template")
        return render_template('objects/confirm_support_installation.html', object=obj, support=support, today_date=datetime.now().strftime('%Y-%m-%d'))

# Маршруты для траншей
@objects_bp.route('/<uuid:object_id>/trenches')
@login_required
def trenches_list(object_id):
    """Список траншей объекта"""
    obj = Object.query.get_or_404(object_id)
    from sqlalchemy.orm import load_only
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = max(10, min(per_page, 100))
    query = Trench.query.options(
        load_only(Trench.id, Trench.planned_length, Trench.current_length, Trench.status, Trench.excavation_date, Trench.created_at, Trench.object_id)
    ).filter_by(object_id=object_id).order_by(Trench.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    trenches = pagination.items
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр траншей",
        description=f"Пользователь {current_user.login} просмотрел траншеи объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_trenches_list.html', object=obj, trenches=trenches, pagination=pagination)
    else:
        return render_template('objects/trenches_list.html', object=obj, trenches=trenches, pagination=pagination)

@objects_bp.route('/<uuid:object_id>/trenches/add', methods=['GET', 'POST'])
@login_required
def add_trench(object_id):
    """Добавление траншеи"""
    obj = Object.query.get_or_404(object_id)
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device()
    
    if request.method == 'POST':
        planned_length = request.form.get('planned_length')
        current_length = request.form.get('current_length')
        width = request.form.get('width')
        depth = request.form.get('depth')
        soil_type = request.form.get('soil_type', '').strip()
        excavation_date = request.form.get('excavation_date')
        notes = request.form.get('notes', '').strip()
        
        if not planned_length:
            flash('Запланированная длина обязательна для заполнения', 'error')
            return render_template('objects/mobile_add_trench.html' if is_mobile else 'objects/add_trench.html', object=obj)
        
        # Преобразуем дату
        if excavation_date:
            try:
                excavation_date = datetime.strptime(excavation_date, '%Y-%m-%d').date()
            except ValueError:
                excavation_date = None
        
        # Преобразуем числовые значения
        try:
            planned_length = float(planned_length) if planned_length else 0.0
            current_length = float(current_length) if current_length else 0.0
            width = float(width) if width else None
            depth = float(depth) if depth else None
        except ValueError:
            flash('Некорректные числовые значения', 'error')
            return render_template('objects/mobile_add_trench.html' if is_mobile else 'objects/add_trench.html', object=obj)
        
        # Проверяем валидность значений
        if planned_length <= 0:
            flash('Запланированная длина должна быть больше 0', 'error')
            return render_template('objects/mobile_add_trench.html' if is_mobile else 'objects/add_trench.html', object=obj)
        
        if current_length > planned_length:
            flash('Текущая длина не может быть больше запланированной', 'error')
            return render_template('objects/mobile_add_trench.html' if is_mobile else 'objects/add_trench.html', object=obj)
        
        new_trench = Trench(
            id=str(uuid.uuid4()),
            object_id=object_id,
            planned_length=planned_length,
            current_length=current_length,
            width=width,
            depth=depth,
            soil_type=soil_type,
            excavation_date=excavation_date,
            notes=notes,
            created_by=current_user.userid
        )
        
        # Проверяем и устанавливаем статус завершения
        new_trench.check_completion_status()
        
        db.session.add(new_trench)
        db.session.flush()  # Получаем ID траншеи
        
        # Создаём запланированную работу на рытьё траншеи
        work_date = excavation_date if excavation_date else datetime.utcnow().date()
        
        planned_work = PlannedWork(
            id=str(uuid.uuid4()),
            object_id=object_id,
            work_type='trench_excavation',
            work_title=f'Рытьё траншеи длиной {planned_length}м',
            description=f'Рытьё траншеи: длина {planned_length}м, ширина {width or "не указана"}м, глубина {depth or "не указана"}м. Тип грунта: {soil_type or "не указан"}. {notes or ""}',
            planned_date=work_date,
            priority='medium',
            status='planned',
            location_details=f'Объект: {obj.name}',
            notes=f'Автоматически создано при добавлении траншеи. Траншея ID: {new_trench.id}',
            created_by=current_user.userid
        )
        
        try:
            db.session.add(planned_work)
            db.session.flush()  # Получаем ID запланированной работы
            
            # Связываем траншею с запланированной работой
            new_trench.planned_work_id = planned_work.id
            
            # Логируем для отладки
            print(f"DEBUG: Создана траншея ID: {new_trench.id}")
            print(f"DEBUG: Создана запланированная работа ID: {planned_work.id}")
            print(f"DEBUG: Траншея связана с работой: {new_trench.planned_work_id}")
            
            db.session.commit()
            
            # Проверяем после коммита
            print(f"DEBUG: После коммита - траншея ID: {new_trench.id}, planned_work_id: {new_trench.planned_work_id}")
            print(f"DEBUG: Запланированная работа существует: {PlannedWork.query.get(planned_work.id) is not None}")
            
        except Exception as e:
            print(f"ERROR: Ошибка при создании запланированной работы: {e}")
            db.session.rollback()
            flash(f'Ошибка при создании запланированной работы: {e}', 'error')
            return render_template('objects/add_trench.html', object=obj)
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление траншеи",
            description=f"Пользователь {current_user.login} добавил траншею длиной {planned_length}м к объекту '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        if excavation_date:
            flash(f'Траншея успешно добавлена. Запланирована работа на рытьё траншеи на {work_date.strftime("%d.%m.%Y")}', 'success')
        else:
            flash(f'Траншея успешно добавлена. Запланирована работа на рытьё траншеи на {work_date.strftime("%d.%m.%Y")}', 'success')
        
        return redirect(url_for('objects.trenches_list', object_id=object_id))
    
    return render_template('objects/mobile_add_trench.html' if is_mobile else 'objects/add_trench.html', object=obj)

# Маршруты для отчётов
@objects_bp.route('/<uuid:object_id>/reports')
@login_required
@cache.cached(timeout=60, query_string=True)
def reports_list(object_id):
    """Список отчётов объекта"""
    obj = Object.query.get_or_404(object_id)
    from sqlalchemy.orm import load_only
    # Пагинация основных отчётов
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = max(10, min(per_page, 100))
    reports_query = Report.query.options(
        load_only(Report.id, Report.report_number, Report.title, Report.report_type, Report.report_date, Report.created_at, Report.object_id)
    ).filter_by(object_id=object_id).order_by(Report.created_at.desc())
    reports_pagination = reports_query.paginate(page=page, per_page=per_page, error_out=False)
    reports = reports_pagination.items
    
    # Последние 30 дней daily_reports (без пагинации, но с выбором полей)
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    daily_reports = DailyReport.query.options(
        load_only(DailyReport.id, DailyReport.report_date, DailyReport.object_id)
    ).filter_by(object_id=object_id).filter(
        DailyReport.report_date >= thirty_days_ago
    ).order_by(DailyReport.report_date.desc()).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр отчётов",
        description=f"Пользователь {current_user.login} просмотрел отчёты объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    from ..utils.mobile_detection import is_mobile_device
    if is_mobile_device():
        return render_template('objects/mobile_reports_list.html', object=obj, reports=reports, daily_reports=daily_reports, today=date.today(), pagination=reports_pagination)
    else:
        return render_template('objects/reports_list.html', object=obj, reports=reports, daily_reports=daily_reports, today=date.today(), pagination=reports_pagination)

@objects_bp.route('/<uuid:object_id>/reports/add', methods=['GET', 'POST'])
@login_required
def add_report(object_id):
    """Добавление отчёта"""
    obj = Object.query.get_or_404(object_id)
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device()
    
    if request.method == 'POST':
        report_number = request.form.get('report_number', '').strip()
        report_type = request.form.get('report_type', '').strip()
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        report_date = request.form.get('report_date')
        notes = request.form.get('notes', '').strip()
        
        if not report_number or not title:
            flash('Номер отчёта и заголовок обязательны для заполнения', 'error')
            return render_template('objects/mobile_add_report.html' if is_mobile else 'objects/add_report.html', object=obj, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # Преобразуем дату
        if report_date:
            try:
                report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
            except ValueError:
                report_date = datetime.utcnow().date()
        
        new_report = Report(
            id=str(uuid.uuid4()),
            object_id=object_id,
            report_number=report_number,
            report_type=report_type,
            title=title,
            content=content,
            report_date=report_date,
            notes=notes,
            created_by=current_user.userid
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление отчёта",
            description=f"Пользователь {current_user.login} добавил отчёт {report_number} к объекту '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Отчёт успешно добавлен', 'success')
        return redirect(url_for('objects.reports_list', object_id=object_id))
    
    return render_template('objects/mobile_add_report.html' if is_mobile else 'objects/add_report.html', object=obj, today_date=datetime.now().strftime('%Y-%m-%d'))



@objects_bp.route('/<uuid:object_id>/checklist')
@login_required
def checklist_view(object_id):
    """View checklist for a specific object"""
    obj = Object.query.get_or_404(object_id)
    
    # Get or create checklist for the object
    if not obj.checklist:
        checklist = Checklist(
            object_id=obj.id,
            created_by=current_user.userid
        )
        db.session.add(checklist)
        db.session.commit()
        # Обновляем объект в сессии, чтобы получить связь с чек-листом
        db.session.refresh(obj)
    else:
        # Обновляем счетчики для существующего чек-листа
        obj.checklist.update_completion_status()
        db.session.commit()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр чек-листа",
        description=f"Пользователь {current_user.login} просмотрел чек-лист объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Уважаем форсирование мобильной версии через параметр ?mobile=1,
    # и автоматическое определение мобильного устройства
    from ..utils.mobile_detection import is_mobile_device
    force_mobile = request.args.get('mobile') == '1'
    if force_mobile or is_mobile_device():
        return render_template('objects/mobile_checklist_view.html', object=obj, checklist=obj.checklist)
    return render_template('objects/checklist_view.html', object=obj, checklist=obj.checklist)

@objects_bp.route('/<uuid:object_id>/checklist/add-item', methods=['GET', 'POST'])
@login_required
def add_checklist_item(object_id):
    """Add a new checklist item (PTO Engineer only)"""
    if current_user.role != 'Инженер ПТО':
        abort(403)
    
    obj = Object.query.get_or_404(object_id)
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device()
    
    if request.method == 'POST':
        item_text = request.form.get('item_text', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not item_text:
            flash('Текст позиции обязателен для заполнения', 'error')
            return render_template('objects/mobile_add_checklist_item.html' if is_mobile else 'objects/add_checklist_item.html', object=obj)
        
        # Get or create checklist for the object
        if not obj.checklist:
            checklist = Checklist(
                object_id=obj.id,
                created_by=current_user.userid
            )
            db.session.add(checklist)
            db.session.commit()
            obj.checklist = checklist
        
        # Получаем текущее количество с проверкой на пустые значения
        current_quantity_str = request.form.get('current_quantity', '0.0')
        if not current_quantity_str or current_quantity_str.strip() == '':
            current_quantity = 0.0
        else:
            try:
                current_quantity = float(current_quantity_str)
                if current_quantity < 0:
                    current_quantity = 0.0
            except ValueError:
                current_quantity = 0.0
        
        # Получаем планируемое количество с проверкой на пустые значения
        quantity_str = request.form.get('quantity', '1.0')
        if not quantity_str or quantity_str.strip() == '':
            quantity = 1.0
        else:
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    flash('Планируемое количество должно быть положительным числом (больше 0)', 'error')
                    return render_template('objects/add_checklist_item.html', object=obj)
            except ValueError:
                flash('Планируемое количество должно быть числом', 'error')
                return render_template('objects/add_checklist_item.html', object=obj)
        
        # Получаем единицу измерения с проверкой на пустые значения
        unit = request.form.get('unit', 'шт')
        if not unit or unit.strip() == '':
            unit = 'шт'
        
        # Create new checklist item
        new_item = ChecklistItem(
            checklist_id=obj.checklist.id,
            item_text=item_text,
            unit=unit,
            quantity=quantity,
            current_quantity=current_quantity,
            notes=notes,
            order_index=len(obj.checklist.items) + 1
        )
        
        db.session.add(new_item)
        db.session.flush()  # Получаем ID элемента
        
        # Обновляем счетчики в чек-листе
        obj.checklist.update_completion_status()
        
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление позиции чек-листа",
            description=f"Пользователь {current_user.login} добавил позицию в чек-лист объекта '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Позиция чек-листа успешно добавлена', 'success')
        return redirect(url_for('objects.checklist_view', object_id=object_id))
    
    return render_template('objects/mobile_add_checklist_item.html' if is_mobile else 'objects/add_checklist_item.html', object=obj)

@objects_bp.route('/<uuid:object_id>/checklist/<uuid:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_checklist_item(object_id, item_id):
    """Edit a checklist item (PTO Engineer only)"""
    if current_user.role != 'Инженер ПТО':
        abort(403)
    
    obj = Object.query.get_or_404(object_id)
    item = ChecklistItem.query.get_or_404(item_id)
    
    if item.checklist.object_id != object_id:
        abort(404)
    
    # Определяем мобильное устройство для выбора шаблона
    from ..utils.mobile_detection import is_mobile_device
    is_mobile = is_mobile_device()
    
    if request.method == 'POST':
        item_text = request.form.get('item_text', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Получаем текущее количество с проверкой на пустые значения
        current_quantity_str = request.form.get('current_quantity', '0.0')
        if not current_quantity_str or current_quantity_str.strip() == '':
            current_quantity = 0.0
        else:
            try:
                current_quantity = float(current_quantity_str)
                if current_quantity < 0:
                    current_quantity = 0.0
            except ValueError:
                current_quantity = 0.0
        
        # Получаем планируемое количество с проверкой на пустые значения
        quantity_str = request.form.get('quantity', '1.0')
        if not quantity_str or quantity_str.strip() == '':
            quantity = 1.0
        else:
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    flash('Планируемое количество должно быть положительным числом (больше 0)', 'error')
                    return render_template('objects/mobile_edit_checklist_item.html' if is_mobile else 'objects/edit_checklist_item.html', object=obj, item=item)
            except ValueError:
                flash('Планируемое количество должно быть числом', 'error')
                return render_template('objects/mobile_edit_checklist_item.html' if is_mobile else 'objects/edit_checklist_item.html', object=obj, item=item)
        
        # Получаем единицу измерения с проверкой на пустые значения
        unit = request.form.get('unit', 'шт')
        if not unit or unit.strip() == '':
            unit = 'шт'
        
        if not item_text:
            flash('Текст позиции обязателен для заполнения', 'error')
            return render_template('objects/mobile_edit_checklist_item.html' if is_mobile else 'objects/edit_checklist_item.html', object=obj, item=item)
        
        item.item_text = item_text
        item.notes = notes
        item.unit = unit
        item.quantity = quantity
        item.current_quantity = current_quantity
        item.updated_at = datetime.utcnow()
        
        # Обновляем счетчики в чек-листе
        obj.checklist.update_completion_status()
        
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Редактирование позиции чек-листа",
            description=f"Пользователь {current_user.login} отредактировал позицию в чек-листе объекта '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Позиция чек-листа успешно обновлена', 'success')
        return redirect(url_for('objects.checklist_view', object_id=object_id))
    
    return render_template('objects/mobile_edit_checklist_item.html' if is_mobile else 'objects/edit_checklist_item.html', object=obj, item=item)

@objects_bp.route('/<uuid:object_id>/checklist/<uuid:item_id>/toggle', methods=['POST'])
@login_required
def toggle_checklist_item(object_id, item_id):
    """Toggle checklist item completion status"""
    obj = Object.query.get_or_404(object_id)
    item = ChecklistItem.query.get_or_404(item_id)
    
    if item.checklist.object_id != object_id:
        abort(404)
    
    try:
        data = request.get_json() or {}
        force_complete = data.get('force_complete', False)
        
        # Toggle completion status
        if item.is_completed:
            item.uncomplete()
            message = 'Позиция отмечена как невыполненная'
            is_completed = False
            completion_date = None
            completed_by = None
        else:
            # Проверяем количество
            current_qty = item.current_quantity or 0
            planned_qty = item.quantity
            
            if current_qty >= planned_qty:
                # Количество совпадает - обычное выполнение
                item.complete(user_id=current_user.userid, force=False)
                message = 'Позиция отмечена как выполненная'
                is_completed = True
                completion_date = item.completed_at.strftime('%d.%m.%Y %H:%M') if item.completed_at else None
                completed_by = current_user.login
            else:
                # Количество не совпадает
                if not force_complete:
                    # Возвращаем информацию для показа предупреждения
                    return jsonify({
                        'success': False,
                        'needs_confirmation': True,
                        'message': f'Внимание! Количество не совпадает: установлено {current_qty} из {planned_qty} {item.unit or "шт"}. Подтвердить выполнение?',
                        'current_quantity': current_qty,
                        'planned_quantity': planned_qty,
                        'unit': item.unit or 'шт'
                    })
                else:
                    # Принудительное выполнение
                    if current_user.role == 'Инженер ПТО':
                        item.complete(user_id=current_user.userid, force=True)
                        message = f'Позиция принудительно отмечена как выполненная (количество: {current_qty}/{planned_qty} {item.unit or "шт"})'
                        is_completed = True
                        completion_date = item.completed_at.strftime('%d.%m.%Y %H:%M') if item.completed_at else None
                        completed_by = current_user.login
                    else:
                        return jsonify({
                            'success': False,
                            'message': 'Только инженер ПТО может принудительно отмечать позиции как выполненные'
                        }), 403
        
        # Обновляем счетчики в чек-листе
        obj.checklist.update_completion_status()
        
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Изменение статуса позиции чек-листа",
            description=f"Пользователь {current_user.login} изменил статус позиции в чек-листе объекта '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        return jsonify({
            'success': True,
            'message': message,
            'is_completed': is_completed,
            'completion_date': completion_date,
            'completed_by': completed_by
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при изменении статуса: {str(e)}'
        }), 500

@objects_bp.route('/<uuid:object_id>/checklist/<uuid:item_id>/delete', methods=['POST'])
@login_required
def delete_checklist_item(object_id, item_id):
    """Delete a checklist item (PTO Engineer only)"""
    if current_user.role != 'Инженер ПТО':
        abort(403)
    
    object = Object.query.get_or_404(object_id)
    item = ChecklistItem.query.get_or_404(item_id)
    
    if item.checklist.object_id != object.id:
        abort(404)
    
    db.session.delete(item)
    
    # Обновляем счетчики в чек-листе
    object.checklist.update_completion_status()
    
    db.session.commit()
    
    flash('Позиция чек-листа удалена', 'success')
    return redirect(url_for('objects.checklist_view', object_id=object.id))


# Маршруты для запланированных работ
@objects_bp.route('/<uuid:object_id>/planned-works')
@login_required
@cache.cached(timeout=60, query_string=True)
def planned_works_list(object_id):
    """Список запланированных работ объекта"""
    # Обновляем статус просроченных работ
    PlannedWork.update_overdue_works()
    
    # Обновляем статус просроченных траншей
    Trench.update_overdue_trenches()
    
    obj = Object.query.get_or_404(object_id)
    
    # Пагинация и узкая выборка полей для ускорения
    from sqlalchemy.orm import load_only
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = max(10, min(per_page, 50))
    
    query = PlannedWork.query.options(
        load_only(PlannedWork.id, PlannedWork.work_type, PlannedWork.work_title, 
                 PlannedWork.planned_date, PlannedWork.priority, PlannedWork.status, 
                 PlannedWork.object_id, PlannedWork.created_at)
    ).filter_by(object_id=object_id).order_by(PlannedWork.planned_date.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    planned_works = pagination.items
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр запланированных работ",
        description=f"Пользователь {current_user.login} просмотрел запланированные работы объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Проверяем, является ли пользователь инженером ПТО
    is_pto = is_pto_engineer(current_user)
    
    return render_template('objects/planned_works_list.html', object=obj, planned_works=planned_works, pagination=pagination, is_pto=is_pto)

@objects_bp.route('/<uuid:object_id>/planned-works/add', methods=['GET', 'POST'])
@login_required
def add_planned_work(object_id):
    """Добавление запланированной работы"""
    obj = Object.query.get_or_404(object_id)
    
    # Получаем список опор для данного объекта
    supports = Support.query.filter_by(object_id=object_id, status='planned').order_by(Support.support_number.asc()).all()
    
    if request.method == 'POST':
        work_type = request.form.get('work_type', '').strip()
        work_title = request.form.get('work_title', '').strip()
        selected_support_id = request.form.get('selected_support_id', '').strip()
        description = request.form.get('description', '').strip()
        planned_date = request.form.get('planned_date')
        priority = request.form.get('priority', 'medium')
        materials_required = request.form.get('materials_required', '').strip()
        location_details = request.form.get('location_details', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Обрабатываем загруженные файлы
        location_files = request.files.getlist('location_files')
        
        if not work_type or not work_title or not planned_date:
            flash('Тип работы, заголовок и планируемая дата обязательны для заполнения', 'error')
            # Убеждаемся, что передаем правильную дату
            today_date = datetime.now().strftime('%Y-%m-%d')
            print(f"DEBUG: Передаем today_date = {today_date}")
            return render_template('objects/add_planned_work.html', object=obj, supports=supports, today_date=today_date)
        
        # Преобразуем дату
        try:
            planned_date = datetime.strptime(planned_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты', 'error')
            # Убеждаемся, что передаем правильную дату
            today_date = datetime.now().strftime('%Y-%m-%d')
            print(f"DEBUG: Передаем today_date = {today_date}")
            return render_template('objects/add_planned_work.html', object=obj, supports=supports, today_date=today_date)
        
        # Проверяем, что дата не в прошлом (строгая проверка)
        from datetime import timezone
        # Используем UTC время для консистентности
        today_utc = datetime.now(timezone.utc).date()
        today_local = datetime.now().date()
        
        print(f"DEBUG: Проверяем дату {planned_date} против {today_local}")
        
        # Проверяем как по UTC, так и по локальному времени
        if planned_date < today_utc or planned_date < today_local:
            flash(f'ОШИБКА: Нельзя планировать работу на прошедшую дату! Выбрана дата: {planned_date.strftime("%d.%m.%Y")}, а сегодня: {today_local.strftime("%d.%m.%Y")}', 'error')
            # Убеждаемся, что передаем правильную дату
            today_date = datetime.now().strftime('%Y-%m-%d')
            print(f"DEBUG: Передаем today_date = {today_date}")
            return render_template('objects/add_planned_work.html', object=obj, supports=supports, today_date=today_date)
        
        
        try:
            # Создаем ID для запланированной работы
            planned_work_id = str(uuid.uuid4())
            
            # Сохраняем загруженные файлы
            saved_files = save_uploaded_files(location_files, planned_work_id)
            location_files_json = json.dumps(saved_files) if saved_files else None
            
            new_planned_work = PlannedWork(
                id=planned_work_id,
                object_id=object_id,
                work_type=work_type,
                work_title=work_title,
                description=description,
                planned_date=planned_date,
                priority=priority,
                materials_required=materials_required,
                location_details=location_details,
                location_files=location_files_json,
                notes=notes,
                created_by=current_user.userid
            )
        except ValueError as e:
            flash(str(e), 'error')
            # Убеждаемся, что передаем правильную дату
            today_date = datetime.now().strftime('%Y-%m-%d')
            print(f"DEBUG: Передаем today_date = {today_date}")
            return render_template('objects/add_planned_work.html', object=obj, supports=supports, today_date=today_date)
        
        db.session.add(new_planned_work)
        db.session.flush()  # Получаем ID запланированной работы
        
        # Если выбрана опора, связываем её с запланированной работой
        if selected_support_id and work_type == 'support_installation':
            support = Support.query.get(selected_support_id)
            if support and support.object_id == object_id:
                support.planned_work_id = new_planned_work.id
                # Обновляем описание работы с информацией об опоре
                if not description:
                    description = f'Установка опоры {support.support_number}'
                    if support.support_type:
                        description += f' ({support.support_type})'
                    new_planned_work.description = description
        
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление запланированной работы",
            description=f"Пользователь {current_user.login} добавил запланированную работу '{work_title}' к объекту '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Запланированная работа успешно добавлена', 'success')
        return redirect(url_for('objects.planned_works_list', object_id=object_id))
    
    # Устанавливаем завтрашнюю дату по умолчанию (используем московское время)
    from datetime import timedelta
    from app.utils.timezone_utils import get_moscow_now
    
    moscow_now = get_moscow_now()
    tomorrow_date = (moscow_now + timedelta(days=1)).strftime('%Y-%m-%d')
    today_date = moscow_now.strftime('%Y-%m-%d')  # Для min атрибута
    print(f"DEBUG: GET запрос - передаем tomorrow_date = {tomorrow_date}, today_date = {today_date}")
    return render_template('objects/add_planned_work.html', object=obj, supports=supports, today_date=today_date, default_date=tomorrow_date)

@objects_bp.route('/<uuid:object_id>/planned-works/<uuid:work_id>/delete', methods=['POST'])
@login_required
def delete_planned_work(object_id, work_id):
    """Удаление запланированной работы (только для инженера ПТО)"""
    print(f"DEBUG: DELETE запрос получен для работы {work_id} объекта {object_id}")
    print(f"DEBUG: Пользователь: {current_user.login}, роль: {current_user.role}")
    
    obj = Object.query.get_or_404(object_id)
    planned_work = PlannedWork.query.get_or_404(work_id)
    
    print(f"DEBUG: Найдена работа: {planned_work.work_title}")
    
    # Проверяем, что работа принадлежит указанному объекту
    print(f"DEBUG: Проверяем принадлежность работы объекту: {planned_work.object_id} (тип: {type(planned_work.object_id)}) == {str(object_id)} (тип: {type(str(object_id))})")
    if str(planned_work.object_id) != str(object_id):
        print("DEBUG: Работа не принадлежит указанному объекту, возвращаем 404")
        abort(404)
    
    # Проверяем права доступа - только инженер ПТО может удалять работы
    print(f"DEBUG: Проверяем права доступа: is_pto_engineer = {is_pto_engineer(current_user)}")
    if not is_pto_engineer(current_user):
        print("DEBUG: У пользователя нет прав для удаления, перенаправляем")
        flash('У вас нет прав для удаления запланированных работ. Только инженер ПТО может выполнять эту операцию.', 'error')
        return redirect(url_for('objects.planned_works_list', object_id=object_id))
    
    print("DEBUG: Все проверки пройдены, начинаем удаление")
    
    try:
        print("DEBUG: Начинаем удаление файлов")
        # Удаляем связанные файлы, если они есть
        if hasattr(planned_work, 'location_files') and planned_work.location_files:
            import json
            try:
                files = json.loads(planned_work.location_files)
                for file_info in files:
                    file_path = os.path.join('app/static', file_info['file_path'])
                    if os.path.exists(file_path):
                        os.remove(file_path)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Удаляем папку с файлами, если она пустая
        upload_dir = os.path.join(UPLOAD_FOLDER, str(work_id))
        if os.path.exists(upload_dir) and not os.listdir(upload_dir):
            os.rmdir(upload_dir)
        
        print("DEBUG: Удаляем связанные записи")
        # Удаляем связанные записи о выполнении работы
        from app.models.objects import WorkExecution, WorkComparison
        
        # Сначала удаляем WorkComparison (они ссылаются на WorkExecution)
        print("DEBUG: Удаляем WorkComparison записи")
        WorkComparison.query.filter_by(planned_work_id=work_id).delete()
        
        # Потом удаляем WorkExecution
        print("DEBUG: Удаляем WorkExecution записи")
        WorkExecution.query.filter_by(planned_work_id=work_id).delete()
        
        print("DEBUG: Удаляем саму работу")
        # Удаляем запланированную работу
        db.session.delete(planned_work)
        db.session.commit()
        
        print("DEBUG: Логируем действие")
        # Логируем действие
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Удаление работы",
            description=f"Инженер ПТО {current_user.login} удалил работу '{planned_work.work_title}' (статус: {planned_work.status}) для объекта '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        print("DEBUG: Показываем сообщение об успехе")
        flash(f'Работа "{planned_work.work_title}" успешно удалена', 'success')
        
    except Exception as e:
        print(f"DEBUG: Ошибка при удалении: {str(e)}")
        db.session.rollback()
        flash(f'Ошибка при удалении работы: {str(e)}', 'error')
    
    return redirect(url_for('objects.planned_works_list', object_id=object_id))

@objects_bp.route('/<uuid:object_id>/planned-works/<uuid:work_id>/execute', methods=['GET', 'POST'])
@login_required
def execute_planned_work(object_id, work_id):
    """Выполнение запланированной работы"""
    obj = Object.query.get_or_404(object_id)
    planned_work = PlannedWork.query.get_or_404(work_id)
    
    if request.method == 'POST':
        execution_date = request.form.get('execution_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        actual_hours = request.form.get('actual_hours')
        completion_notes = request.form.get('completion_notes', '').strip()
        quality_rating = request.form.get('quality_rating')
        issues_encountered = request.form.get('issues_encountered', '').strip()
        
        # Преобразуем пустые строки в None
        if not completion_notes:
            completion_notes = None
        if not issues_encountered:
            issues_encountered = None
        
        if not execution_date:
            flash('Дата выполнения обязательна для заполнения', 'error')
            return render_template('objects/execute_planned_work.html', object=obj, planned_work=planned_work, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # Преобразуем дату
        try:
            execution_date = datetime.strptime(execution_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты', 'error')
            return render_template('objects/execute_planned_work.html', object=obj, planned_work=planned_work, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # Преобразуем время
        if start_time and start_time.strip():
            try:
                start_time = datetime.strptime(start_time, '%H:%M').time()
            except ValueError:
                start_time = None
        else:
            start_time = None
        
        if end_time and end_time.strip():
            try:
                end_time = datetime.strptime(end_time, '%H:%M').time()
            except ValueError:
                end_time = None
        else:
            end_time = None
        
        # Преобразуем часы
        if actual_hours and actual_hours.strip():
            try:
                actual_hours = float(actual_hours)
            except ValueError:
                actual_hours = None
        else:
            actual_hours = None
        
        # Преобразуем рейтинг
        if quality_rating and quality_rating.strip():
            try:
                quality_rating = int(quality_rating)
            except ValueError:
                quality_rating = None
        else:
            quality_rating = None
        
        # Создаем выполнение работы
        work_execution = WorkExecution(
            id=str(uuid.uuid4()),
            planned_work_id=work_id,
            execution_date=execution_date,
            start_time=start_time,
            end_time=end_time,
            actual_hours=actual_hours,
            status='completed',
            completion_notes=completion_notes,
            quality_rating=quality_rating,
            issues_encountered=issues_encountered,
            executed_by=current_user.userid
        )
        
        db.session.add(work_execution)
        
        # Сначала фиксируем work_execution в базе
        db.session.flush()
        
        # Обновляем статус запланированной работы
        planned_work.status = 'completed'
        planned_work.updated_at = datetime.utcnow()
        
        # Создаем сравнение плана и факта
        comparison = create_work_comparison(planned_work, work_execution)
        db.session.add(comparison)
        
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Выполнение запланированной работы",
            description=f"Пользователь {current_user.login} выполнил работу '{planned_work.work_title}' на объекте '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Работа успешно выполнена и зафиксирована', 'success')
        return redirect(url_for('objects.planned_works_list', object_id=object_id))
    
    return render_template('objects/execute_planned_work.html', object=obj, planned_work=planned_work, today_date=datetime.now().strftime('%Y-%m-%d'))

@objects_bp.route('/<uuid:object_id>/planned-works/<uuid:work_id>/change-date', methods=['POST'])
@login_required
def change_planned_work_date(object_id, work_id):
    """Изменение даты запланированной работы"""
    try:
        # Получаем работу
        work = PlannedWork.query.get_or_404(work_id)
        
        # Проверяем, что работа принадлежит указанному объекту
        if str(work.object_id) != str(object_id):
            abort(404)
        
        # Получаем новую дату из формы
        new_date_str = request.form.get('new_date')
        
        if not new_date_str:
            return jsonify({'success': False, 'error': 'Дата не указана'})
        
        # Парсим дату
        try:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Неверный формат даты'})
        
        # Проверяем, что дата не в прошлом (если работа ещё не завершена)
        if work.status != 'completed' and new_date < datetime.utcnow().date():
            return jsonify({'success': False, 'error': 'Нельзя перенести работу на прошедшую дату'})
        
        # Сохраняем старую дату для логирования
        old_date = work.planned_date
        
        # Обновляем дату
        work.planned_date = new_date
        work.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Логируем изменение
        try:
            old_date_str = old_date.strftime('%d.%m.%Y') if old_date else 'не установлена'
            ActivityLog.log_action(
                user_id=current_user.userid,
                user_login=current_user.login,
                action="Изменение даты запланированной работы",
                description=f"Пользователь {current_user.login} перенёс работу '{work.work_title}' с {old_date_str} на {new_date.strftime('%d.%m.%Y')}",
                ip_address=request.remote_addr,
                page_url=request.url,
                method=request.method
            )
        except Exception as log_error:
            print(f"Ошибка при логировании: {log_error}")
        
        return jsonify({
            'success': True, 
            'message': f'Дата работы изменена на {new_date.strftime("%d.%m.%Y")}',
            'new_date': new_date.strftime('%d.%m.%Y')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: Ошибка при изменении даты работы: {e}")
        return jsonify({'success': False, 'error': f'Ошибка при изменении даты: {str(e)}'})

@objects_bp.route('/<uuid:object_id>/planned-works/<uuid:work_id>/comparison')
@login_required
def work_comparison(object_id, work_id):
    """Просмотр сравнения плана и факта выполнения работы"""
    obj = Object.query.get_or_404(object_id)
    planned_work = PlannedWork.query.get_or_404(work_id)
    
    # Получаем последнее выполнение работы
    work_execution = WorkExecution.query.filter_by(planned_work_id=work_id).order_by(WorkExecution.created_at.desc()).first()
    
    if not work_execution:
        flash('Работа еще не выполнялась', 'info')
        return redirect(url_for('objects.planned_works_list', object_id=object_id))
    
    # Получаем сравнение
    comparison = WorkComparison.query.filter_by(
        planned_work_id=work_id,
        work_execution_id=work_execution.id
    ).first()
    
    if not comparison:
        # Создаем сравнение если его нет
        comparison = create_work_comparison(planned_work, work_execution)
        db.session.add(comparison)
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
        action="Просмотр сравнения плана и факта",
        description=f"Пользователь {current_user.login} просмотрел сравнение плана и факта для работы '{planned_work.work_title}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
    return render_template('objects/work_comparison.html', 
                         object=obj, 
                         planned_work=planned_work, 
                         work_execution=work_execution, 
                         comparison=comparison)

def create_work_comparison(planned_work, work_execution):
    """Создает сравнение плана и факта выполнения работы"""
    from datetime import date
    
    # Вычисляем отклонения
    if planned_work.planned_date:
        date_deviation = (work_execution.execution_date - planned_work.planned_date).days
    else:
        date_deviation = 0  # Если планируемая дата не установлена, отклонение = 0
    
    hours_deviation = 0
    # Убрано сравнение планируемых часов, так как поле estimated_hours больше не используется
    
    # Определяем процент выполнения
    completion_rate = 100.0  # Если работа выполнена, то 100%
    
    # Определяем оценку качества
    quality_score = work_execution.quality_rating or 0
    
    comparison = WorkComparison(
        id=str(uuid.uuid4()),
        planned_work_id=planned_work.id,
        work_execution_id=work_execution.id,
        planned_work_type=planned_work.work_type,
        planned_work_title=planned_work.work_title,
        planned_date=planned_work.planned_date,
        planned_hours=None,  # Поле больше не используется
        actual_work_type=planned_work.work_type,  # Предполагаем, что тип не изменился
        actual_work_title=planned_work.work_title,  # Предполагаем, что заголовок не изменился
        actual_date=work_execution.execution_date,
        actual_hours=work_execution.actual_hours,
        date_deviation_days=date_deviation,
        hours_deviation=hours_deviation,
        completion_rate=completion_rate,
        quality_score=quality_score,
        comparison_status='completed'
    )
    
    return comparison

@objects_bp.route('/<uuid:object_id>/checklist/<uuid:item_id>/add-quantity', methods=['POST'])
@login_required
def add_checklist_item_quantity(object_id, item_id):
    """Добавляет количество к позиции чек-листа"""
    obj = Object.query.get_or_404(object_id)
    item = ChecklistItem.query.get_or_404(item_id)
    
    if item.checklist.object_id != object_id:
        abort(404)
    
    try:
        data = request.get_json()
        add_quantity = float(data.get('add_quantity', 0))
        
        if add_quantity <= 0:
            return jsonify({
                'success': False,
                'message': 'Количество должно быть положительным числом'
            }), 400
        
        # Проверяем, не превышает ли новое количество планируемое
        new_current_quantity = (item.current_quantity or 0) + add_quantity
        if new_current_quantity > item.quantity:
            return jsonify({
                'success': False,
                'message': f'Нельзя добавить больше {item.quantity - (item.current_quantity or 0)} {item.unit}'
            }), 400
        
        # Обновляем текущее количество
        item.current_quantity = new_current_quantity
        item.updated_at = datetime.utcnow()
        
        # Проверяем и обновляем статус выполнения
        item.check_completion_status()
        
        # Обновляем счетчики в чек-листе
        obj.checklist.update_completion_status()
        
        db.session.commit()
        
        # Логируем действие
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление количества к позиции чек-листа",
            description=f"Пользователь {current_user.login} добавил {add_quantity} {item.unit} к позиции '{item.item_text}' в чек-листе объекта '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        return jsonify({
            'success': True,
            'new_current_quantity': new_current_quantity,
            'planned_quantity': item.quantity,
            'message': f'Количество успешно добавлено: {add_quantity} {item.unit}'
        })
        
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Некорректное значение количества'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при добавлении количества: {str(e)}'
        }), 500

# ==================== АВТОМАТИЗАЦИЯ ====================

@objects_bp.route('/admin/update-overdue-works', methods=['POST'])
@login_required
def manual_update_overdue_works():
    """Ручное обновление статуса просроченных работ"""
    try:
        updated_count = PlannedWork.update_overdue_works()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            action='manual_update_overdue_works',
            details=f'Обновлено просроченных работ: {updated_count}',
            method=request.method
        )
        
        flash(f'Обновлено просроченных работ: {updated_count}', 'success')
        
    except Exception as e:
        flash(f'Ошибка при обновлении просроченных работ: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('objects.planned_works_overview'))

@objects_bp.route('/admin/generate-daily-reports', methods=['POST'])
@login_required
def manual_generate_daily_reports():
    """Ручная генерация ежедневных отчетов за сегодня"""
    try:
        from app.utils.scheduler import scheduler
        generated_count = scheduler.generate_report_for_today()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            action='manual_generate_daily_reports',
            details=f'Сгенерировано отчетов: {generated_count}',
            method=request.method
        )
        
        flash(f'Сгенерировано отчетов за сегодня: {generated_count}', 'success')
        
    except Exception as e:
        flash(f'Ошибка при генерации отчетов: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('objects.planned_works_overview'))

@objects_bp.route('/admin/generate-missing-reports', methods=['POST'])
@login_required
def manual_generate_missing_reports():
    """Ручная генерация всех пропущенных отчетов"""
    try:
        from app.utils.scheduler import scheduler
        generated_count = scheduler.generate_missing_reports()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            action='manual_generate_missing_reports',
            details=f'Восстановлено пропущенных отчетов: {generated_count}',
            method=request.method
        )
        
        flash(f'Восстановлено пропущенных отчетов: {generated_count}', 'success')
        
    except Exception as e:
        flash(f'Ошибка при восстановлении отчетов: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('objects.planned_works_overview'))

# ==================== ЕЖЕДНЕВНЫЕ ОТЧЕТЫ ====================

def generate_daily_report_for_date(object_id, report_date):
    """Генерирует ежедневный отчёт для указанной даты"""
    try:
        # Проверяем, существует ли уже отчёт за эту дату
        existing_report = DailyReport.query.filter_by(
            object_id=object_id, 
            report_date=report_date
        ).first()
        
        if existing_report:
            return existing_report
        
        # Получаем объект
        obj = Object.query.get(object_id)
        if not obj:
            return None
        
        # Подсчитываем статистику
        # Запланированные работы - все работы со статусом 'planned'
        planned_works = PlannedWork.query.filter_by(object_id=object_id).filter(
            PlannedWork.status == 'planned'
        ).all()
        
        completed_works = PlannedWork.query.filter_by(object_id=object_id).filter(
            PlannedWork.status == 'completed'
        ).join(WorkExecution).filter(
            WorkExecution.execution_date == report_date
        ).all()
        
        overdue_works = PlannedWork.query.filter_by(object_id=object_id).filter(
            PlannedWork.planned_date < report_date,
            PlannedWork.status.in_(['planned', 'in_progress'])
        ).all()
        
        # Создаем новый отчёт
        daily_report = DailyReport(
            object_id=object_id,
            report_date=report_date,
            planned_works_count=len(planned_works),
            completed_works_count=len(completed_works),
            overdue_works_count=len(overdue_works),
            created_by=current_user.userid if current_user.is_authenticated else None
        )
        
        db.session.add(daily_report)
        db.session.commit()
        
        return daily_report
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при генерации отчёта: {e}")
        return None

def get_daily_report_data(object_id, report_date):
    """Получает данные для отображения ежедневного отчёта"""
    try:
        # Получаем или создаем отчёт
        report = generate_daily_report_for_date(object_id, report_date)
        if not report:
            return None
        
        # Получаем запланированные работы - все работы со статусом 'planned'
        planned_works = PlannedWork.query.filter_by(object_id=object_id).filter(
            PlannedWork.status == 'planned'
        ).all()
        
        # Получаем выполненные работы за эту дату
        completed_works = db.session.query(PlannedWork, WorkExecution).join(
            WorkExecution, PlannedWork.id == WorkExecution.planned_work_id
        ).filter(
            PlannedWork.object_id == object_id,
            WorkExecution.execution_date == report_date
        ).all()
        
        # Получаем просроченные работы
        overdue_works = PlannedWork.query.filter_by(object_id=object_id).filter(
            PlannedWork.planned_date < report_date,
            PlannedWork.status.in_(['planned', 'in_progress'])
        ).all()
        
        return {
            'report': report,
            'planned_works': planned_works,
            'completed_works': completed_works,
            'overdue_works': overdue_works
        }
        
    except Exception as e:
        print(f"Ошибка при получении данных отчёта: {e}")
        return None

@objects_bp.route('/<uuid:object_id>/daily-report/<date>')
@login_required
def daily_report_view(object_id, date):
    """Просмотр ежедневного отчёта"""
    try:
        # Парсим дату
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Получаем данные отчёта
        report_data = get_daily_report_data(object_id, report_date)
        if not report_data:
            flash('Ошибка при загрузке отчёта', 'error')
            return redirect(url_for('objects.object_detail', object_id=object_id))
        
        obj = Object.query.get_or_404(object_id)
        
        return render_template('objects/daily_report.html', 
                             object=obj, 
                             report_data=report_data,
                             report_date=report_date)
        
    except ValueError:
        flash('Некорректная дата', 'error')
        return redirect(url_for('objects.object_detail', object_id=object_id))
    except Exception as e:
        flash(f'Ошибка при загрузке отчёта: {str(e)}', 'error')
        return redirect(url_for('objects.object_detail', object_id=object_id))

@objects_bp.route('/<uuid:object_id>/daily-report/<date>/approve', methods=['POST'])
@login_required
def approve_daily_report(object_id, date):
    """Утверждение ежедневного отчёта"""
    try:
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
        report = DailyReport.query.filter_by(
            object_id=object_id, 
            report_date=report_date
        ).first()
        
        if not report:
            flash('Отчёт не найден', 'error')
            return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))
        
        # Проверяем права пользователя
        user_role = current_user.role.upper() if current_user.role else ''
        
        if 'ПТО' in user_role:
            report.approved_by_pto = True
        elif 'ЗАМ' in user_role or 'ДИРЕКТОР' in user_role:
            report.approved_by_deputy = True
        elif 'ГЕН' in user_role or 'ГЕНЕРАЛЬНЫЙ' in user_role:
            report.approved_by_director = True
        else:
            flash('У вас нет прав для утверждения отчётов', 'error')
            return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))
        
        # Новая логика: достаточно одного утверждения
        report.approval_status = 'approved'
        report.approved_by = current_user.userid
        report.approved_at = datetime.utcnow()
        # Сбрасываем признаки отклонения, если были
        report.rejection_reason = None
        report.rejected_by = None
        report.rejected_at = None
        
        db.session.commit()
        
        flash('Отчёт успешно утверждён', 'success')
        return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))
        
    except ValueError:
        flash('Некорректная дата', 'error')
        return redirect(url_for('objects.object_detail', object_id=object_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при утверждении отчёта: {str(e)}', 'error')
        return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))

@objects_bp.route('/<uuid:object_id>/daily-report/<date>/reject', methods=['POST'])
@login_required
def reject_daily_report(object_id, date):
    """Отклонение ежедневного отчёта"""
    try:
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
        report = DailyReport.query.filter_by(
            object_id=object_id, 
            report_date=report_date
        ).first()
        
        if not report:
            flash('Отчёт не найден', 'error')
            return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))
        
        # Получаем причину отклонения
        rejection_reason = request.form.get('rejection_reason', '').strip()
        if not rejection_reason:
            flash('Укажите причину отклонения', 'error')
            return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))
        
        # Проверяем права пользователя
        user_role = current_user.role.upper() if current_user.role else ''
        
        if 'ПТО' not in user_role and 'ЗАМ' not in user_role and 'ДИРЕКТОР' not in user_role and 'ГЕН' not in user_role:
            flash('У вас нет прав для отклонения отчётов', 'error')
            return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))
        
        # Отклоняем отчёт (новая логика: достаточно одного отклонения)
        report.approval_status = 'rejected'
        report.rejection_reason = rejection_reason
        report.rejected_by = current_user.userid
        report.rejected_at = datetime.utcnow()
        
        # Сбрасываем все утверждения
        report.approved_by_pto = False
        report.approved_by_deputy = False
        report.approved_by_director = False
        report.approved_by = None
        report.approved_at = None
        
        db.session.commit()
        
        flash('Отчёт отклонён', 'success')
        return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))
        
    except ValueError:
        flash('Некорректная дата', 'error')
        return redirect(url_for('objects.object_detail', object_id=object_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при отклонении отчёта: {str(e)}', 'error')
        return redirect(url_for('objects.daily_report_view', object_id=object_id, date=date))

@objects_bp.route('/<uuid:object_id>/delete', methods=['POST'])
@login_required
def delete_object(object_id):
    """Удаление объекта (только для инженера ПТО)"""
    try:
        # Получаем объект
        obj = Object.query.get_or_404(object_id)
        
        # Проверяем права пользователя - только инженер ПТО может удалять объекты
        user_role = current_user.role if current_user.role else ''
        print(f"DEBUG: User role: '{user_role}'")  # Отладочная информация
        if user_role != 'Инженер ПТО':
            return jsonify({'success': False, 'error': f'У вас нет прав для удаления объектов. Ваша роль: {user_role}'})
        
        # Логируем действие перед удалением
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Удаление объекта",
            description=f"Пользователь {current_user.login} удалил объект '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        # Сначала удаляем все связанные DailyReport записи
        DailyReport.query.filter_by(object_id=object_id).delete()
        
        # Затем удаляем сам объект
        db.session.delete(obj)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Объект "{obj.name}" успешно удалён'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Ошибка при удалении объекта: {str(e)}'})

# Отладочная информация будет добавлена позже в приложении


