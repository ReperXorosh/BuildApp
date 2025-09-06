from flask_login import UserMixin
import uuid
from datetime import datetime, timezone, timedelta
import pytz

from ..extensions import db
from ..utils.timezone_utils import get_moscow_now

class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    userid = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    login = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    firstname = db.Column(db.String(100), nullable=True)
    secondname = db.Column(db.String(100), nullable=True)
    thirdname = db.Column(db.String(100), nullable=True)
    phonenumber = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=True)
    registration_date = db.Column(db.DateTime, nullable=False, default=get_moscow_now)
    last_login = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, nullable=True)
    is_online = db.Column(db.Boolean, default=False)

    def get_id(self):
        return str(self.userid)
    
    def update_activity(self):
        """Обновляет время последней активности пользователя"""
        from ..utils.timezone_utils import get_moscow_now
        self.last_activity = get_moscow_now()
        db.session.commit()
    
    def mark_online(self):
        """Отмечает пользователя как находящегося в сети"""
        from ..utils.timezone_utils import get_moscow_now
        self.is_online = True
        self.last_activity = get_moscow_now()
        db.session.commit()
    
    def mark_offline(self):
        """Отмечает пользователя как не находящегося в сети"""
        self.is_online = False
        db.session.commit()
    
    def get_online_status(self):
        """Возвращает статус пользователя в сети"""
        if not self.last_activity:
            return "Никогда не был в сети"
        
        from ..utils.timezone_utils import get_moscow_now
        now = get_moscow_now()
        time_diff = now - self.last_activity
        
        if self.is_online:
            return "В сети"
        elif time_diff.total_seconds() < 300:  # 5 минут
            return "Недавно в сети"
        elif time_diff.total_seconds() < 3600:  # 1 час
            minutes = int(time_diff.total_seconds() / 60)
            return f"Был в сети {minutes} мин. назад"
        elif time_diff.total_seconds() < 86400:  # 1 день
            hours = int(time_diff.total_seconds() / 3600)
            return f"Был в сети {hours} ч. назад"
        else:
            days = int(time_diff.total_seconds() / 86400)
            return f"Был в сети {days} дн. назад"