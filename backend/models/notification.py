from utils.db import db
from datetime import datetime, timezone

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    scan_id = db.Column(db.Integer, nullable=False, index=True)
    repo = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(32), nullable=False)  # SUCCESS / FAILED
    findings_count = db.Column(db.Integer, nullable=False, default=0)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    sent = db.Column(db.Boolean, default=False)
    error_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('scan_id', 'user_id', name='uq_notifications_scan_user'),
    )
