import uuid
from datetime import datetime, timezone, timedelta
import pytz
from app.extensions import db
from app.utils.timezone_utils import get_moscow_now

class Material(db.Model):
    """Модель для материалов"""
    __tablename__ = 'materials'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    unit = db.Column(db.String(50), nullable=False)  # шт, кг, м, л и т.д.
    current_quantity = db.Column(db.Float, default=0.0)
    min_quantity = db.Column(db.Float, default=0.0)  # минимальный запас
    supplier = db.Column(db.String(200), nullable=True)
    price_per_unit = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=get_moscow_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_now, onupdate=get_moscow_now)
    
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

class WarehouseMovement(db.Model):
    """Движение по складу: поступления, выдачи, перемещения, возвраты, списания"""
    __tablename__ = 'warehouse_movements'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('materials.id'), nullable=False)
    # from_user/to_user: NULL означает склад
    from_user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=True)
    to_user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    movement_type = db.Column(db.String(32), nullable=False)  # add, move, return, writeoff
    note = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_moscow_now, nullable=False)

    # связи
    material = db.relationship('Material')
    from_user = db.relationship('Users', foreign_keys=[from_user_id])
    to_user = db.relationship('Users', foreign_keys=[to_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'material_id': self.material_id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'quantity': self.quantity,
            'movement_type': self.movement_type,
            'note': self.note,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class WarehouseAttachment(db.Model):
    """Файл-вложение, прикрепленный к движению по складу. Хранится в БД."""
    __tablename__ = 'warehouse_attachments'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movement_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('warehouse_movements.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(127), nullable=True)
    data = db.Column(db.LargeBinary, nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    uploaded_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=get_moscow_now, nullable=False)

    movement = db.relationship('WarehouseMovement', backref='attachments')

    def to_dict(self, include_data: bool = False):
        payload = {
            'id': self.id,
            'movement_id': self.movement_id,
            'filename': self.filename,
            'content_type': self.content_type,
            'size_bytes': self.size_bytes,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
        if include_data:
            payload['data'] = self.data
        return payload

class UserMaterialAllocation(db.Model):
    """Текущее распределение материалов по пользователям (денормализация для быстрых отчетов)."""
    __tablename__ = 'user_material_allocations'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)
    material_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Float, default=0.0, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_now, onupdate=get_moscow_now)

    user = db.relationship('Users')
    material = db.relationship('Material')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'material_id', name='uq_user_material'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'material_id': self.material_id,
            'quantity': self.quantity,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class Equipment(db.Model):
    """Модель для техники"""
    __tablename__ = 'equipment'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='available')  # available, in_use, maintenance, broken
    location = db.Column(db.String(200), nullable=True)
    supplier = db.Column(db.String(200), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    warranty_until = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=get_moscow_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_now, onupdate=get_moscow_now)
    
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
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = db.Column(db.String(50), nullable=False, unique=True)
    order_type = db.Column(db.String(50), nullable=False)  # material, equipment
    status = db.Column(db.String(50), default='pending')  # pending, approved, delivered, cancelled
    requested_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)
    approved_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=True)
    supplier = db.Column(db.String(200), nullable=True)
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_moscow_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_now, onupdate=get_moscow_now)
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
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('supply_orders.id'), nullable=False)
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

class SupplyRequest(db.Model):
    """Заявка на выдачу/закупку материалов"""
    __tablename__ = 'supply_requests'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(32), default='new')  # new, approved, rejected, fulfilled, cancelled
    requested_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)
    approver_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_moscow_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=get_moscow_now, onupdate=get_moscow_now)

    requester = db.relationship('Users', foreign_keys=[requested_by])
    approver = db.relationship('Users', foreign_keys=[approver_id])

    def to_dict(self):
        return {
            'id': self.id,
            'request_number': self.request_number,
            'status': self.status,
            'requested_by': self.requested_by,
            'approver_id': self.approver_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class SupplyRequestItem(db.Model):
    __tablename__ = 'supply_request_items'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('supply_requests.id'), nullable=False)
    material_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text)

    request = db.relationship('SupplyRequest', backref='items')
    material = db.relationship('Material')

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'material_id': self.material_id,
            'quantity': self.quantity,
            'unit': self.unit,
            'note': self.note,
        }
