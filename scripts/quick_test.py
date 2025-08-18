#!/usr/bin/env python3
"""
Quick test script for PageSpeed API
Run with: poetry run python scripts/quick_test.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.pagespeed import PageSpeedInsights
from app.core.config import settings

async def main():
    if not settings.GOOGLE_PAGESPEED_API_KEY or settings.GOOGLE_PAGESPEED_API_KEY == "your_pagespeed_api_key_here":
        print("❌ Please set GOOGLE_PAGESPEED_API_KEY in .env file")
        print("Get your API key from: https://console.cloud.google.com/apis/credentials")
        print("Make sure to enable PageSpeed Insights API first")
        return
    
    print("🚀 Testing PageSpeed Insights API...")
    pagespeed = PageSpeedInsights()
    
    # Test URLs
    test_urls = [
        "https://na.gov.pk",        # Pakistan National Assembly
        "https://www.gov.pk",       # Pakistan Government Portal
        "https://www.google.com",   # Fast reference site
    ]
    
    for url in test_urls:
        print(f"\n📊 Analyzing: {url}")
        print("-" * 60)
        
        result = await pagespeed.analyze_url(url, "mobile")
        
        if result:
            scores = result['scores']
            env = result['environmental_impact']
            
            print(f"✅ Performance: {scores['performance']}/100")
            print(f"♿ Accessibility: {scores['accessibility']}/100")
            print(f"🛡️  Best Practices: {scores['best_practices']}/100")
            print(f"🔍 SEO: {scores['seo']}/100")
            print(f"🌍 CO2 Emissions: {env['co2_grams']}g")
            print(f"📦 Page Size: {env['total_mb']}MB")
            
            # Core Web Vitals
            cwv = result['field_data']
            if cwv['largest_contentful_paint']:
                print(f"⚡ LCP: {cwv['largest_contentful_paint']}ms")
            if cwv['first_input_delay']:
                print(f"👆 FID: {cwv['first_input_delay']}ms")
            if cwv['cumulative_layout_shift']:
                print(f"📐 CLS: {cwv['cumulative_layout_shift']}")
        else:
            print("❌ Failed to analyze (check URL accessibility or API key)")

if __name__ == "__main__":
    asyncio.run(main())