from typing import List, Optional
from fastapi import APIRouter, Query
from enum import Enum
from datetime import datetime

from app.models.leaderboard import LeaderboardEntry, LeaderboardResponse

class SortBy(str, Enum):
    performance = "performance"
    accessibility = "accessibility"
    design = "design"
    overall = "overall"

router = APIRouter()

@router.get("/", response_model=LeaderboardResponse)
async def get_leaderboard(
    sort_by: SortBy = Query(default=SortBy.overall),
    government_level: Optional[str] = Query(None, description="Filter by government level"),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get the performance leaderboard of government websites"""
    return LeaderboardResponse(
        entries=[],
        total_count=0,
        sort_by=sort_by,
        updated_at=datetime.utcnow()
    )