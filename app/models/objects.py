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
    checklists = db.relationship('Checklist', backref='object', lazy=True, cascade='all, delete-orphan')

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))

class Trench(db.Model):
    """Модель траншеи"""
    __tablename__ = 'trenches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = db.Column(db.String(36), db.ForeignKey('objects.id'), nullable=False)
    trench_number = db.Column(db.String(50), nullable=False)
    length = db.Column(db.Float)  # длина в метрах
    width = db.Column(db.Float)  # ширина в метрах
    depth = db.Column(db.Float)  # глубина в метрах
    soil_type = db.Column(db.String(100))  # тип грунта
    excavation_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='planned')  # planned, in_progress, completed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))

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
    object_id = db.Column(db.String(36), db.ForeignKey('objects.id'), nullable=False)
    checklist_number = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    checklist_type = db.Column(db.String(100))  # тип чек-листа
    completion_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed
    total_items = db.Column(db.Integer, default=0)
    completed_items = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    
    # Связь с элементами чек-листа
    items = db.relationship('ChecklistItem', backref='checklist', lazy=True, cascade='all, delete-orphan')

class ChecklistItem(db.Model):
    """Модель элемента чек-листа"""
    __tablename__ = 'checklist_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checklist_id = db.Column(db.String(36), db.ForeignKey('checklists.id'), nullable=False)
    item_text = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    completed_by = db.Column(db.String(36), db.ForeignKey('users.userid'))
    notes = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)