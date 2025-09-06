import uuid
from ..extensions import db

class Columns(db.Model):
    __tablename__ = 'columns'

    columnid = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objectid = db.Column(db.String(36), db.ForeignKey('objects.objectid'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    modelid = db.Column(db.String(36), db.ForeignKey('models.modelid'), nullable=False)
    status = db.Column(db.String(100))
    finishdate = db.Column(db.DateTime)
    userid = db.Column(db.String(36), db.ForeignKey('users.userid'), nullable=False)