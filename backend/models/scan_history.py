from datetime import datetime
import pytz
from  utils.db import db 
from sqlalchemy.dialects.postgresql import JSONB

class ScanHistory(db.Model):
    __tablename__ = "scan_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repo_id = db.Column(db.Integer, db.ForeignKey("selected_repos.id", ondelete="SET NULL"))
    scan_result = db.Column(JSONB, nullable=False)
    repo_url = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer)
    compliant = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.UTC))
    input_type = db.Column(db.String(50))
    scan_type = db.Column(db.String(50))
    
    user = db.relationship("User", backref="scan_history")
    repo = db.relationship("SelectedRepo", backref="scan_history")