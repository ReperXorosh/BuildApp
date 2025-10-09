import uuid
from ..extensions import db

class Models(db.Model):
    __tablename__ = 'models'

    modelid = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    typeid = db.Column(db.UUID(as_uuid=True), db.ForeignKey('types.typeid'), nullable=False)