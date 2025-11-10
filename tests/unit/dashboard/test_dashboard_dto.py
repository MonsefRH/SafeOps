import pytest
from pydantic import ValidationError
from schemas.dashboard_dto import DashboardStatsResponse, DashboardErrorResponse

def test_dashboard_stats_valid():
    data = {"policies": 12, "alerts": 3, "security_score": 87}
    stats = DashboardStatsResponse(**data)
    assert stats.policies == 12
    assert stats.alerts == 3
    assert stats.security_score == 87
    assert stats.model_dump() == data

def test_dashboard_stats_negative_values():
    with pytest.raises(ValidationError):
        DashboardStatsResponse(policies=-1, alerts=0, security_score=100)

def test_dashboard_error_valid():
    err = DashboardErrorResponse(error="Something went wrong")
    assert err.error == "Something went wrong"
    assert err.model_dump() == {"error": "Something went wrong"}