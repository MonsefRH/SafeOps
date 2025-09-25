from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    policies: int
    alerts: int
    security_score: int

class DashboardErrorResponse(BaseModel):
    error: str