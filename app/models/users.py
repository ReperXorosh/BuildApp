from flask_login import UserMixin

from ..extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    userid = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    firstname = db.Column(db.String(100), nullable=True)
    secondname = db.Column(db.String(100), nullable=True)
    thirdname = db.Column(db.String(100), nullable=True)
    phonenumber = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.userid)