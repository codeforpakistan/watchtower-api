from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
from app.core.config import settings
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations using Supabase"""
    
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
    async def get_all_websites(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all websites from the database"""
        try:
            query = self.supabase.table('websites').select('*').order('name')
            
            if active_only:
                query = query.eq('is_active', True)
                
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch websites: {e}")
            return []
    
    async def get_website_by_id(self, website_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific website by ID"""
        try:
            response = self.supabase.table('websites').select('*').eq('id', website_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to fetch website {website_id}: {e}")
            return None
    
    async def get_websites_for_crawling(self) -> List[Dict[str, Any]]:
        """Get all active websites that need to be crawled"""
        return await self.get_all_websites(active_only=True)
    
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
        
        try:
            # Insert the report data
            response = self.supabase.table('reports').insert(report_data).execute()
            
            if response.data:
                report_id = response.data[0]['id']
                logger.info(f"Stored analysis report {report_id} for website {website_id}")
                return report_id
            else:
                logger.error(f"Failed to store report for website {website_id}")
                return str(uuid.uuid4())  # Fallback ID
                
        except Exception as e:
            logger.error(f"Error storing report for website {website_id}: {e}")
            return str(uuid.uuid4())  # Fallback ID
    
    async def get_latest_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get latest reports across all websites"""
        try:
            response = self.supabase.table('reports')\
                .select('*, websites(name, url)')\
                .order('scan_date', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch latest reports: {e}")
            return []
    
    async def get_website_reports(self, website_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get reports for a specific website"""
        try:
            response = self.supabase.table('reports')\
                .select('*')\
                .eq('website_id', website_id)\
                .order('scan_date', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch reports for website {website_id}: {e}")
            return []
    
    async def get_leaderboard(
        self, 
        sort_by: str = 'overall_score',
        government_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard of government websites with their latest scores
        """
        try:
            # Get latest report for each website using a subquery approach
            # This is a complex query, so we'll use RPC or raw SQL if needed
            
            # For now, let's use a simpler approach - get all websites and their latest reports
            websites = await self.get_all_websites(active_only=True)
            leaderboard = []
            
            for website in websites:
                if government_level and website.get('government_level') != government_level:
                    continue
                
                # Get latest report for this website
                reports = await self.get_website_reports(website['id'], limit=1)
                
                if reports:
                    report = reports[0]
                    leaderboard.append({
                        **website,
                        'latest_report': report,
                        'overall_score': report.get('overall_score', 0),
                        'performance_score': report.get('performance_score', 0),
                        'ssl_security_score': report.get('ssl_security_score', 0),
                        'scan_date': report.get('scan_date')
                    })
            
            # Sort by the specified column
            leaderboard.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
            
            return leaderboard[:limit]
            
        except Exception as e:
            logger.error(f"Failed to fetch leaderboard: {e}")
            return []
    
    async def get_shame_wall(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get websites that are shame-worthy"""
        try:
            # Get leaderboard and filter for shame-worthy sites
            leaderboard = await self.get_leaderboard(sort_by='overall_score', limit=100)
            
            shame_wall = []
            for entry in leaderboard:
                report = entry.get('latest_report', {})
                if report.get('shame_worthy'):
                    if not severity or report.get('ssl_shame_severity') == severity:
                        shame_wall.append({
                            **entry,
                            'shame_reasons': self._get_shame_reasons(report)
                        })
            
            return shame_wall
            
        except Exception as e:
            logger.error(f"Failed to fetch shame wall: {e}")
            return []
    
    async def get_website_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about monitored websites"""
        try:
            # Get basic counts
            websites = await self.get_all_websites(active_only=False)
            active_websites = [w for w in websites if w.get('is_active', True)]
            
            # Get reports statistics
            latest_reports = await self.get_latest_reports(limit=1000)  # Get more for stats
            
            shame_worthy_count = len([r for r in latest_reports if r.get('shame_worthy')])
            ssl_issues_count = len([r for r in latest_reports if not r.get('ssl_valid')])
            
            # Calculate average scores
            valid_scores = [r.get('overall_score', 0) for r in latest_reports if r.get('overall_score', 0) > 0]
            avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
            
            # Get latest scan date
            latest_scan = max([r.get('scan_date') for r in latest_reports if r.get('scan_date')], default=None)
            
            return {
                'total_websites': len(websites),
                'active_websites': len(active_websites),
                'total_reports': len(latest_reports),
                'average_overall_score': round(avg_score, 2),
                'shame_worthy_count': shame_worthy_count,
                'ssl_issues_count': ssl_issues_count,
                'latest_scan_date': latest_scan
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch statistics: {e}")
            return {
                'total_websites': 0,
                'total_reports': 0,
                'average_overall_score': 0,
                'shame_worthy_count': 0,
                'ssl_issues_count': 0,
                'latest_scan_date': None
            }
    
    def _get_shame_reasons(self, report: Dict[str, Any]) -> List[str]:
        """Extract shame reasons from a report"""
        reasons = []
        
        if report.get('ssl_expired'):
            reasons.append("Expired SSL certificate")
        elif not report.get('ssl_valid'):
            reasons.append("Invalid SSL certificate")
        elif not report.get('https_enforced'):
            reasons.append("HTTPS not enforced")
            
        performance = report.get('performance_score', 100)
        if performance < 30:
            reasons.append(f"Very poor performance ({performance}/100)")
            
        accessibility = report.get('accessibility_score', 100)
        if accessibility < 50:
            reasons.append(f"Poor accessibility ({accessibility}/100)")
            
        return reasons
    
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