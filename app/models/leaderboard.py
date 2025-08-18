from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List

class LeaderboardEntry(BaseModel):
    rank: int
    website_id: UUID
    website_name: str
    website_url: str
    government_level: str
    overall_score: float
    performance_score: int
    accessibility_score: int
    design_score: int
    last_scan_date: datetime

class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_count: int
    sort_by: str
    updated_at: datetime