import uuid
from datetime import datetime, timezone, timedelta
import pytz
from app.extensions import db

def get_moscow_time():
    """Возвращает текущее время в московском часовом поясе"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    return datetime.now(moscow_tz)

class ActivityLog(db.Model):
    """Модель журнала действий пользователей"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.userid'), nullable=True)
    user_login = db.Column(db.String(50), nullable=True)  # Сохраняем логин для быстрого поиска
    action = db.Column(db.String(100), nullable=False)  # Тип действия
    description = db.Column(db.Text, nullable=False)  # Описание действия
    ip_address = db.Column(db.String(45), nullable=True)  # IP адрес
    user_agent = db.Column(db.Text, nullable=True)  # User Agent браузера
    page_url = db.Column(db.String(500), nullable=True)  # URL страницы
    method = db.Column(db.String(10), nullable=True)  # HTTP метод
    status_code = db.Column(db.Integer, nullable=True)  # HTTP статус код
    created_at = db.Column(db.DateTime, default=get_moscow_time, nullable=False)
    
    # Связь с пользователем
    user = db.relationship('Users', backref='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.action} by {self.user_login} at {self.created_at}>'
    
    def to_dict(self):
        """Преобразует запись в словарь"""
        # Форматируем время в московском формате
        moscow_time = None
        if self.created_at:
            if self.created_at.tzinfo is None:
                # Если время без часового пояса, считаем его московским
                moscow_tz = timezone(timedelta(hours=3))
                moscow_time = self.created_at.replace(tzinfo=moscow_tz)
            else:
                # Если время с часовым поясом, конвертируем в московское
                moscow_tz = timezone(timedelta(hours=3))
                moscow_time = self.created_at.astimezone(moscow_tz)
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_login': self.user_login,
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'page_url': self.page_url,
            'method': self.method,
            'status_code': self.status_code,
            'created_at': moscow_time.isoformat() if moscow_time else None
        }
    
    @classmethod
    def log_action(cls, user_id=None, user_login=None, action="", description="", ip_address=None, page_url=None, method=None, **kwargs):
        """Создает запись в журнале действий"""
        try:
            log_entry = cls(
                user_id=user_id,
                user_login=user_login or "Неавторизованный пользователь",
                action=action,
                description=description,
                ip_address=ip_address,
                page_url=page_url,
                method=method,
                **kwargs
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            return log_entry
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при записи в журнал действий: {e}")
            return None
    
    @classmethod
    def get_recent_activities(cls, limit=50):
        """Получает последние действия"""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_user_activities(cls, user_id, limit=50):
        """Получает действия конкретного пользователя"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_activities_by_action(cls, action, limit=50):
        """Получает действия по типу"""
        return cls.query.filter_by(action=action).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_activities_by_date_range(cls, start_date, end_date, limit=100):
        """Получает действия за период"""
        return cls.query.filter(
            cls.created_at >= start_date,
            cls.created_at <= end_date
        ).order_by(cls.created_at.desc()).limit(limit).all()
