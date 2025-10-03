from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from uuid import UUID
from datetime import datetime

from app.services.crawler import WatchtowerCrawler
from app.services.database import DatabaseService

router = APIRouter()
crawler = WatchtowerCrawler()
db_service = DatabaseService()

# IMPORTANT: /all must come BEFORE /{website_id} to avoid route conflicts
@router.post("/all")
async def scan_all_websites(
    background_tasks: BackgroundTasks,
    strategy: str = Query("mobile", description="Strategy: mobile or desktop"),
    active_only: bool = Query(True, description="Scan only active websites")
):
    """
    Trigger a scan for all websites in the database
    
    This is typically used by the scheduler for weekly scans.
    The scan runs in the background and can take several minutes.
    """
    if strategy not in ["mobile", "desktop"]:
        raise HTTPException(status_code=400, detail="Strategy must be 'mobile' or 'desktop'")
    
    try:
        # Get count of websites to scan
        websites = await db_service.get_all_websites(active_only=active_only)
        website_count = len(websites)
        
        if website_count == 0:
            raise HTTPException(status_code=404, detail="No websites found to scan")
        
        # Start crawl in background
        background_tasks.add_task(crawler.crawl_all_websites, strategy)
        
        return {
            "status": "scan_started",
            "website_count": website_count,
            "strategy": strategy,
            "active_only": active_only,
            "message": f"Batch scan initiated for {website_count} websites. This may take several minutes.",
            "timestamp": datetime.utcnow().isoformat(),
            "estimated_duration_minutes": website_count * 0.5
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate batch scan: {str(e)}")


@router.post("/url")
async def scan_single_url(
    url: str = Query(..., description="URL to scan (for testing)"),
    strategy: str = Query("mobile", description="Strategy: mobile or desktop")
):
    """
    Scan a single URL without storing results (useful for testing)
    """
    if strategy not in ["mobile", "desktop"]:
        raise HTTPException(status_code=400, detail="Strategy must be 'mobile' or 'desktop'")
    
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    
    try:
        result = await crawler.crawl_single_url(url, strategy)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/{website_id}")
async def scan_website(
    website_id: UUID,
    background_tasks: BackgroundTasks,
    strategy: str = Query("mobile", description="Strategy: mobile or desktop")
):
    """
    Trigger a scan for a specific website
    """
    if strategy not in ["mobile", "desktop"]:
        raise HTTPException(status_code=400, detail="Strategy must be 'mobile' or 'desktop'")
    
    try:
        website = await db_service.get_website_by_id(str(website_id))
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        if not website.get('is_active', True):
            raise HTTPException(status_code=400, detail="Website is not active")
        
        background_tasks.add_task(crawler.analyze_website, website, strategy)
        
        return {
            "status": "scan_started",
            "website_id": str(website_id),
            "website_name": website.get('name'),
            "website_url": website.get('url'),
            "strategy": strategy,
            "message": f"Scan initiated for {website.get('name')}. Results will be available shortly.",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate scan: {str(e)}")
