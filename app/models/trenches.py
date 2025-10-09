import uuid
from ..extensions import db

class Trenches(db.Model):
    __tablename__ = 'trenches'

    trenchid = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objectid = db.Column(db.UUID(as_uuid=True), db.ForeignKey('objects.id'), nullable=False)
    totaltrenchlength = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    finishdate = db.Column(db.DateTime)
    userid = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.userid'), nullable=False)

