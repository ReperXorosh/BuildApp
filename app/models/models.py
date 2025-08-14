from ..extensions import db

class Columns(db.Model):
    __tablename__ = 'models'

    modelid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    typeid = db.Column(db.Integer, db.ForeignKey('types.typeid'), nullable=False)