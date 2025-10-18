from datetime import datetime

import pytest
from unittest.mock import Mock
from services.admin_service import get_admin_stats


def test_get_admin_stats_valid(t5_mock_user_query, mock_scan_query, mock_filter_by_admin, t5_mock_db_session):
    """Test successful admin stats fetch."""
    # Mock total_users count
    mock_user_count = Mock()
    mock_user_count.count.return_value = 2

    # Use side_effect to return different mocks based on filter_by arguments
    t5_mock_user_query.filter_by.side_effect = lambda **kwargs: (
        mock_filter_by_admin if 'id' in kwargs else mock_user_count
    )

    # Mock total_scans count
    mock_scan_query.count.return_value = 50

    # Mock users with scan counts
    mock_user1 = Mock(spec=[])
    mock_user1.id = 1
    mock_user1.name = "User1"
    mock_user1.email = "u1@example.com"
    mock_user1.role = "user"
    mock_user1.created_at = datetime(2023, 1, 1)
    mock_user1.scan_count = 3

    mock_user2 = Mock(spec=[])
    mock_user2.id = 2
    mock_user2.name = "User2"
    mock_user2.email = "u2@example.com"
    mock_user2.role = "user"
    mock_user2.created_at = datetime(2023, 1, 2)
    mock_user2.scan_count = 0

    # Mock the complex db.session.query() chain
    mock_query_result = Mock()
    mock_query_result.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        mock_user1, mock_user2
    ]
    t5_mock_db_session.query.return_value = mock_query_result

    # Execute
    result = get_admin_stats(1)

    # Verify
    assert result["total_users"] == 2
    assert result["total_scans"] == 50
    assert len(result["users"]) == 2
    assert result["users"][0]["name"] == "User1"
    assert result["users"][0]["scan_count"] == 3
    assert result["users"][1]["name"] == "User2"
    assert result["users"][1]["scan_count"] == 0

def test_get_admin_stats_non_admin(t5_mock_user_query):
    """Test non-admin access denied."""
    # Mock non-admin user
    mock_user = Mock(role="user")
    t5_mock_user_query.filter_by.return_value.first.return_value = mock_user

    with pytest.raises(ValueError, match="Access denied: Admin role required"):
        get_admin_stats(1)


def test_get_admin_stats_no_users(t5_mock_user_query, mock_scan_query, mock_users_query, t5_mock_db_session,mock_filter_by_admin):
    """Test admin with no users."""
    t5_mock_user_query.filter_by.return_value = mock_filter_by_admin
    # Mock total_users count
    mock_user_count = Mock()
    mock_user_count.count.return_value = 0
    # When filter_by(role="user") is called for counting
    t5_mock_user_query.filter_by.side_effect = lambda **kwargs: (
        mock_filter_by_admin if 'id' in kwargs else mock_user_count
    )

    # Mock total_scans count
    mock_scan_query.count.return_value = 0

    # Mock the complex db.session.query() chain - RETURN EMPTY LIST
    mock_query_result = Mock()
    mock_query_result.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []
    t5_mock_db_session.query.return_value = mock_query_result

    result = get_admin_stats(1)

    assert result["total_users"] == 0
    assert result["total_scans"] == 0
    assert len(result["users"]) == 0


def test_get_admin_stats_exception(t5_mock_user_query, t5_mock_db_session,mock_filter_by_admin):
    """Test RuntimeError on query failure."""
    t5_mock_user_query.filter_by.return_value = mock_filter_by_admin
    # Mock query failure
    t5_mock_db_session.query.side_effect = Exception("DB error")

    with pytest.raises(RuntimeError, match="Error fetching admin stats"):
        get_admin_stats(1)

    t5_mock_db_session.rollback.assert_called_once()