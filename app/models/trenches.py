from ..extensions import db

class Trenches(db.Model):
    __tablename__ = 'trenches'

    trenchid = db.Column(db.Integer, primary_key=True)
    objectid = db.Column(db.Integer, db.ForeignKey('objects.objectid'), nullable=False)
    totaltrenchlength = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    finishdate = db.Column(db.DateTime)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)

