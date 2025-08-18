from typing import List
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

from app.models.website import Website, WebsiteCreate, WebsiteResponse

router = APIRouter()

@router.get("/", response_model=List[WebsiteResponse])
async def list_websites():
    """List all monitored government websites"""
    return []

@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(website_id: UUID):
    """Get details of a specific website"""
    raise HTTPException(status_code=404, detail="Website not found")

@router.post("/", response_model=WebsiteResponse)
async def create_website(website: WebsiteCreate):
    """Add a new website to monitoring"""
    return WebsiteResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        **website.model_dump()
    )

@router.post("/{website_id}/scan")
async def trigger_scan(website_id: UUID):
    """Trigger a manual scan of a website"""
    return {"message": "Scan triggered", "website_id": str(website_id)}