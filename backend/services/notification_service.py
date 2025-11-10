import os
import smtplib
import threading
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import current_app

from utils.db import db
from models.user import User
from models.notification import Notification

# On réutilise tes identifiants SMTP déjà définis dans services/email_template.py
from services.email_template import EMAIL_ADDRESS, EMAIL_PASSWORD


def _display_repo(repo: str) -> str:
    """Affiche un nom propre au lieu d’un chemin local ou d’un ID."""
    if not repo:
        return "votre projet"
    if repo.startswith(("http://", "https://")):
        parts = repo.rstrip("/").split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1].replace('.git','')}"
    if "/" in repo and not os.path.isabs(repo):
        segs = repo.split("/")
        if len(segs) == 2 and all(segs):
            return repo
    return os.path.basename(repo.rstrip("/")) or "votre projet"


def render_scan_completed_subject(repo: str, status: str, scan_id: int) -> str:
    emoji = "✅" if (status or "").upper() == "SUCCESS" else "❌"
    repo_disp = _display_repo(repo)
    return f"{emoji} SafeOps — Scan terminé · {repo_disp}"

def render_scan_completed_text(name: str, repo: str, status: str, findings_count: int, scan_id: int) -> str:
    repo_disp = _display_repo(repo)
    return f"""Hello {name},

Votre scan est terminé pour {repo_disp}.
Statut : {status}
Findings : {findings_count}

Vous pouvez consulter les détails dans SafeOps+ (Historique des scans).

— SafeOps
"""

def render_scan_completed_html(name: str, repo: str, status: str, findings_count: int, scan_id: int) -> str:
    color = "#16a34a" if (status or "").upper() == "SUCCESS" else "#dc2626"
    repo_disp = _display_repo(repo)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Scan terminé</title></head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f6f8ff">
  <table width="100%" style="background:#1e5fff;padding:18px 0"><tr><td align="center">
    <h1 style="color:#fff;margin:0">SafeOps</h1>
  </td></tr></table>
  <table align="center" width="100%" style="max-width:640px;background:#fff;border-radius:10px;padding:24px;margin-top:16px;box-shadow:0 4px 12px rgba(0,0,0,.06)">
    <tr><td>
      <h2 style="margin:0 0 8px;color:#1e5fff">Scan terminé · {repo_disp}</h2>
      <p style="margin:8px 0;color:#333">Bonjour <b>{name}</b>,</p>
      <p style="margin:12px 0;color:#333">
        Statut : <b style="color:{color}">{status}</b><br/>
        Findings : <b>{findings_count}</b>
      </p>
      <p style="margin:12px 0;color:#555">Vous pouvez consulter le détail dans l’historique des scans.</p>
    </td></tr>
  </table>
  <table align="center" width="100%" style="max-width:640px;padding:16px;margin-top:12px;color:#999;text-align:center">
    <tr><td>© 2025 SafeOps Security Platform</td></tr>
  </table>
</body></html>"""

# Feature flag
NOTIFY_ENABLED = os.getenv("NOTIFY_ON_SCAN_COMPLETE", "true").lower() == "true"

# ----------------------------
# Envoi brut d'email
# ----------------------------
def _send_email_raw(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ----------------------------
# Persistance / marquage
# ----------------------------
def _persist_notification(**kwargs) -> Notification:
    n = Notification(**kwargs)
    db.session.add(n)
    db.session.commit()
    return n

def _mark_sent(n: Notification):
    if not n:
        return
    n.sent = True
    n.sent_at = datetime.now(timezone.utc)
    db.session.commit()

def _mark_failed(n: Notification, error_text: str):
    if not n:
        return
    n.error_text = error_text
    db.session.commit()

def _email_allowed(user_id: int) -> bool:
    pref = db.session.query(User).filter_by(id=user_id).first()
    return True if pref is None else bool(pref.email_notifications_enabled)

# ----------------------------
# Worker thread (avec app_context)
# ----------------------------
def _worker_send(app, user: User, repo: str, status: str, findings_count: int, scan_id: int, notification_id: int):
    """Exécuté dans un thread séparé. Ouvre un app_context() pour accéder à la DB."""
    with app.app_context():
        subject = render_scan_completed_subject(repo, status, scan_id)
        text = render_scan_completed_text(user.name, repo, status, findings_count, scan_id)
        html = render_scan_completed_html(user.name, repo, status, findings_count, scan_id)

        # SQLAlchemy 2.x : utiliser db.session.get()
        notif = db.session.get(Notification, notification_id)
        try:
            _send_email_raw(user.email, subject, text, html)
            _mark_sent(notif)
        except Exception as e:
            _mark_failed(notif, str(e))

# ----------------------------
# API publique à appeler par les services de scan
# ----------------------------
def notify_scan_completed(user_id: int, scan_id: int, repo: str, status: str, findings_count: int):
    """
    À appeler quand un scan se termine.
    - crée une ligne dans notifications (idempotence sur (scan_id, user_id))
    - lance un thread qui enverra l'email et mettra à jour 'sent'/'error_text'
    """
    if not NOTIFY_ENABLED:
        return

    # Récupère l'app courante AVANT de sortir du contexte de requête
    app = current_app._get_current_object()

    # Assure-toi d'avoir un int (get_jwt_identity() peut être une string)
    try:
        user_id_int = int(user_id)
    except Exception:
        user_id_int = user_id

    user = db.session.get(User, user_id_int)
    if not user:
        return

    if not _email_allowed(user_id_int):
        return

    # Idempotence
    exists = db.session.query(Notification).filter_by(user_id=user_id_int, scan_id=scan_id).first()
    if exists:
        return

    notif = _persist_notification(
        user_id=user_id_int,
        scan_id=scan_id,
        repo=repo,
        status=status,
        findings_count=findings_count,
        email=user.email,
        subject=render_scan_completed_subject(repo, status, scan_id),
    )

    t = threading.Thread(
        target=_worker_send,
        args=(app, user, repo, status, findings_count, scan_id, notif.id),
        daemon=True,
    )
    t.start()
