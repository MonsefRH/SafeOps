import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def notification_mock_app():
    """Flask app with working app_context()."""
    app = Mock()
    app._get_current_object.return_value = app

    # app_context() must return a context manager
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=None)
    ctx.__exit__ = MagicMock(return_value=False)
    app.app_context.return_value = ctx

    with patch("services.notification_service.current_app", app):
        yield app


@pytest.fixture
def notification_mock_user():
    user = Mock(
        id=1,
        name="Ahmed",
        email="ahmed@gmail.com",
        email_notifications_enabled=True
    )
    return user


@pytest.fixture
def notification_mock_notification():
    notif = Mock()
    notif.id = 2
    notif.sent = False
    notif.sent_at = None
    notif.error_text = None
    return notif


@pytest.fixture
def notification_mock_session(notification_mock_notification):
    sess = Mock()
    sess.get.return_value = None
    sess.add.return_value = None
    sess.commit.return_value = None
    sess.rollback.return_value = None

    # query chain for _email_allowed and idempotency
    query_chain = Mock()
    query_chain.filter_by.return_value.first.return_value = None
    sess.query.return_value = query_chain

    def add_side_effect(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = notification_mock_notification.id

    sess.add.side_effect = add_side_effect

    with patch("services.notification_service.db.session", sess):
        yield sess


@pytest.fixture
def mock_smtp():
    with patch("services.notification_service.smtplib.SMTP_SSL") as mock:
        smtp = Mock()
        mock.return_value.__enter__.return_value = smtp
        smtp.login.return_value = None
        smtp.send_message.return_value = None
        yield mock


@pytest.fixture
def mock_thread():
    with patch("services.notification_service.threading.Thread") as mock:
        mock.return_value.start.return_value = None
        yield mock


@pytest.fixture
def mock_render_functions():
    with patch("services.notification_service.render_scan_completed_subject", return_value="Subject"), \
         patch("services.notification_service.render_scan_completed_text", return_value="Text body"), \
         patch("services.notification_service.render_scan_completed_html", return_value="<html>Body</html>"):
        yield