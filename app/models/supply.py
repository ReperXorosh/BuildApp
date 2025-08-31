import uuid
from datetime import datetime, timezone, timedelta
import pytz
from app.extensions import db

def get_moscow_time():
    moscow_tz = pytz.timezone('Europe/Moscow')
    return datetime.now(moscow_tz)

class Material(db.Model):
    """Модель для материалов"""
    __tablename__ = 'materials'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    unit = db.Column(db.String(50), nullable=False)  # шт, кг, м, л и т.д.
    current_quantity = db.Column(db.Float, default=0.0)
    min_quantity = db.Column(db.Float, default=0.0)  # минимальный запас
    supplier = db.Column(db.String(200), nullable=True)
    price_per_unit = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=get_moscow_time, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_time, onupdate=get_moscow_time)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'current_quantity': self.current_quantity,
            'min_quantity': self.min_quantity,
            'supplier': self.supplier,
            'price_per_unit': self.price_per_unit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Equipment(db.Model):
    """Модель для техники"""
    __tablename__ = 'equipment'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='available')  # available, in_use, maintenance, broken
    location = db.Column(db.String(200), nullable=True)
    supplier = db.Column(db.String(200), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    warranty_until = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=get_moscow_time, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_time, onupdate=get_moscow_time)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model': self.model,
            'serial_number': self.serial_number,
            'status': self.status,
            'location': self.location,
            'supplier': self.supplier,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'warranty_until': self.warranty_until.isoformat() if self.warranty_until else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SupplyOrder(db.Model):
    """Модель для заказов на снабжение"""
    __tablename__ = 'supply_orders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = db.Column(db.String(50), nullable=False, unique=True)
    order_type = db.Column(db.String(50), nullable=False)  # material, equipment
    status = db.Column(db.String(50), default='pending')  # pending, approved, delivered, cancelled
    requested_by = db.Column(db.String(36), db.ForeignKey('users.userid'), nullable=False)
    approved_by = db.Column(db.String(36), db.ForeignKey('users.userid'), nullable=True)
    supplier = db.Column(db.String(200), nullable=True)
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_moscow_time, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_time, onupdate=get_moscow_time)
    delivery_date = db.Column(db.Date, nullable=True)
    
    # Связи
    requested_user = db.relationship('Users', foreign_keys=[requested_by])
    approved_user = db.relationship('Users', foreign_keys=[approved_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'order_type': self.order_type,
            'status': self.status,
            'requested_by': self.requested_by,
            'approved_by': self.approved_by,
            'supplier': self.supplier,
            'total_amount': self.total_amount,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None
        }

class SupplyOrderItem(db.Model):
    """Модель для элементов заказа на снабжение"""
    __tablename__ = 'supply_order_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey('supply_orders.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    price_per_unit = db.Column(db.Float, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Связи
    order = db.relationship('SupplyOrder', backref='items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'unit': self.unit,
            'price_per_unit': self.price_per_unit,
            'total_price': self.total_price,
            'notes': self.notes
        }
