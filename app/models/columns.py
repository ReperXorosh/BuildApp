from ..extensions import db

class Columns(db.Model):
    __tablename__ = 'columns'

    columnid = db.Column(db.Integer, primary_key=True)
    objectid = db.Column(db.Integer, db.ForeignKey('objects.objectid'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    modelid = db.Column(db.Integer, db.ForeignKey('models.modelid'), nullable=False)
    status = db.Column(db.String(100))
    finishdate = db.Column(db.DateTime)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)