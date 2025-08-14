from ..extensions import db

class Reports(db.Model):
    __tablename__ = 'reports'

    reportid = db.Column(db.Integer, primary_key=True)
    objectid = db.Column(db.Integer, db.ForeignKey('objects.objectid'), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    comment = db.Column(db.String(100), nullable=False)

