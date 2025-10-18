import pytest
from pydantic import ValidationError
from schemas.admin_dto import UserStatsResponse, AdminStatsResponse

def test_user_stats_response_valid():
    """Test valid UserStatsResponse."""
    data = {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "role": "user",
        "created_at": "2023-01-01T00:00:00",
        "scan_count": 5
    }
    response = UserStatsResponse(**data)
    assert response.id == 1
    assert response.name == "Test User"
    assert response.scan_count == 5
    assert response.model_dump()["created_at"] == "2023-01-01T00:00:00"

def test_user_stats_response_invalid():
    """Test invalid UserStatsResponse (e.g., negative scan_count)."""
    with pytest.raises(ValueError):
        UserStatsResponse(id=1, name="Test", email="test@example.com", role="user", created_at="2023-01-01T00:00:00", scan_count=-1)

def test_admin_stats_response_valid():
    """Test valid AdminStatsResponse serialization."""
    user_stats = [UserStatsResponse(id=1, name="User1", email="u1@example.com", role="user", created_at="2023-01-01T00:00:00", scan_count=3)]
    response = AdminStatsResponse(total_users=10, total_scans=50, users=user_stats)
    assert response.total_users == 10
    assert response.total_scans == 50
    assert len(response.users) == 1
    assert response.model_dump()["users"][0]["name"] == "User1"

def test_admin_stats_response_invalid():
    """Test invalid AdminStatsResponse (e.g., negative totals)."""
    with pytest.raises(ValueError):
        AdminStatsResponse(total_users=-5, total_scans=10, users=[])