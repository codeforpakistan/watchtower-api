import httpx
import asyncio
from typing import Dict, Optional, Any
from urllib.parse import quote
from app.core.config import settings
from app.services.carbon_footprint import CarbonFootprintCalculator
import logging

logger = logging.getLogger(__name__)

class PageSpeedInsights:
    def __init__(self):
        self.api_key = settings.GOOGLE_PAGESPEED_API_KEY
        self.base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        self.carbon_calculator = CarbonFootprintCalculator()
        
    async def check_url_accessibility(self, url: str) -> bool:
        """Check if URL is accessible before making API call"""
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.head(url)
                return response.status_code < 400
        except Exception as e:
            logger.error(f"Error accessing URL {url}: {e}")
            return False
    
    def create_query_url(self, url: str, strategy: str = "mobile") -> str:
        """Create the PageSpeed Insights API query URL"""
        params = {
            "url": quote(url),
            "key": self.api_key,
            "strategy": strategy,
            "category": ["performance", "accessibility", "best-practices", "seo", "pwa"]
        }
        
        # Build query string with multiple categories
        query_parts = [f"url={params['url']}", f"key={params['key']}", f"strategy={params['strategy']}"]
        for category in params['category']:
            query_parts.append(f"category={category}")
            
        return f"{self.base_url}?{'&'.join(query_parts)}"
    
    async def analyze_url(self, url: str, strategy: str = "mobile") -> Optional[Dict[str, Any]]:
        """
        Analyze a URL using PageSpeed Insights API
        Returns comprehensive performance data including Core Web Vitals
        """
        # Check URL accessibility first
        is_accessible = await self.check_url_accessibility(url)
        if not is_accessible:
            logger.warning(f"URL {url} is not accessible")
            return None
            
        api_endpoint = self.create_query_url(url, strategy)
        logger.info(f"Analyzing {url} with strategy: {strategy}")
        
        try:
            # Add delay to respect rate limits
            await asyncio.sleep(1)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_endpoint)
                response.raise_for_status()
                data = response.json()
                
            # Extract comprehensive metrics
            lighthouse = data.get('lighthouseResult', {})
            loading_exp = data.get('loadingExperience', {})
            
            # Core Web Vitals from field data (real user data)
            field_metrics = loading_exp.get('metrics', {})
            
            # Extract all scores
            categories = lighthouse.get('categories', {})
            
            # Extract detailed metrics
            audits = lighthouse.get('audits', {})
            
            result = {
                "url": url,
                "strategy": strategy,
                "final_url": lighthouse.get('finalUrl', url),
                "fetch_time": lighthouse.get('fetchTime'),
                
                # Category scores (0-100)
                "scores": {
                    "performance": categories.get('performance', {}).get('score', 0) * 100 if categories.get('performance', {}).get('score') else 0,
                    "accessibility": categories.get('accessibility', {}).get('score', 0) * 100 if categories.get('accessibility', {}).get('score') else 0,
                    "best_practices": categories.get('best-practices', {}).get('score', 0) * 100 if categories.get('best-practices', {}).get('score') else 0,
                    "seo": categories.get('seo', {}).get('score', 0) * 100 if categories.get('seo', {}).get('score') else 0,
                    "pwa": categories.get('pwa', {}).get('score', 0) * 100 if categories.get('pwa', {}).get('score') else 0,
                },
                
                # Core Web Vitals (field data from real users)
                "field_data": {
                    "first_contentful_paint": field_metrics.get('FIRST_CONTENTFUL_PAINT', {}).get('percentile'),
                    "first_input_delay": field_metrics.get('FIRST_INPUT_DELAY', {}).get('percentile'),
                    "largest_contentful_paint": field_metrics.get('LARGEST_CONTENTFUL_PAINT', {}).get('percentile'),
                    "cumulative_layout_shift": field_metrics.get('CUMULATIVE_LAYOUT_SHIFT', {}).get('percentile'),
                    "interaction_to_next_paint": field_metrics.get('INTERACTION_TO_NEXT_PAINT', {}).get('percentile'),
                    "time_to_first_byte": field_metrics.get('EXPERIMENTAL_TIME_TO_FIRST_BYTE', {}).get('percentile'),
                },
                
                # Lab data (from Lighthouse simulation)
                "lab_data": {
                    "first_contentful_paint": audits.get('first-contentful-paint', {}).get('numericValue'),
                    "speed_index": audits.get('speed-index', {}).get('numericValue'),
                    "largest_contentful_paint": audits.get('largest-contentful-paint', {}).get('numericValue'),
                    "time_to_interactive": audits.get('interactive', {}).get('numericValue'),
                    "total_blocking_time": audits.get('total-blocking-time', {}).get('numericValue'),
                    "cumulative_layout_shift": audits.get('cumulative-layout-shift', {}).get('numericValue'),
                },
                
                # Additional metrics
                "metrics": {
                    "total_byte_weight": audits.get('total-byte-weight', {}).get('numericValue'),
                    "dom_size": audits.get('dom-size', {}).get('numericValue'),
                    "max_potential_fid": audits.get('max-potential-fid', {}).get('numericValue'),
                    "server_response_time": audits.get('server-response-time', {}).get('numericValue'),
                    "main_thread_work": audits.get('mainthread-work-breakdown', {}).get('numericValue'),
                    "bootup_time": audits.get('bootup-time', {}).get('numericValue'),
                },
                
                # Resource details
                "resources": {
                    "total_requests": len(lighthouse.get('audits', {}).get('network-requests', {}).get('details', {}).get('items', [])) if lighthouse.get('audits', {}).get('network-requests') else 0,
                    "third_party_summary": audits.get('third-party-summary', {}).get('details', {}),
                },
                
                # Diagnostics
                "diagnostics": {
                    "num_requests": audits.get('diagnostics', {}).get('details', {}).get('items', [{}])[0].get('numRequests') if audits.get('diagnostics') else None,
                    "num_scripts": audits.get('diagnostics', {}).get('details', {}).get('items', [{}])[0].get('numScripts') if audits.get('diagnostics') else None,
                    "num_stylesheets": audits.get('diagnostics', {}).get('details', {}).get('items', [{}])[0].get('numStylesheets') if audits.get('diagnostics') else None,
                    "num_fonts": audits.get('diagnostics', {}).get('details', {}).get('items', [{}])[0].get('numFonts') if audits.get('diagnostics') else None,
                },
                
                # Enhanced carbon footprint calculation
                "environmental_impact": self._calculate_enhanced_carbon_footprint(
                    audits.get('total-byte-weight', {}).get('numericValue', 0),
                    audits.get('server-response-time', {}).get('numericValue')
                ),
            }
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing {url}: {e}")
            return None
    
    def _calculate_enhanced_carbon_footprint(
        self, 
        total_bytes: int, 
        server_response_time_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate enhanced carbon footprint using the dedicated carbon service
        """
        if not total_bytes:
            return {
                "co2_grams": 0.0, 
                "total_mb": 0.0, 
                "energy_kwh": 0.0,
                "rating": "A+",
                "recommendations": []
            }
            
        # Use the dedicated carbon footprint calculator
        footprint = self.carbon_calculator.calculate_website_footprint(
            page_size_bytes=total_bytes,
            server_response_time_ms=server_response_time_ms
        )
        
        # Get comparison data
        comparison = self.carbon_calculator.compare_with_average(footprint)
        
        return {
            "co2_grams": footprint.total_co2_grams,
            "total_mb": footprint.data_transfer_mb,
            "energy_kwh": footprint.energy_kwh,
            "rating": comparison["rating"],
            "percentile": comparison["percentile"],
            "breakdown": {
                "data_transfer": footprint.data_transfer_co2,
                "server_processing": footprint.server_processing_co2,
                "network_transmission": footprint.network_transmission_co2,
                "end_user_device": footprint.end_user_device_co2
            },
            "vs_average_website": comparison["vs_average_website"],
            "recommendations": footprint.recommendations[:3],  # Top 3 recommendations
            "confidence_level": footprint.confidence_level,
            "methodology": footprint.methodology
        }
    
    async def analyze_both_strategies(self, url: str) -> Dict[str, Any]:
        """Analyze URL for both mobile and desktop strategies"""
        mobile_task = self.analyze_url(url, "mobile")
        desktop_task = self.analyze_url(url, "desktop")
        
        mobile_results, desktop_results = await asyncio.gather(
            mobile_task, desktop_task, return_exceptions=True
        )
        
        return {
            "mobile": mobile_results if not isinstance(mobile_results, Exception) else None,
            "desktop": desktop_results if not isinstance(desktop_results, Exception) else None,
        }