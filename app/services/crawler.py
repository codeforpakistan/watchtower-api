import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.pagespeed import PageSpeedInsights
from app.services.ssl_checker import SSLChecker
from app.services.database import DatabaseService
from app.core.config import settings

logger = logging.getLogger(__name__)

class WatchtowerCrawler:
    """
    Main crawler service that orchestrates website analysis
    Combines PageSpeed, SSL, and Carbon footprint analysis
    """
    
    def __init__(self):
        self.pagespeed = PageSpeedInsights()
        self.ssl_checker = SSLChecker()
        self.db = DatabaseService()
        self.max_concurrent = settings.MAX_CONCURRENT_SCANS
        
    async def crawl_all_websites(self, strategy: str = "mobile") -> Dict[str, Any]:
        """
        Crawl all active websites in the database
        
        Args:
            strategy: 'mobile' or 'desktop'
            
        Returns:
            Summary of crawl results
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting crawl of all websites with {strategy} strategy")
        
        # Get all websites to crawl
        websites = await self.db.get_websites_for_crawling()
        
        if not websites:
            logger.warning("No websites found to crawl")
            return {
                "status": "completed",
                "websites_crawled": 0,
                "duration_seconds": 0,
                "errors": []
            }
        
        logger.info(f"Found {len(websites)} websites to crawl")
        
        # Process websites in batches to respect rate limits
        results = []
        errors = []
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def crawl_single_website(website: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Crawl a single website with semaphore protection"""
            async with semaphore:
                try:
                    return await self.analyze_website(website, strategy)
                except Exception as e:
                    error_msg = f"Failed to crawl {website.get('url', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    return None
        
        # Create tasks for all websites
        tasks = [crawl_single_website(website) for website in websites]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        # Log exceptions
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "status": "completed",
            "websites_crawled": len(successful_results),
            "total_websites": len(websites),
            "duration_seconds": round(duration, 2),
            "errors": errors,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "strategy": strategy
        }
        
        logger.info(f"Crawl completed: {len(successful_results)}/{len(websites)} websites analyzed in {duration:.2f}s")
        
        return summary
    
    async def analyze_website(
        self, 
        website: Dict[str, Any], 
        strategy: str = "mobile"
    ) -> Dict[str, Any]:
        """
        Perform complete analysis of a single website
        
        Args:
            website: Website data from database
            strategy: 'mobile' or 'desktop'
            
        Returns:
            Analysis results
        """
        website_id = website['id']
        url = website['url']
        name = website['name']
        
        logger.info(f"Analyzing {name} ({url}) with {strategy} strategy")
        
        # Initialize results
        analysis_result = {
            "website_id": website_id,
            "website_name": name,
            "url": url,
            "strategy": strategy,
            "timestamp": datetime.utcnow().isoformat(),
            "success": False,
            "errors": []
        }
        
        try:
            # Run PageSpeed and SSL analysis in parallel
            pagespeed_task = self._analyze_pagespeed(url, strategy)
            ssl_task = self._analyze_ssl(url)
            
            # Wait for both to complete
            pagespeed_data, ssl_data = await asyncio.gather(
                pagespeed_task, 
                ssl_task, 
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(pagespeed_data, Exception):
                analysis_result["errors"].append(f"PageSpeed analysis failed: {str(pagespeed_data)}")
                pagespeed_data = self._get_empty_pagespeed_data()
                
            if isinstance(ssl_data, Exception):
                analysis_result["errors"].append(f"SSL analysis failed: {str(ssl_data)}")
                ssl_data = self._get_empty_ssl_data()
            
            # Extract carbon footprint data from PageSpeed results
            carbon_data = pagespeed_data.get('environmental_impact', {})
            
            # Store results in database
            try:
                report_id = await self.db.store_analysis_report(
                    website_id=website_id,
                    strategy=strategy,
                    pagespeed_data=pagespeed_data,
                    ssl_data=ssl_data,
                    carbon_data=carbon_data
                )
                
                analysis_result.update({
                    "success": True,
                    "report_id": report_id,
                    "pagespeed_score": pagespeed_data.get('scores', {}).get('performance', 0),
                    "ssl_score": ssl_data.get('security_score', 0),
                    "carbon_rating": carbon_data.get('rating', 'Unknown'),
                    "overall_score": self.db._calculate_overall_score(pagespeed_data, ssl_data, carbon_data),
                    "shame_worthy": self.db._determine_shame_worthiness(pagespeed_data, ssl_data, carbon_data)
                })
                
                logger.info(f"✅ Successfully analyzed {name}: Performance={analysis_result['pagespeed_score']}, SSL={analysis_result['ssl_score']}, Carbon={analysis_result['carbon_rating']}")
                
            except Exception as e:
                analysis_result["errors"].append(f"Database storage failed: {str(e)}")
                logger.error(f"Failed to store results for {name}: {e}")
                
        except Exception as e:
            analysis_result["errors"].append(f"General analysis failure: {str(e)}")
            logger.error(f"Analysis failed for {name}: {e}")
        
        return analysis_result
    
    async def _analyze_pagespeed(self, url: str, strategy: str) -> Dict[str, Any]:
        """Analyze website with PageSpeed Insights"""
        try:
            result = await self.pagespeed.analyze_url(url, strategy)
            if result is None:
                raise Exception("PageSpeed analysis returned None")
            return result
        except Exception as e:
            logger.error(f"PageSpeed analysis failed for {url}: {e}")
            raise
    
    async def _analyze_ssl(self, url: str) -> Dict[str, Any]:
        """Analyze website SSL configuration"""
        try:
            result = await self.ssl_checker.check_ssl_comprehensive(url)
            if "error" in result:
                raise Exception(result["error"])
            return result
        except Exception as e:
            logger.error(f"SSL analysis failed for {url}: {e}")
            raise
    
    def _get_empty_pagespeed_data(self) -> Dict[str, Any]:
        """Return empty PageSpeed data structure for failed requests"""
        return {
            "url": "",
            "strategy": "mobile",
            "scores": {
                "performance": 0,
                "accessibility": 0,
                "best_practices": 0,
                "seo": 0,
                "pwa": 0
            },
            "field_data": {},
            "lab_data": {},
            "metrics": {},
            "environmental_impact": {
                "co2_grams": 0,
                "rating": "F",
                "percentile": 0
            }
        }
    
    def _get_empty_ssl_data(self) -> Dict[str, Any]:
        """Return empty SSL data structure for failed requests"""
        return {
            "security_score": 0,
            "certificate": {
                "valid": False,
                "expired": True,
                "days_until_expiry": 0
            },
            "https_redirect": {
                "enforced": False,
                "hsts_enabled": False
            },
            "shame_worthy": {
                "worthy": True,
                "severity": "critical",
                "reasons": ["Analysis failed"]
            }
        }
    
    async def crawl_single_url(self, url: str, strategy: str = "mobile") -> Dict[str, Any]:
        """
        Crawl a single URL (for testing/debugging)
        
        Args:
            url: URL to analyze
            strategy: 'mobile' or 'desktop'
            
        Returns:
            Analysis results (not stored in database)
        """
        logger.info(f"Single URL analysis: {url} ({strategy})")
        
        try:
            # Run analysis in parallel
            pagespeed_task = self._analyze_pagespeed(url, strategy)
            ssl_task = self._analyze_ssl(url)
            
            pagespeed_data, ssl_data = await asyncio.gather(
                pagespeed_task, 
                ssl_task, 
                return_exceptions=True
            )
            
            # Handle exceptions
            errors = []
            if isinstance(pagespeed_data, Exception):
                errors.append(f"PageSpeed: {str(pagespeed_data)}")
                pagespeed_data = self._get_empty_pagespeed_data()
                
            if isinstance(ssl_data, Exception):
                errors.append(f"SSL: {str(ssl_data)}")
                ssl_data = self._get_empty_ssl_data()
            
            carbon_data = pagespeed_data.get('environmental_impact', {})
            
            return {
                "url": url,
                "strategy": strategy,
                "timestamp": datetime.utcnow().isoformat(),
                "success": len(errors) == 0,
                "errors": errors,
                "pagespeed": pagespeed_data,
                "ssl": ssl_data,
                "carbon": carbon_data,
                "overall_score": self.db._calculate_overall_score(pagespeed_data, ssl_data, carbon_data),
                "shame_worthy": self.db._determine_shame_worthiness(pagespeed_data, ssl_data, carbon_data)
            }
            
        except Exception as e:
            logger.error(f"Single URL analysis failed for {url}: {e}")
            return {
                "url": url,
                "strategy": strategy,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "errors": [str(e)]
            }