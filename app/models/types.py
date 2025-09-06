import uuid
from ..extensions import db

class Types(db.Model):
    __tablename__ = 'types'

    typeid = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)