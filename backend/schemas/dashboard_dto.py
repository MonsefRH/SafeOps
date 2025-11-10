from pydantic import BaseModel, field_validator, ValidationError


class DashboardStatsResponse(BaseModel):
    policies: int
    alerts: int
    security_score: int

    @field_validator('policies','alerts','security_score')
    @classmethod
    def ensure_not_negative(cls, v):
        if v < 0:
            raise ValueError(f'Policies value {v} is negative')
        return v


class DashboardErrorResponse(BaseModel):
    error: str