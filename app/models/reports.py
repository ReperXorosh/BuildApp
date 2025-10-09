import uuid
from ..extensions import db

class Reports(db.Model):
    __tablename__ = 'reports'

    reportid = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objectid = db.Column(db.UUID(as_uuid=True), db.ForeignKey('objects.id'), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime)
    userid = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)
    comment = db.Column(db.String(100), nullable=False)

