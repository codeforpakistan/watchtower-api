from typing import List
from fastapi import APIRouter, HTTPException
from uuid import UUID
from datetime import datetime

from app.models.report import Report, ReportResponse

router = APIRouter()

@router.get("/website/{website_id}", response_model=List[ReportResponse])
async def get_website_reports(website_id: UUID):
    """Get all analysis reports for a specific website"""
    return []

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: UUID):
    """Get details of a specific report"""
    raise HTTPException(status_code=404, detail="Report not found")