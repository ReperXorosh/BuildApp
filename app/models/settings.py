from app.extensions import db
from datetime import datetime

class SystemSetting(db.Model):
    """Простое key-value хранилище системных настроек/состояний."""
    __tablename__ = 'system_settings'
    __table_args__ = (
        db.Index('ix_system_settings_key', 'key', unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(key: str, default: str | None = None) -> str | None:
        setting = SystemSetting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key: str, value: str) -> None:
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
