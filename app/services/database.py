from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations using Supabase"""
    
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        
    async def get_all_websites(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all websites from the database"""
        # This will be implemented using MCP calls
        return []
    
    async def get_website_by_id(self, website_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific website by ID"""
        return None
    
    async def get_websites_for_crawling(self) -> List[Dict[str, Any]]:
        """Get all active websites that need to be crawled"""
        return []
    
    async def store_analysis_report(
        self,
        website_id: str,
        strategy: str,
        pagespeed_data: Dict[str, Any],
        ssl_data: Dict[str, Any],
        carbon_data: Dict[str, Any]
    ) -> str:
        """
        Store complete analysis report for a website
        
        Args:
            website_id: UUID of the website
            strategy: 'mobile' or 'desktop'
            pagespeed_data: Results from PageSpeed Insights
            ssl_data: Results from SSL checker
            carbon_data: Results from carbon footprint calculator
            
        Returns:
            Report ID (UUID)
        """
        # Calculate overall score
        overall_score = self._calculate_overall_score(pagespeed_data, ssl_data, carbon_data)
        shame_worthy = self._determine_shame_worthiness(pagespeed_data, ssl_data, carbon_data)
        
        report_data = {
            'website_id': website_id,
            'strategy': strategy,
            'scan_date': datetime.utcnow().isoformat(),
            
            # PageSpeed scores
            'performance_score': pagespeed_data.get('scores', {}).get('performance'),
            'accessibility_score': pagespeed_data.get('scores', {}).get('accessibility'),
            'best_practices_score': pagespeed_data.get('scores', {}).get('best_practices'),
            'seo_score': pagespeed_data.get('scores', {}).get('seo'),
            'pwa_score': pagespeed_data.get('scores', {}).get('pwa'),
            
            # Core Web Vitals (field data)
            'lcp_field': pagespeed_data.get('field_data', {}).get('largest_contentful_paint'),
            'fid_field': pagespeed_data.get('field_data', {}).get('first_input_delay'),
            'cls_field': pagespeed_data.get('field_data', {}).get('cumulative_layout_shift'),
            'inp_field': pagespeed_data.get('field_data', {}).get('interaction_to_next_paint'),
            'ttfb_field': pagespeed_data.get('field_data', {}).get('time_to_first_byte'),
            'fcp_field': pagespeed_data.get('field_data', {}).get('first_contentful_paint'),
            
            # Lab data
            'lcp_lab': pagespeed_data.get('lab_data', {}).get('largest_contentful_paint'),
            'speed_index': pagespeed_data.get('lab_data', {}).get('speed_index'),
            'tti': pagespeed_data.get('lab_data', {}).get('time_to_interactive'),
            'tbt': pagespeed_data.get('lab_data', {}).get('total_blocking_time'),
            'cls_lab': pagespeed_data.get('lab_data', {}).get('cumulative_layout_shift'),
            'fcp_lab': pagespeed_data.get('lab_data', {}).get('first_contentful_paint'),
            
            # Additional metrics
            'total_byte_weight': pagespeed_data.get('metrics', {}).get('total_byte_weight'),
            'dom_size': pagespeed_data.get('metrics', {}).get('dom_size'),
            'server_response_time': pagespeed_data.get('metrics', {}).get('server_response_time'),
            
            # SSL data
            'ssl_valid': ssl_data.get('certificate', {}).get('valid'),
            'ssl_expired': ssl_data.get('certificate', {}).get('expired'),
            'ssl_days_until_expiry': ssl_data.get('certificate', {}).get('days_until_expiry'),
            'ssl_issuer': ssl_data.get('certificate', {}).get('issuer'),
            'https_enforced': ssl_data.get('https_redirect', {}).get('enforced'),
            'hsts_enabled': ssl_data.get('https_redirect', {}).get('hsts_enabled'),
            'ssl_security_score': ssl_data.get('security_score'),
            'ssl_shame_worthy': ssl_data.get('shame_worthy', {}).get('worthy'),
            'ssl_shame_severity': ssl_data.get('shame_worthy', {}).get('severity'),
            
            # Carbon footprint
            'carbon_co2_grams': carbon_data.get('co2_grams'),
            'carbon_rating': carbon_data.get('rating'),
            'carbon_percentile': carbon_data.get('percentile'),
            'carbon_vs_average': carbon_data.get('vs_average_website'),
            'carbon_data_transfer': carbon_data.get('breakdown', {}).get('data_transfer'),
            'carbon_server_processing': carbon_data.get('breakdown', {}).get('server_processing'),
            'carbon_network_transmission': carbon_data.get('breakdown', {}).get('network_transmission'),
            'carbon_end_user_device': carbon_data.get('breakdown', {}).get('end_user_device'),
            
            # Overall metrics
            'overall_score': overall_score,
            'shame_worthy': shame_worthy,
            
            # Raw data for debugging
            'raw_pagespeed_data': pagespeed_data,
            'raw_ssl_data': ssl_data,
            'raw_carbon_data': carbon_data
        }
        
        # This will be implemented using MCP calls
        return str(uuid.uuid4())
    
    async def get_latest_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get latest reports across all websites"""
        return []
    
    async def get_website_reports(self, website_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get reports for a specific website"""
        return []
    
    async def get_leaderboard(
        self, 
        sort_by: str = 'overall_score',
        government_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard of government websites
        
        Args:
            sort_by: 'overall_score', 'performance_score', 'ssl_security_score', etc.
            government_level: Filter by 'federal', 'state', 'local'
            limit: Number of results to return
        """
        return []
    
    async def get_shame_wall(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get websites that are shame-worthy"""
        return []
    
    async def get_website_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about monitored websites"""
        return {
            'total_websites': 0,
            'total_reports': 0,
            'average_overall_score': 0,
            'shame_worthy_count': 0,
            'ssl_issues_count': 0,
            'latest_scan_date': None
        }
    
    def _calculate_overall_score(
        self, 
        pagespeed_data: Dict[str, Any],
        ssl_data: Dict[str, Any], 
        carbon_data: Dict[str, Any]
    ) -> float:
        """Calculate overall score from all metrics"""
        scores = []
        weights = []
        
        # PageSpeed scores (weight: 40%)
        performance = pagespeed_data.get('scores', {}).get('performance', 0)
        accessibility = pagespeed_data.get('scores', {}).get('accessibility', 0)
        best_practices = pagespeed_data.get('scores', {}).get('best_practices', 0)
        seo = pagespeed_data.get('scores', {}).get('seo', 0)
        
        if performance > 0:
            scores.extend([performance, accessibility, best_practices, seo])
            weights.extend([0.15, 0.10, 0.10, 0.05])  # Total: 40%
        
        # SSL security score (weight: 30%)
        ssl_score = ssl_data.get('security_score', 0)
        if ssl_score > 0:
            scores.append(ssl_score)
            weights.append(0.30)
        
        # Carbon footprint score (weight: 20%) - convert percentile to 0-100 score
        carbon_percentile = carbon_data.get('percentile', 0)
        if carbon_percentile > 0:
            scores.append(carbon_percentile)
            weights.append(0.20)
        
        # Mobile-friendliness bonus (weight: 10%)
        # This could be derived from accessibility and performance scores
        mobile_bonus = min(performance, accessibility) if performance > 0 and accessibility > 0 else 0
        if mobile_bonus > 0:
            scores.append(mobile_bonus)
            weights.append(0.10)
        
        # Calculate weighted average
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0
        
        return 0
    
    def _determine_shame_worthiness(
        self,
        pagespeed_data: Dict[str, Any],
        ssl_data: Dict[str, Any],
        carbon_data: Dict[str, Any]
    ) -> bool:
        """Determine if a website is shame-worthy based on all metrics"""
        # SSL issues are immediate shame
        if ssl_data.get('shame_worthy', {}).get('worthy', False):
            return True
        
        # Very poor performance
        performance = pagespeed_data.get('scores', {}).get('performance', 100)
        if performance < 30:
            return True
        
        # Very poor accessibility 
        accessibility = pagespeed_data.get('scores', {}).get('accessibility', 100)
        if accessibility < 50:
            return True
        
        # Terrible carbon footprint (bottom 10%)
        carbon_percentile = carbon_data.get('percentile', 100)
        if carbon_percentile < 10:
            return True
        
        return False