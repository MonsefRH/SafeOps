from utils.db import db

class UserPreference(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, index=True, nullable=False)
    email_notifications_enabled = db.Column(db.Boolean, default=True)
