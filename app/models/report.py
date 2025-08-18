from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict, Optional, Any

class PageSpeedScores(BaseModel):
    performance: int
    accessibility: int
    best_practices: int
    seo: int
    pwa: int

class CoreWebVitals(BaseModel):
    # Field data (real user data)
    first_contentful_paint: Optional[float] = None
    first_input_delay: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    interaction_to_next_paint: Optional[float] = None
    time_to_first_byte: Optional[float] = None

class LabData(BaseModel):
    # Lab data (Lighthouse simulation)
    first_contentful_paint: Optional[float] = None
    speed_index: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    time_to_interactive: Optional[float] = None
    total_blocking_time: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None

class EnvironmentalImpact(BaseModel):
    co2_grams: float
    total_mb: float
    energy_kwh: float

class PageSpeedMetrics(BaseModel):
    total_byte_weight: Optional[float] = None
    dom_size: Optional[float] = None
    max_potential_fid: Optional[float] = None
    server_response_time: Optional[float] = None
    main_thread_work: Optional[float] = None
    bootup_time: Optional[float] = None

class PageSpeedResults(BaseModel):
    mobile: Optional[Dict[str, Any]] = None
    desktop: Optional[Dict[str, Any]] = None

class AIAnalysis(BaseModel):
    accessibility_score: int
    design_quality_score: int
    content_quality_score: int
    usability_score: int
    recommendations: list[str]
    language_accessibility: Optional[Dict[str, int]] = None

class Report(BaseModel):
    id: UUID
    website_id: UUID
    scan_date: datetime
    strategy: str  # mobile or desktop
    
    # PageSpeed Insights data
    pagespeed_scores: PageSpeedScores
    core_web_vitals: CoreWebVitals
    lab_data: LabData
    environmental_impact: EnvironmentalImpact
    additional_metrics: PageSpeedMetrics
    
    # AI Analysis
    ai_analysis: Optional[AIAnalysis] = None
    
    # Overall calculated score
    overall_score: float
    
    # Raw data for debugging
    raw_pagespeed_data: Optional[Dict[str, Any]] = None

class ReportResponse(Report):
    pass