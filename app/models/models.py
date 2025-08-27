import uuid
from ..extensions import db

class Models(db.Model):
    __tablename__ = 'models'

    modelid = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    typeid = db.Column(db.String(36), db.ForeignKey('types.typeid'), nullable=False)