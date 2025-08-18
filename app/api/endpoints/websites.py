from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from uuid import UUID

from app.services.database import DatabaseService

router = APIRouter()
db_service = DatabaseService()

@router.get("/")
async def list_websites(
    active_only: bool = Query(True, description="Show only active websites"),
    government_level: Optional[str] = Query(None, description="Filter by government level")
):
    """List all monitored government websites with their latest scores"""
    try:
        websites = await db_service.get_all_websites(active_only=active_only)
        
        # Filter by government level if specified
        if government_level:
            websites = [w for w in websites if w.get('government_level') == government_level]
        
        return {
            "websites": websites,
            "total_count": len(websites),
            "active_only": active_only,
            "government_level_filter": government_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch websites: {str(e)}")

@router.get("/{website_id}")
async def get_website(website_id: UUID):
    """Get details of a specific website with its latest report"""
    try:
        website = await db_service.get_website_by_id(str(website_id))
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        # Get latest reports for this website
        reports = await db_service.get_website_reports(str(website_id), limit=5)
        
        return {
            "website": website,
            "latest_reports": reports,
            "report_count": len(reports)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch website: {str(e)}")

@router.get("/{website_id}/reports")
async def get_website_reports(
    website_id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Number of reports to return"),
    strategy: Optional[str] = Query(None, description="Filter by strategy (mobile/desktop)")
):
    """Get historical reports for a specific website"""
    try:
        reports = await db_service.get_website_reports(str(website_id), limit=limit)
        
        # Filter by strategy if specified
        if strategy:
            reports = [r for r in reports if r.get('strategy') == strategy]
        
        return {
            "website_id": str(website_id),
            "reports": reports,
            "total_count": len(reports),
            "strategy_filter": strategy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

@router.get("/{website_id}/latest")
async def get_website_latest_score(website_id: UUID):
    """Get the latest scores for a specific website"""
    try:
        reports = await db_service.get_website_reports(str(website_id), limit=1)
        
        if not reports:
            raise HTTPException(status_code=404, detail="No reports found for this website")
        
        latest_report = reports[0]
        
        return {
            "website_id": str(website_id),
            "latest_report": latest_report,
            "scan_date": latest_report.get('scan_date'),
            "overall_score": latest_report.get('overall_score'),
            "shame_worthy": latest_report.get('shame_worthy', False)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest score: {str(e)}")