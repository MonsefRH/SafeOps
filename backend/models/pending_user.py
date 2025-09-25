from  utils.db import db 

class PendingUser(db.Model):
    __tablename__ = "pending_users"
    email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    verification_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)