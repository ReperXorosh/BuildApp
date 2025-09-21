from datetime import datetime, timedelta
import uuid
import secrets
from app.extensions import db

class RememberedDevice(db.Model):
    """Модель для запомненных устройств пользователей"""
    __tablename__ = 'remembered_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)
    device_token = db.Column(db.String(255), nullable=False, unique=True)
    device_name = db.Column(db.String(255), nullable=True)  # Название устройства (iPhone, Chrome, etc.)
    device_fingerprint = db.Column(db.String(255), nullable=True)  # Отпечаток устройства
    user_agent = db.Column(db.Text, nullable=True)  # User Agent браузера
    ip_address = db.Column(db.String(45), nullable=True)  # IP адрес
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связь с пользователем
    user = db.relationship('Users', backref=db.backref('remembered_devices', lazy=True, cascade='all, delete-orphan'))
    
    @staticmethod
    def generate_token():
        """Генерирует безопасный токен для устройства"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_for_user(user_id, device_name=None, device_fingerprint=None, user_agent=None, ip_address=None, days_valid=30):
        """Создает новую запись запомненного устройства для пользователя"""
        token = RememberedDevice.generate_token()
        expires_at = datetime.utcnow() + timedelta(days=days_valid)
        
        # Преобразуем user_id в UUID если это строка
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        device = RememberedDevice(
            user_id=user_id,
            device_token=token,
            device_name=device_name,
            device_fingerprint=device_fingerprint,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at
        )
        
        db.session.add(device)
        db.session.commit()
        return device
    
    @staticmethod
    def find_by_token(token):
        """Находит устройство по токену"""
        return RememberedDevice.query.filter_by(
            device_token=token,
            is_active=True
        ).first()
    
    @staticmethod
    def find_by_user_and_fingerprint(user_id, device_fingerprint):
        """Находит устройство по пользователю и отпечатку"""
        # Преобразуем user_id в UUID если это строка
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
            
        return RememberedDevice.query.filter_by(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            is_active=True
        ).first()
    
    def is_valid(self):
        """Проверяет, действителен ли токен устройства"""
        return (
            self.is_active and 
            self.expires_at > datetime.utcnow()
        )
    
    def update_last_used(self):
        """Обновляет время последнего использования"""
        self.last_used = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Деактивирует устройство"""
        self.is_active = False
        db.session.commit()
    
    def extend_expiry(self, days=30):
        """Продлевает срок действия токена"""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        db.session.commit()
    
    @staticmethod
    def cleanup_expired():
        """Удаляет истекшие токены"""
        expired_devices = RememberedDevice.query.filter(
            RememberedDevice.expires_at < datetime.utcnow()
        ).all()
        
        for device in expired_devices:
            device.deactivate()
    
    @staticmethod
    def get_user_devices(user_id):
        """Получает все активные устройства пользователя"""
        # Преобразуем user_id в UUID если это строка
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
            
        return RememberedDevice.query.filter_by(
            user_id=user_id,
            is_active=True
        ).filter(
            RememberedDevice.expires_at > datetime.utcnow()
        ).order_by(RememberedDevice.last_used.desc()).all()
    
    def __repr__(self):
        return f'<RememberedDevice {self.device_name or "Unknown"} for user {self.user_id}>'
