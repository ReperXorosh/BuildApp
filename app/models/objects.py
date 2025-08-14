from ..extensions import db

class Objects(db.Model):
    __tablename__ = 'objects'

    objectid = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)