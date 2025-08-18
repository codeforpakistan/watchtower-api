import asyncio
import json
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.pagespeed import PageSpeedInsights

async def test_pagespeed_analysis():
    """Test the PageSpeed Insights service"""
    
    # Test URLs
    test_urls = [
        "https://www.usa.gov",  # US government portal
        # Add more URLs as needed
    ]
    
    pagespeed = PageSpeedInsights()
    
    for url in test_urls:
        print(f"\nAnalyzing: {url}")
        print("-" * 80)
        
        # Analyze both mobile and desktop
        results = await pagespeed.analyze_both_strategies(url)
        
        # Display mobile results
        if results['mobile']:
            mobile = results['mobile']
            print("\n📱 MOBILE RESULTS:")
            print(f"Performance Score: {mobile['scores']['performance']}")
            print(f"Accessibility Score: {mobile['scores']['accessibility']}")
            print(f"Best Practices Score: {mobile['scores']['best_practices']}")
            print(f"SEO Score: {mobile['scores']['seo']}")
            
            print("\n🚀 Core Web Vitals (Field Data):")
            field_data = mobile['field_data']
            if field_data['largest_contentful_paint']:
                print(f"LCP: {field_data['largest_contentful_paint']}ms")
            if field_data['first_input_delay']:
                print(f"FID: {field_data['first_input_delay']}ms")
            if field_data['cumulative_layout_shift']:
                print(f"CLS: {field_data['cumulative_layout_shift']}")
            
            print("\n🌍 Environmental Impact:")
            env_impact = mobile['environmental_impact']
            print(f"CO2 Emissions: {env_impact['co2_grams']}g")
            print(f"Page Size: {env_impact['total_mb']}MB")
            print(f"Energy Usage: {env_impact['energy_kwh']} kWh")
            
        # Display desktop results
        if results['desktop']:
            desktop = results['desktop']
            print("\n💻 DESKTOP RESULTS:")
            print(f"Performance Score: {desktop['scores']['performance']}")
            print(f"Accessibility Score: {desktop['scores']['accessibility']}")
            print(f"Best Practices Score: {desktop['scores']['best_practices']}")
            print(f"SEO Score: {desktop['scores']['seo']}")
        
        # Save full results to file
        output_file = f"pagespeed_results_{url.replace('https://', '').replace('/', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Full results saved to: {output_file}")

if __name__ == "__main__":
    # Note: Make sure you have set GOOGLE_PAGESPEED_API_KEY in your .env file
    asyncio.run(test_pagespeed_analysis())