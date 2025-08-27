import uuid
from ..extensions import db

class Types(db.Model):
    __tablename__ = 'types'

    typeid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)