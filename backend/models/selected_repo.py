from datetime import datetime
import pytz
from  utils.db import db 

class SelectedRepo(db.Model):
    __tablename__ = "selected_repos"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    full_name = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    html_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.UTC))
    
    user = db.relationship("User", backref="selected_repos")