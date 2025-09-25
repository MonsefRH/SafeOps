from datetime import datetime
import pytz
from  utils.db import db 

class RepoConfig(db.Model):
    __tablename__ = "repo_configs"
    id = db.Column(db.Integer, primary_key=True)
    repo_id = db.Column(db.Integer, db.ForeignKey("selected_repos.id", ondelete="CASCADE"))
    file_path = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    content = db.Column(db.LargeBinary)
    sha = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.now(pytz.UTC))
    framework = db.Column(db.String(50))
    
    repo = db.relationship("SelectedRepo", backref="configs")
    
    __table_args__ = (
        db.UniqueConstraint("file_path", "repo_id", name="unique_file_path_repo_id"),
    )