from datetime import datetime
import pytz
from  utils.db import db 

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.Text)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.UTC))
    
    __table_args__ = (
        db.CheckConstraint("role IN ('user', 'admin')", name="valid_role"),
    )