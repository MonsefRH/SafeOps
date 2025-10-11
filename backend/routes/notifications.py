from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.db import db
from models.notification import Notification
from models.user_preference import UserPreference

bp_notifications = Blueprint("notifications", __name__, url_prefix="/api/notifications")

@bp_notifications.get("/")
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    rows = (Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .limit(100).all())
    data = [{
        "id": r.id, "scan_id": r.scan_id, "repo": r.repo, "status": r.status,
        "findings_count": r.findings_count, "email": r.email, "subject": r.subject,
        "sent": r.sent, "error_text": r.error_text,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
    } for r in rows]
    return jsonify(data)

@bp_notifications.patch("/preferences/email")
@jwt_required()
def toggle_email_pref():
    user_id = int(get_jwt_identity())
    body = request.get_json(force=True) or {}
    enabled = bool(body.get("enabled", True))
    pref = UserPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        pref = UserPreference(user_id=user_id, email_notifications_enabled=enabled)
        db.session.add(pref)
    else:
        pref.email_notifications_enabled = enabled
    db.session.commit()
    return jsonify({"email_notifications_enabled": pref.email_notifications_enabled})
