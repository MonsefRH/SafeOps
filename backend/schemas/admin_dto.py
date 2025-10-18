from pydantic import BaseModel, field_validator
from typing import List

class UserStatsResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: str
    scan_count: int

    @field_validator('scan_count')
    @classmethod
    def validate_scan_count(cls, v):
        if v < 0:
            raise ValueError('Scan count must be greater than 0')
        return v


class AdminStatsResponse(BaseModel):
    total_users: int
    total_scans: int
    users: List[UserStatsResponse]

    @field_validator('total_users', 'total_scans')
    @classmethod
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError('Value must be greater than or equal to 0')
        return v