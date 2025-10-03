from fastapi import APIRouter

from app.api.endpoints import websites, reports, leaderboard, scan, stats

api_router = APIRouter()

api_router.include_router(websites.router, prefix="/websites", tags=["websites"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
api_router.include_router(stats.router, prefix="/stats", tags=["statistics"])