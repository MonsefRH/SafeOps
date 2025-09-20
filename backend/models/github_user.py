from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from  utils.db import db 
from models.user import User

class GithubUser(db.Model):
    __tablename__ = "github_users"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    github_id = db.Column(db.String(255), unique=True, nullable=False)
    access_token = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.UTC))
    
    user = db.relationship("User", backref="github_user")