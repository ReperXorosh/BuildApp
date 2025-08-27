import uuid
from ..extensions import db

class Reports(db.Model):
    __tablename__ = 'reports'

    reportid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    objectid = db.Column(db.String(36), db.ForeignKey('objects.objectid'), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime)
    userid = db.Column(db.String(36), db.ForeignKey('users.userid'), nullable=False)
    comment = db.Column(db.String(100), nullable=False)

