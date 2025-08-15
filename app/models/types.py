from ..extensions import db

class Types(db.Model):
    __tablename__ = 'types'

    typeid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)