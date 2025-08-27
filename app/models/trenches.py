import uuid
from ..extensions import db

class Trenches(db.Model):
    __tablename__ = 'trenches'

    trenchid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    objectid = db.Column(db.String(36), db.ForeignKey('objects.objectid'), nullable=False)
    totaltrenchlength = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    finishdate = db.Column(db.DateTime)
    userid = db.Column(db.String(36), db.ForeignKey('users.userid'), nullable=False)

