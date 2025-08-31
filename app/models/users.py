from flask_login import UserMixin
import uuid
from datetime import datetime, timezone, timedelta
import pytz

from ..extensions import db

def get_moscow_time():
    """Возвращает текущее время в московском часовом поясе"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    return datetime.now(moscow_tz)

class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    userid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    login = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    firstname = db.Column(db.String(100), nullable=True)
    secondname = db.Column(db.String(100), nullable=True)
    thirdname = db.Column(db.String(100), nullable=True)
    phonenumber = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=True)
    registration_date = db.Column(db.DateTime, nullable=False, default=get_moscow_time)

    def get_id(self):
        return str(self.userid)