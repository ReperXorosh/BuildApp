from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class UserPIN(db.Model):
    """Модель для хранения PIN-кодов пользователей"""
    __tablename__ = 'user_pins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False, unique=True)
    pin_hash = db.Column(db.String(255), nullable=False)
    is_biometric_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('pin', uselist=False))
    
    def set_pin(self, pin):
        """Установить PIN-код"""
        self.pin_hash = generate_password_hash(pin)
        self.updated_at = datetime.utcnow()
    
    def check_pin(self, pin):
        """Проверить PIN-код"""
        if self.pin_hash and check_password_hash(self.pin_hash, pin):
            self.last_used = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def enable_biometric(self):
        """Включить биометрическую аутентификацию"""
        self.is_biometric_enabled = True
        self.updated_at = datetime.utcnow()
    
    def disable_biometric(self):
        """Отключить биометрическую аутентификацию"""
        self.is_biometric_enabled = False
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<UserPIN {self.user_id}>'
