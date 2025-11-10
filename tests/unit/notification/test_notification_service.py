from unittest.mock import patch, Mock
from services.notification_service import notify_scan_completed, _worker_send


def test_notify_scan_completed_success(
    notification_mock_app,
    notification_mock_user,
    notification_mock_session,
    mock_thread,
    mock_render_functions
):
    """Happy path: notification created, thread started."""
    # User exists
    notification_mock_session.get.side_effect = lambda model, uid: (
        notification_mock_user if model.__name__ == "User" and uid == 1 else None
    )
    # No existing notification
    notification_mock_session.query.return_value.filter_by.return_value.first.return_value = None

    notify_scan_completed(
        user_id=1,
        scan_id=99,
        repo="https://github.com/user/repo.git",
        status="SUCCESS",
        findings_count=3
    )

    # Notification added
    notification_mock_session.add.assert_called_once()
    added_notif = notification_mock_session.add.call_args[0][0]
    assert added_notif.user_id == 1
    assert added_notif.scan_id == 99
    assert added_notif.email == "ahmed@gmail.com"
    assert added_notif.subject == "Subject"

    # Thread started
    mock_thread.assert_called_once()
    args = mock_thread.call_args[1]["args"]
    assert args[1] == notification_mock_user
    assert args[5] == 99
    assert args[6] == added_notif.id


def test_notify_scan_completed_disabled_by_env(
    notification_mock_app,
    notification_mock_user,
    notification_mock_session
):
    """Feature flag off → skip."""
    with patch("services.notification_service.NOTIFY_ENABLED", False):
        notify_scan_completed(user_id=1, scan_id=1, repo="", status="SUCCESS", findings_count=0)
    notification_mock_session.add.assert_not_called()


def test_notify_scan_completed_user_not_found(
    notification_mock_app,
    notification_mock_session
):
    """User missing → skip."""
    notification_mock_session.get.return_value = None
    notify_scan_completed(user_id=999, scan_id=1, repo="", status="SUCCESS", findings_count=0)
    notification_mock_session.add.assert_not_called()


def test_notify_scan_completed_email_disabled(
    notification_mock_app,
    notification_mock_user,
    notification_mock_session
):
    """email_notifications_enabled=False → skip."""
    notification_mock_user.email_notifications_enabled = False
    notification_mock_session.get.side_effect = lambda m, uid: notification_mock_user if uid == 1 else None
    # _email_allowed() queries User → mock it
    with patch("services.notification_service.db.session.query") as mock_query:
        mock_query.return_value.filter_by.return_value.first.return_value = notification_mock_user

        notify_scan_completed(user_id=1, scan_id=1, repo="", status="SUCCESS", findings_count=0)

    notification_mock_session.add.assert_not_called()


def test_notify_scan_completed_idempotent(
    notification_mock_app,
    notification_mock_user,
    notification_mock_session
):
    """Same scan_id + user_id → skip."""
    notification_mock_session.get.side_effect = lambda m, uid: notification_mock_user if uid == 1 else None
    notification_mock_session.query.return_value.filter_by.return_value.first.return_value = Mock()

    notify_scan_completed(user_id=1, scan_id=1, repo="", status="SUCCESS", findings_count=0)
    notification_mock_session.add.assert_not_called()


def test_worker_send_success(
    notification_mock_app,
    notification_mock_user,
    notification_mock_notification,
    mock_smtp,
    notification_mock_session,
    mock_render_functions
):
    """Email sent → mark sent."""
    notification_mock_session.get.return_value = notification_mock_notification

    _worker_send(
        notification_mock_app,
        notification_mock_user,
        "repo",
        "SUCCESS",
        3,
        99,
        notification_mock_notification.id
    )

    mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()
    assert notification_mock_notification.sent is True
    assert notification_mock_notification.sent_at is not None
    notification_mock_session.commit.assert_called()


def test_worker_send_failure(
    notification_mock_app,
    notification_mock_user,
    notification_mock_notification,
    mock_smtp,
    notification_mock_session,
    mock_render_functions
):
    """Email fails → mark error."""
    notification_mock_session.get.return_value = notification_mock_notification
    mock_smtp.return_value.__enter__.return_value.send_message.side_effect = Exception("SMTP error")

    _worker_send(
        notification_mock_app,
        notification_mock_user,
        "repo",
        "FAIL",
        1,
        99,
        notification_mock_notification.id
    )

    assert notification_mock_notification.error_text == "SMTP error"
    notification_mock_session.commit.assert_called()