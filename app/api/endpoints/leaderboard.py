from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from enum import Enum
from datetime import datetime

from app.services.database import DatabaseService

class SortBy(str, Enum):
    overall_score = "overall_score"
    performance_score = "performance_score"
    accessibility_score = "accessibility_score"
    ssl_security_score = "ssl_security_score"
    carbon_rating = "carbon_rating"

router = APIRouter()
db_service = DatabaseService()

@router.get("/")
async def get_leaderboard(
    sort_by: SortBy = Query(default=SortBy.overall_score, description="Sort criteria"),
    government_level: Optional[str] = Query(None, description="Filter by government level"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of results"),
    ascending: bool = Query(False, description="Sort in ascending order (default: descending)")
):
    """Get the performance leaderboard of government websites"""
    try:
        leaderboard_data = await db_service.get_leaderboard(
            sort_by=sort_by.value,
            government_level=government_level,
            limit=limit
        )
        
        # Reverse order if ascending is requested
        if ascending:
            leaderboard_data.reverse()
        
        return {
            "entries": leaderboard_data,
            "total_count": len(leaderboard_data),
            "sort_by": sort_by.value,
            "government_level_filter": government_level,
            "ascending": ascending,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leaderboard: {str(e)}")

@router.get("/shame-wall")
async def get_shame_wall(
    severity: Optional[str] = Query(None, description="Filter by severity (critical, high, medium)"),
    limit: int = Query(default=50, ge=1, le=100, description="Number of results")
):
    """Get the shame wall - websites with poor performance/security"""
    try:
        shame_data = await db_service.get_shame_wall(severity=severity)
        
        # Limit results
        if limit and len(shame_data) > limit:
            shame_data = shame_data[:limit]
        
        return {
            "shame_wall": shame_data,
            "total_count": len(shame_data),
            "severity_filter": severity,
            "updated_at": datetime.utcnow().isoformat(),
            "description": "Government websites that need immediate attention for security, performance, or accessibility issues"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch shame wall: {str(e)}")

@router.get("/statistics")
async def get_statistics():
    """Get overall statistics about monitored websites"""
    try:
        stats = await db_service.get_website_statistics()
        
        return {
            "statistics": stats,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")

@router.get("/top-performers")
async def get_top_performers(
    category: str = Query("overall_score", description="Category to rank by"),
    limit: int = Query(10, ge=1, le=50, description="Number of top performers")
):
    """Get top performing government websites in a specific category"""
    try:
        # Get leaderboard data for the specific category
        top_performers = await db_service.get_leaderboard(
            sort_by=category,
            limit=limit
        )
        
        return {
            "top_performers": top_performers,
            "category": category,
            "total_count": len(top_performers),
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top performers: {str(e)}")

@router.get("/bottom-performers")
async def get_bottom_performers(
    category: str = Query("overall_score", description="Category to rank by"),
    limit: int = Query(10, ge=1, le=50, description="Number of bottom performers")
):
    """Get worst performing government websites in a specific category"""
    try:
        # Get leaderboard data for the specific category (ascending order for worst)
        bottom_performers = await db_service.get_leaderboard(
            sort_by=category,
            limit=limit
        )
        
        # Reverse to get worst performers
        bottom_performers.reverse()
        
        return {
            "bottom_performers": bottom_performers,
            "category": category,
            "total_count": len(bottom_performers),
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch bottom performers: {str(e)}")