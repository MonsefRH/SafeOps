from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from  utils.db import db 
from models.scan_history import ScanHistory

class FileContent(db.Model):
    __tablename__ = "file_contents"
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scan_history.id", ondelete="CASCADE"))
    file_path = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    input_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.UTC))
    
    scan = db.relationship("ScanHistory", backref="file_contents")