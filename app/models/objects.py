from app.extensions import db
from datetime import datetime
import uuid

class Object(db.Model):
    """Модель объекта"""
    __tablename__ = 'objects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    status = db.Column(db.String(50), default='active')  # active, inactive, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    
    # Связи с подпунктами
    supports = db.relationship('Support', backref='object', lazy=True, cascade='all, delete-orphan')
    trenches = db.relationship('Trench', backref='object', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='object', lazy=True, cascade='all, delete-orphan')
    checklist = db.relationship('Checklist', backref='object', lazy=True, uselist=False, cascade='all, delete-orphan')
    planned_works = db.relationship('PlannedWork', backref='object', lazy=True, cascade='all, delete-orphan')

    # Добавить связь с пользователем
    creator = db.relationship('Users', foreign_keys=[created_by], backref='created_objects')

class Support(db.Model):
    """Модель опоры"""
    __tablename__ = 'supports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = db.Column(db.String(36), db.ForeignKey('objects.id'), nullable=False)
    support_number = db.Column(db.String(50), nullable=False)
    support_type = db.Column(db.String(100))  # тип опоры
    height = db.Column(db.Float)  # высота
    material = db.Column(db.String(100))  # материал
    installation_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='planned')  # planned, in_progress, completed
    notes = db.Column(db.Text)
    planned_work_id = db.Column(db.String(36), db.ForeignKey('planned_works.id'))  # связь с запланированной работой
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    
    # Связь с запланированной работой
    planned_work = db.relationship('PlannedWork', backref='supports', lazy=True)

class Trench(db.Model):
    """Модель траншеи"""
    __tablename__ = 'trenches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = db.Column(db.String(36), db.ForeignKey('objects.id'), nullable=False)
    planned_length = db.Column(db.Float, nullable=False, default=0.0)  # запланированная длина в метрах
    current_length = db.Column(db.Float, default=0.0)  # текущая длина в метрах
    width = db.Column(db.Float)  # ширина в метрах (опционально)
    depth = db.Column(db.Float)  # глубина в метрах
    soil_type = db.Column(db.String(100))  # тип грунта (опционально)
    excavation_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='planned')  # planned, in_progress, completed
    notes = db.Column(db.Text)
    planned_work_id = db.Column(db.String(36), db.ForeignKey('planned_works.id'))  # связь с запланированной работой
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    
    # Связь с запланированной работой
    planned_work = db.relationship('PlannedWork', backref='trenches', lazy=True)
    
    def check_completion_status(self):
        """Проверяет и обновляет статус завершения траншеи"""
        if self.current_length >= self.planned_length:
            self.status = 'completed'
        elif self.current_length > 0:
            self.status = 'in_progress'
        else:
            self.status = 'planned'

class Report(db.Model):
    """Модель отчёта"""
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = db.Column(db.String(36), db.ForeignKey('objects.id'), nullable=False)
    report_number = db.Column(db.String(50), nullable=False)
    report_type = db.Column(db.String(100))  # тип отчёта
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    report_date = db.Column(db.Date, default=datetime.utcnow().date)
    status = db.Column(db.String(50), default='draft')  # draft, submitted, approved
    file_path = db.Column(db.String(500))  # путь к файлу отчёта
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))

class Checklist(db.Model):
    """Модель чек-листа"""
    __tablename__ = 'checklists'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = db.Column(db.String(36), db.ForeignKey('objects.id'), nullable=False, unique=True)
    checklist_number = db.Column(db.String(50), nullable=False)  # Добавляем поле для номера чек-листа
    title = db.Column(db.String(255), default='Чек-лист объекта')
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed
    total_items = db.Column(db.Integer, default=0)
    completed_items = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    
    # Связь с элементами чек-листа
    items = db.relationship('ChecklistItem', backref='checklist', lazy=True, cascade='all, delete-orphan', order_by='ChecklistItem.order_index')
    
    # Связь с пользователем
    creator = db.relationship('Users', foreign_keys=[created_by], backref='created_checklists')
    
    def __init__(self, **kwargs):
        super(Checklist, self).__init__(**kwargs)
        if not self.title:
            self.title = 'Чек-лист объекта'
        if not self.checklist_number:
            # Генерируем автоматический номер чек-листа
            self.checklist_number = f"ЧЛ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    def add_item(self, item_text, order_index=None):
        """Добавляет новый элемент в чек-лист"""
        if order_index is None:
            order_index = len(self.items) + 1
        
        item = ChecklistItem(
            checklist_id=self.id,
            item_text=item_text,
            order_index=order_index
        )
        self.items.append(item)
        self.total_items = len(self.items)
        return item
    
    @property
    def actual_total_items(self):
        """Возвращает фактическое количество элементов в чек-листе"""
        return len(self.items)
    
    def update_completion_status(self):
        """Обновляет статус завершения чек-листа"""
        # Синхронизируем total_items с фактическим количеством
        self.total_items = self.actual_total_items
        
        completed = sum(1 for item in self.items if item.is_completed)
        self.completed_items = completed
        
        if self.total_items > 0:
            completion_rate = (completed / self.total_items) * 100
            if completion_rate == 100:
                self.status = 'completed'
            elif completion_rate > 0:
                self.status = 'in_progress'
            else:
                self.status = 'pending'

class ChecklistItem(db.Model):
    """Модель элемента чек-листа"""
    __tablename__ = 'checklist_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checklist_id = db.Column(db.String(36), db.ForeignKey('checklists.id'), nullable=False)
    item_text = db.Column(db.String(500), nullable=False)
    unit = db.Column(db.String(20), default='шт')  # единица измерения (м, шт, м3, кг и т.д.)
    quantity = db.Column(db.Float, default=1.0)  # планируемое количество
    current_quantity = db.Column(db.Float, default=0.0)  # текущее установленное количество
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    completed_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    notes = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем, который выполнил элемент
    completed_by_user = db.relationship('Users', foreign_keys=[completed_by], backref='completed_checklist_items')
    
    def complete(self, user_id=None, notes=None, force=False):
        """Отмечает элемент как выполненный"""
        # Проверяем, достигнуто ли планируемое количество (если не принудительное выполнение)
        if not force and (self.current_quantity or 0) < self.quantity:
            # Если количество не достигнуто и это не принудительное выполнение, элемент не может быть выполнен
            return False
        
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        if user_id:
            self.completed_by = user_id
        if notes:
            self.notes = notes
        
        # Обновляем статус чек-листа
        if self.checklist:
            self.checklist.update_completion_status()
        return True
    
    def uncomplete(self):
        """Отмечает элемент как невыполненный"""
        self.is_completed = False
        self.completed_at = None
        self.completed_by = None
        
        # Обновляем статус чек-листа
        if self.checklist:
            self.checklist.update_completion_status()
    
    def check_completion_status(self):
        """Проверяет и обновляет статус выполнения на основе количества"""
        if (self.current_quantity or 0) >= self.quantity:
            if not self.is_completed:
                self.is_completed = True
                self.completed_at = datetime.utcnow()
        else:
            if self.is_completed:
                self.is_completed = False
                self.completed_at = None
                self.completed_by = None

class PlannedWork(db.Model):
    """Модель запланированной работы"""
    __tablename__ = 'planned_works'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = db.Column(db.String(36), db.ForeignKey('objects.id'), nullable=False)
    work_type = db.Column(db.String(100), nullable=False)  # 'support_installation', 'trench_excavation', etc.
    work_title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    planned_date = db.Column(db.Date, nullable=True)  # может быть NULL для работ без конкретной даты
    priority = db.Column(db.String(50), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(50), default='planned')  # planned, in_progress, completed, cancelled
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.userid'))
    estimated_hours = db.Column(db.Float)
    materials_required = db.Column(db.Text)
    location_details = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    
    # Связи
    work_executions = db.relationship('WorkExecution', backref='planned_work', lazy=True, cascade='all, delete-orphan')
    
    # Связь с пользователем, которому назначена работа
    assignee = db.relationship('Users', foreign_keys=[assigned_to], backref='assigned_works')
    
    @staticmethod
    def update_overdue_works():
        """Обновляет статус просроченных работ"""
        from datetime import date
        
        today = date.today()
        
        # Находим все работы, которые должны были быть выполнены, но не выполнены
        overdue_works = PlannedWork.query.filter(
            PlannedWork.planned_date < today,
            PlannedWork.status.in_(['planned', 'in_progress'])
        ).all()
        
        updated_count = 0
        for work in overdue_works:
            work.status = 'overdue'
            work.updated_at = datetime.utcnow()
            updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
        
        return updated_count
    
    def is_overdue(self):
        """Проверяет, просрочена ли работа"""
        if not self.planned_date:
            return False
        return self.planned_date < datetime.utcnow().date() and self.status not in ['completed', 'cancelled', 'overdue']

class WorkExecution(db.Model):
    """Модель выполнения работы"""
    __tablename__ = 'work_executions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    planned_work_id = db.Column(db.String(36), db.ForeignKey('planned_works.id'), nullable=False)
    execution_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    actual_hours = db.Column(db.Float)
    status = db.Column(db.String(50), default='in_progress')  # in_progress, completed, cancelled
    completion_notes = db.Column(db.Text)
    photos_paths = db.Column(db.Text)  # JSON строка с путями к фотографиям
    executed_by = db.Column(db.String(36), db.ForeignKey('users.userid'), nullable=False)
    quality_rating = db.Column(db.Integer)  # 1-5 звезд
    issues_encountered = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем, который выполнил работу
    executor = db.relationship('Users', foreign_keys=[executed_by], backref='executed_works')
    
class WorkComparison(db.Model):
    """Модель для сравнения плана и факта выполнения работ"""
    __tablename__ = 'work_comparisons'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    planned_work_id = db.Column(db.String(36), db.ForeignKey('planned_works.id'), nullable=False)
    work_execution_id = db.Column(db.String(36), db.ForeignKey('work_executions.id'), nullable=False)
    comparison_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Планируемые параметры
    planned_work_type = db.Column(db.String(100))
    planned_work_title = db.Column(db.String(255))
    planned_date = db.Column(db.Date)
    planned_hours = db.Column(db.Float)
    
    # Фактические параметры
    actual_work_type = db.Column(db.String(100))
    actual_work_title = db.Column(db.String(255))
    actual_date = db.Column(db.Date)
    actual_hours = db.Column(db.Float)
    
    # Результат сравнения
    date_deviation_days = db.Column(db.Integer)  # отклонение по дате в днях
    hours_deviation = db.Column(db.Float)  # отклонение по часам
    completion_rate = db.Column(db.Float)  # процент выполнения (0-100)
    quality_score = db.Column(db.Integer)  # оценка качества (1-5)
    
    # Статус сравнения
    comparison_status = db.Column(db.String(50), default='pending')  # pending, completed, needs_review
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    planned_work = db.relationship('PlannedWork', foreign_keys=[planned_work_id], backref='work_comparisons')
    work_execution = db.relationship('WorkExecution', foreign_keys=[work_execution_id], backref='work_comparisons')