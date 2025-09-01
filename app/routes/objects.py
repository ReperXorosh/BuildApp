from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.objects import Object, Support, Trench, Report, Checklist, ChecklistItem, PlannedWork, WorkExecution, WorkComparison
from app.models.activity_log import ActivityLog
from datetime import datetime
import uuid

objects_bp = Blueprint('objects', __name__)

@objects_bp.context_processor
def inject_gettext():
    """Внедряет функцию gettext в контекст шаблонов"""
    def gettext(text):
        return text
    return dict(gettext=gettext)

@objects_bp.route('/objects')
@login_required
def object_list():
    """Список всех объектов"""
    objects = Object.query.order_by(Object.created_at.desc()).all()
    
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
    
    return render_template('objects/object_list.html', objects=objects)

@objects_bp.route('/objects/add', methods=['GET', 'POST'])
@login_required
def add_object():
    """Добавление нового объекта"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        
        if not name:
            flash('Название объекта обязательно для заполнения', 'error')
            return render_template('objects/add_object.html')
        
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
    
    return render_template('objects/add_object.html')

@objects_bp.route('/objects/<object_id>')
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
    
    return render_template('objects/object_detail.html', object=obj)

# Маршруты для опор
@objects_bp.route('/objects/<object_id>/supports')
@login_required
def supports_list(object_id):
    """Список опор объекта"""
    obj = Object.query.get_or_404(object_id)
    supports = Support.query.filter_by(object_id=object_id).order_by(Support.created_at.desc()).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр опор",
        description=f"Пользователь {current_user.login} просмотрел опоры объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('objects/supports_list.html', object=obj, supports=supports)

@objects_bp.route('/objects/<object_id>/supports/add', methods=['GET', 'POST'])
@login_required
def add_support(object_id):
    """Добавление опоры"""
    obj = Object.query.get_or_404(object_id)
    
    if request.method == 'POST':
        support_number = request.form.get('support_number', '').strip()
        support_type = request.form.get('support_type', '').strip()
        height = request.form.get('height')
        material = request.form.get('material', '').strip()
        installation_date = request.form.get('installation_date')
        notes = request.form.get('notes', '').strip()
        
        if not support_number:
            flash('Номер опоры обязателен для заполнения', 'error')
            return render_template('objects/add_support.html', object=obj)
        
        # Преобразуем дату
        if installation_date:
            try:
                installation_date = datetime.strptime(installation_date, '%Y-%m-%d').date()
            except ValueError:
                installation_date = None
        
        # Преобразуем высоту
        if height:
            try:
                height = float(height)
            except ValueError:
                height = None
        
        new_support = Support(
            id=str(uuid.uuid4()),
            object_id=object_id,
            support_number=support_number,
            support_type=support_type,
            height=height,
            material=material,
            installation_date=installation_date,
            notes=notes,
            created_by=current_user.userid
        )
        
        db.session.add(new_support)
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление опоры",
            description=f"Пользователь {current_user.login} добавил опору {support_number} к объекту '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Опора успешно добавлена', 'success')
        return redirect(url_for('objects.supports_list', object_id=object_id))
    
    return render_template('objects/add_support.html', object=obj)

# Маршруты для траншей
@objects_bp.route('/objects/<object_id>/trenches')
@login_required
def trenches_list(object_id):
    """Список траншей объекта"""
    obj = Object.query.get_or_404(object_id)
    trenches = Trench.query.filter_by(object_id=object_id).order_by(Trench.created_at.desc()).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр траншей",
        description=f"Пользователь {current_user.login} просмотрел траншеи объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('objects/trenches_list.html', object=obj, trenches=trenches)

@objects_bp.route('/objects/<object_id>/trenches/add', methods=['GET', 'POST'])
@login_required
def add_trench(object_id):
    """Добавление траншеи"""
    obj = Object.query.get_or_404(object_id)
    
    if request.method == 'POST':
        trench_number = request.form.get('trench_number', '').strip()
        length = request.form.get('length')
        width = request.form.get('width')
        depth = request.form.get('depth')
        soil_type = request.form.get('soil_type', '').strip()
        excavation_date = request.form.get('excavation_date')
        notes = request.form.get('notes', '').strip()
        
        if not trench_number:
            flash('Номер траншеи обязателен для заполнения', 'error')
            return render_template('objects/add_trench.html', object=obj)
        
        # Преобразуем дату
        if excavation_date:
            try:
                excavation_date = datetime.strptime(excavation_date, '%Y-%m-%d').date()
            except ValueError:
                excavation_date = None
        
        # Преобразуем числовые значения
        try:
            length = float(length) if length else None
            width = float(width) if width else None
            depth = float(depth) if depth else None
        except ValueError:
            flash('Некорректные числовые значения', 'error')
            return render_template('objects/add_trench.html', object=obj)
        
        new_trench = Trench(
            id=str(uuid.uuid4()),
            object_id=object_id,
            trench_number=trench_number,
            length=length,
            width=width,
            depth=depth,
            soil_type=soil_type,
            excavation_date=excavation_date,
            notes=notes,
            created_by=current_user.userid
        )
        
        db.session.add(new_trench)
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление траншеи",
            description=f"Пользователь {current_user.login} добавил траншею {trench_number} к объекту '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Траншея успешно добавлена', 'success')
        return redirect(url_for('objects.trenches_list', object_id=object_id))
    
    return render_template('objects/add_trench.html', object=obj)

# Маршруты для отчётов
@objects_bp.route('/objects/<object_id>/reports')
@login_required
def reports_list(object_id):
    """Список отчётов объекта"""
    obj = Object.query.get_or_404(object_id)
    reports = Report.query.filter_by(object_id=object_id).order_by(Report.created_at.desc()).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр отчётов",
        description=f"Пользователь {current_user.login} просмотрел отчёты объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('objects/reports_list.html', object=obj, reports=reports)

@objects_bp.route('/objects/<object_id>/reports/add', methods=['GET', 'POST'])
@login_required
def add_report(object_id):
    """Добавление отчёта"""
    obj = Object.query.get_or_404(object_id)
    
    if request.method == 'POST':
        report_number = request.form.get('report_number', '').strip()
        report_type = request.form.get('report_type', '').strip()
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        report_date = request.form.get('report_date')
        notes = request.form.get('notes', '').strip()
        
        if not report_number or not title:
            flash('Номер отчёта и заголовок обязательны для заполнения', 'error')
            return render_template('objects/add_report.html', object=obj, today_date=datetime.now().strftime('%Y-%m-%d'))
        
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
    
    return render_template('objects/add_report.html', object=obj, today_date=datetime.now().strftime('%Y-%m-%d'))

# Маршруты для чек-листов
@objects_bp.route('/objects/<object_id>/checklists')
@login_required
def checklists_list(object_id):
    """Список чек-листов объекта"""
    obj = Object.query.get_or_404(object_id)
    checklists = Checklist.query.filter_by(object_id=object_id).order_by(Checklist.created_at.desc()).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр чек-листов",
        description=f"Пользователь {current_user.login} просмотрел чек-листы объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('objects/checklists_list.html', object=obj, checklists=checklists)

@objects_bp.route('/objects/<object_id>/checklists/add', methods=['GET', 'POST'])
@login_required
def add_checklist(object_id):
    """Добавление чек-листа"""
    obj = Object.query.get_or_404(object_id)
    
    if request.method == 'POST':
        checklist_number = request.form.get('checklist_number', '').strip()
        title = request.form.get('title', '').strip()
        checklist_type = request.form.get('checklist_type', '').strip()
        completion_date = request.form.get('completion_date')
        notes = request.form.get('notes', '').strip()
        
        if not checklist_number or not title:
            flash('Номер чек-листа и заголовок обязательны для заполнения', 'error')
            return render_template('objects/add_checklist.html', object=obj)
        
        # Преобразуем дату
        if completion_date:
            try:
                completion_date = datetime.strptime(completion_date, '%Y-%m-%d').date()
            except ValueError:
                completion_date = None
        
        new_checklist = Checklist(
            id=str(uuid.uuid4()),
            object_id=object_id,
            checklist_number=checklist_number,
            title=title,
            checklist_type=checklist_type,
            completion_date=completion_date,
            notes=notes,
            created_by=current_user.userid
        )
        
        db.session.add(new_checklist)
        db.session.commit()
        
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Добавление чек-листа",
            description=f"Пользователь {current_user.login} добавил чек-лист {checklist_number} к объекту '{obj.name}'",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        flash('Чек-лист успешно добавлен', 'success')
        return redirect(url_for('objects.checklists_list', object_id=object_id))
    
    return render_template('objects/add_checklist.html', object=obj)


# Маршруты для запланированных работ
@objects_bp.route('/objects/<object_id>/planned-works')
@login_required
def planned_works_list(object_id):
    """Список запланированных работ объекта"""
    obj = Object.query.get_or_404(object_id)
    planned_works = PlannedWork.query.filter_by(object_id=object_id).order_by(PlannedWork.planned_date.asc()).all()
    
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр запланированных работ",
        description=f"Пользователь {current_user.login} просмотрел запланированные работы объекта '{obj.name}'",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    return render_template('objects/planned_works_list.html', object=obj, planned_works=planned_works)

@objects_bp.route('/objects/<object_id>/planned-works/add', methods=['GET', 'POST'])
@login_required
def add_planned_work(object_id):
    """Добавление запланированной работы"""
    obj = Object.query.get_or_404(object_id)
    
    if request.method == 'POST':
        work_type = request.form.get('work_type', '').strip()
        work_title = request.form.get('work_title', '').strip()
        description = request.form.get('description', '').strip()
        planned_date = request.form.get('planned_date')
        priority = request.form.get('priority', 'medium')
        estimated_hours = request.form.get('estimated_hours')
        materials_required = request.form.get('materials_required', '').strip()
        location_details = request.form.get('location_details', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not work_type or not work_title or not planned_date:
            flash('Тип работы, заголовок и планируемая дата обязательны для заполнения', 'error')
            return render_template('objects/add_planned_work.html', object=obj, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # Преобразуем дату
        try:
            planned_date = datetime.strptime(planned_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат даты', 'error')
            return render_template('objects/add_planned_work.html', object=obj, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # Преобразуем часы
        if estimated_hours:
            try:
                estimated_hours = float(estimated_hours)
            except ValueError:
                estimated_hours = None
        
        new_planned_work = PlannedWork(
            id=str(uuid.uuid4()),
            object_id=object_id,
            work_type=work_type,
            work_title=work_title,
            description=description,
            planned_date=planned_date,
            priority=priority,
            estimated_hours=estimated_hours,
            materials_required=materials_required,
            location_details=location_details,
            notes=notes,
            created_by=current_user.userid
        )
        
        db.session.add(new_planned_work)
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
    
    return render_template('objects/add_planned_work.html', object=obj, today_date=datetime.now().strftime('%Y-%m-%d'))

@objects_bp.route('/objects/<object_id>/planned-works/<work_id>/execute', methods=['GET', 'POST'])
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
        if start_time:
            try:
                start_time = datetime.strptime(start_time, '%H:%M').time()
            except ValueError:
                start_time = None
        
        if end_time:
            try:
                end_time = datetime.strptime(end_time, '%H:%M').time()
            except ValueError:
                end_time = None
        
        # Преобразуем часы
        if actual_hours:
            try:
                actual_hours = float(actual_hours)
            except ValueError:
                actual_hours = None
        
        # Преобразуем рейтинг
        if quality_rating:
            try:
                quality_rating = int(quality_rating)
            except ValueError:
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

@objects_bp.route('/objects/<object_id>/planned-works/<work_id>/comparison')
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
    date_deviation = (work_execution.execution_date - planned_work.planned_date).days
    
    hours_deviation = 0
    if planned_work.estimated_hours and work_execution.actual_hours:
        hours_deviation = work_execution.actual_hours - planned_work.estimated_hours
    
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
        planned_hours=planned_work.estimated_hours,
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

