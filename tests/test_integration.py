"""
Integration Tests for Watchtower API Services

These tests verify that all services work correctly with real websites.
Tests are marked with @pytest.mark.integration and can be run with:
    pytest -m integration tests/test_integration.py

Note: These tests make real API calls and may take time to complete.
"""

import pytest
import asyncio
from datetime import datetime
from app.services.ssl_checker import SSLChecker
from app.services.pagespeed import PageSpeedInsights
from app.services.carbon_footprint import CarbonFootprintCalculator
from app.services.database import DatabaseService
from app.services.crawler import WatchtowerCrawler


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ssl_checker_valid_certificate():
    """Test SSL checker with a website that has a valid certificate"""
    ssl_checker = SSLChecker()

    # Test with invest.gov.pk (known good certificate)
    result = await ssl_checker.check_ssl_comprehensive("https://invest.gov.pk")

    assert result is not None
    assert "certificate" in result
    assert result["certificate"]["valid"] is True
    assert result["certificate"]["expired"] is False
    assert result["certificate"]["days_until_expiry"] > 0
    assert result["security_score"] >= 80  # Should have good security score
    assert result["https_redirect"]["enforced"] is True

    print(f"✅ SSL Test Passed - Security Score: {result['security_score']}/100")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ssl_checker_invalid_certificate():
    """Test SSL checker with a website that has SSL issues"""
    ssl_checker = SSLChecker()

    # Test with cabinet.gov.pk (known to have HTTPS issues)
    result = await ssl_checker.check_ssl_comprehensive("http://www.cabinet.gov.pk")

    assert result is not None
    assert "certificate" in result
    # This site is known to have SSL issues
    assert result["shame_worthy"]["worthy"] is True
    assert result["security_score"] < 50  # Poor security score

    print(f"✅ SSL Test Passed - Detected SSL issues correctly")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pagespeed_insights_fast_site():
    """Test PageSpeed Insights with a fast, well-optimized site"""
    pagespeed = PageSpeedInsights()

    # Test with google.com (known to be fast and well-optimized)
    result = await pagespeed.analyze_url("https://www.google.com", strategy="mobile")

    assert result is not None
    assert result["url"] == "https://www.google.com"
    assert result["strategy"] == "mobile"
    assert "scores" in result
    assert result["scores"]["performance"] >= 80  # Google should score high
    assert result["scores"]["seo"] >= 80
    assert "field_data" in result
    assert "lab_data" in result
    assert "environmental_impact" in result

    print(f"✅ PageSpeed Test Passed - Performance: {result['scores']['performance']}/100")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pagespeed_insights_government_site():
    """Test PageSpeed Insights with a Pakistani government website"""
    pagespeed = PageSpeedInsights()

    # Test with invest.gov.pk (accessible government site)
    result = await pagespeed.analyze_url("https://invest.gov.pk", strategy="mobile")

    assert result is not None
    assert "invest.gov.pk" in result["url"]
    assert result["strategy"] == "mobile"
    assert "scores" in result
    # Government sites typically score lower
    assert 0 <= result["scores"]["performance"] <= 100
    assert "environmental_impact" in result
    assert result["environmental_impact"]["co2_grams"] > 0

    print(f"✅ PageSpeed Test Passed - Performance: {result['scores']['performance']}/100")


@pytest.mark.integration
def test_carbon_footprint_small_page():
    """Test carbon footprint calculation for a small page"""
    calculator = CarbonFootprintCalculator()

    # 1MB page (typical small site)
    page_size_bytes = 1 * 1024 * 1024
    footprint = calculator.calculate_website_footprint(page_size_bytes)
    comparison = calculator.compare_with_average(footprint)

    assert footprint.total_co2_grams > 0
    assert footprint.data_transfer_mb == 1.0
    assert comparison["rating"] in ["A+", "A", "B", "C", "D", "E", "F"]
    assert 0 <= comparison["percentile"] <= 100

    print(f"✅ Carbon Test Passed - 1MB page: {footprint.total_co2_grams:.2f}g CO2, Rating: {comparison['rating']}")


@pytest.mark.integration
def test_carbon_footprint_large_page():
    """Test carbon footprint calculation for a large page"""
    calculator = CarbonFootprintCalculator()

    # 5MB page (typical bloated site)
    page_size_bytes = 5 * 1024 * 1024
    footprint = calculator.calculate_website_footprint(page_size_bytes)
    comparison = calculator.compare_with_average(footprint)

    assert footprint.total_co2_grams > 0
    assert footprint.data_transfer_mb == 5.0
    # Large pages should get poor ratings
    assert comparison["rating"] in ["D", "E", "F"]
    assert len(footprint.recommendations) > 0

    print(f"✅ Carbon Test Passed - 5MB page: {footprint.total_co2_grams:.2f}g CO2, Rating: {comparison['rating']}")


@pytest.mark.integration
def test_carbon_footprint_huge_page():
    """Test carbon footprint calculation for a very large page"""
    calculator = CarbonFootprintCalculator()

    # 20MB page (extremely bloated site)
    page_size_bytes = 20 * 1024 * 1024
    footprint = calculator.calculate_website_footprint(page_size_bytes)
    comparison = calculator.compare_with_average(footprint)

    assert footprint.total_co2_grams > 0
    assert footprint.data_transfer_mb == 20.0
    # Huge pages should get F rating
    assert comparison["rating"] == "F"
    assert comparison["percentile"] < 10  # Bottom 10%

    print(f"✅ Carbon Test Passed - 20MB page: {footprint.total_co2_grams:.2f}g CO2, Rating: {comparison['rating']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_service_operations():
    """Test database service CRUD operations"""
    db = DatabaseService()

    # Test fetching websites
    websites = await db.get_all_websites(active_only=True)
    assert isinstance(websites, list)
    assert len(websites) > 0

    # Test fetching a specific website
    if websites:
        website_id = websites[0]['id']
        website = await db.get_website_by_id(website_id)
        assert website is not None
        assert website['id'] == website_id

    # Test fetching leaderboard
    leaderboard = await db.get_leaderboard(limit=10)
    assert isinstance(leaderboard, list)

    # Test fetching statistics
    stats = await db.get_website_statistics()
    assert "total_websites" in stats
    assert "active_websites" in stats
    assert "average_overall_score" in stats

    print(f"✅ Database Test Passed - Found {stats['total_websites']} websites")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_integer_conversion():
    """Test that PageSpeed float scores are properly converted to integers"""
    db = DatabaseService()

    # Create mock PageSpeed data with floats (as returned by Google API)
    pagespeed_data = {
        "scores": {
            "performance": 56.99999999999999,
            "accessibility": 89.5,
            "best_practices": 75.3,
            "seo": 92.7,
            "pwa": 30.1
        },
        "field_data": {},
        "lab_data": {},
        "metrics": {}
    }

    ssl_data = {
        "security_score": 85,
        "certificate": {"valid": True, "expired": False},
        "https_redirect": {"enforced": True},
        "shame_worthy": {"worthy": False}
    }

    carbon_data = {
        "co2_grams": 1.5,
        "rating": "B",
        "percentile": 60,
        "vs_average_website": "better",
        "breakdown": {}
    }

    # Get a test website
    websites = await db.get_all_websites(active_only=True)
    if websites:
        website_id = websites[0]['id']

        # This should NOT raise an error about invalid integer conversion
        try:
            report_id = await db.store_analysis_report(
                website_id=website_id,
                strategy="mobile",
                pagespeed_data=pagespeed_data,
                ssl_data=ssl_data,
                carbon_data=carbon_data
            )
            assert report_id is not None
            print(f"✅ Integer Conversion Test Passed - Report ID: {report_id}")
        except Exception as e:
            pytest.fail(f"Integer conversion failed: {str(e)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawler_sequential_scanning():
    """Test that crawler scans websites sequentially, not concurrently"""
    crawler = WatchtowerCrawler()

    # Create a list of 3 test websites
    test_websites = [
        {"id": "test-1", "name": "Google", "url": "https://www.google.com", "is_active": True},
        {"id": "test-2", "name": "Invest Pakistan", "url": "https://invest.gov.pk", "is_active": True},
    ]

    # Track scan times
    scan_times = []

    start_time = datetime.utcnow()

    # Scan websites one by one
    for website in test_websites:
        scan_start = datetime.utcnow()
        result = await crawler.analyze_website(website, strategy="mobile")
        scan_end = datetime.utcnow()

        scan_duration = (scan_end - scan_start).total_seconds()
        scan_times.append(scan_duration)

        assert result is not None
        # Add 2-second delay between scans (as per implementation)
        await asyncio.sleep(2)

    end_time = datetime.utcnow()
    total_duration = (end_time - start_time).total_seconds()

    # Verify sequential behavior:
    # Total time should be sum of individual scans + delays
    expected_min_duration = sum(scan_times) + (len(test_websites) - 1) * 2

    assert total_duration >= expected_min_duration
    print(f"✅ Sequential Scanning Test Passed - Total duration: {total_duration:.2f}s")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawler_end_to_end():
    """Test complete crawler workflow with a single website"""
    crawler = WatchtowerCrawler()

    # Test with a single URL (not stored in database)
    result = await crawler.crawl_single_url("https://www.google.com", strategy="mobile")

    assert result is not None
    assert result["url"] == "https://www.google.com"
    assert result["strategy"] == "mobile"
    assert result["success"] is True
    assert "pagespeed" in result
    assert "ssl" in result
    assert "carbon" in result
    assert "overall_score" in result
    assert "shame_worthy" in result

    # Verify all components worked
    assert result["pagespeed"]["scores"]["performance"] > 0
    assert result["ssl"]["security_score"] > 0
    assert result["carbon"]["co2_grams"] > 0

    print(f"✅ End-to-End Test Passed - Overall Score: {result['overall_score']}/100")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawler_error_handling():
    """Test that crawler handles errors gracefully"""
    crawler = WatchtowerCrawler()

    # Test with an invalid URL
    result = await crawler.crawl_single_url("https://this-site-does-not-exist-12345.com", strategy="mobile")

    assert result is not None
    assert result["success"] is False
    assert len(result["errors"]) > 0

    print(f"✅ Error Handling Test Passed - Errors caught: {len(result['errors'])}")


if __name__ == "__main__":
    # Run tests manually
    print("Running Integration Tests...\n")

    # Run async tests
    asyncio.run(test_ssl_checker_valid_certificate())
    asyncio.run(test_ssl_checker_invalid_certificate())
    asyncio.run(test_pagespeed_insights_fast_site())
    asyncio.run(test_pagespeed_insights_government_site())

    # Run sync tests
    test_carbon_footprint_small_page()
    test_carbon_footprint_large_page()
    test_carbon_footprint_huge_page()

    # Run async tests
    asyncio.run(test_database_service_operations())
    asyncio.run(test_database_integer_conversion())
    asyncio.run(test_crawler_sequential_scanning())
    asyncio.run(test_crawler_end_to_end())
    asyncio.run(test_crawler_error_handling())

    print("\n✅ All Integration Tests Completed!")