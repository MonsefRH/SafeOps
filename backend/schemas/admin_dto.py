from pydantic import BaseModel
from typing import List

class UserStatsResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: str
    scan_count: int

class AdminStatsResponse(BaseModel):
    total_users: int
    total_scans: int
    users: List[UserStatsResponse]