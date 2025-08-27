import uuid
from ..extensions import db

class Objects(db.Model):
    __tablename__ = 'objects'

    objectid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    address = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)