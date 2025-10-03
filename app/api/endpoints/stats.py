from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta

from app.services.database import DatabaseService

router = APIRouter()
db_service = DatabaseService()

@router.get("/")
async def get_statistics():
    """
    Get comprehensive statistics for the dashboard

    Returns:
    - Total websites monitored
    - Average scores across all metrics
    - Recent scan summary
    - Performance trends
    - Top and bottom performers
    - SSL security overview
    - Carbon footprint summary
    """
    try:
        # Get all websites
        websites = await db_service.get_all_websites(active_only=True)
        total_websites = len(websites)

        # Get leaderboard data for statistics
        entries = await db_service.get_leaderboard(limit=total_websites)

        if not entries:
            return {
                "total_websites": total_websites,
                "websites_scanned": 0,
                "message": "No scan data available yet. Run a scan to populate statistics.",
                "timestamp": datetime.utcnow().isoformat()
            }

        # Calculate aggregate statistics
        websites_scanned = len(entries)

        # Performance metrics
        avg_performance = sum(e.get('performance_score', 0) for e in entries) / websites_scanned if websites_scanned > 0 else 0
        avg_accessibility = sum(e.get('accessibility_score', 0) for e in entries) / websites_scanned if websites_scanned > 0 else 0
        avg_best_practices = sum(e.get('best_practices_score', 0) for e in entries) / websites_scanned if websites_scanned > 0 else 0
        avg_seo = sum(e.get('seo_score', 0) for e in entries) / websites_scanned if websites_scanned > 0 else 0
        avg_overall = sum(e.get('overall_score', 0) for e in entries) / websites_scanned if websites_scanned > 0 else 0

        # SSL statistics (extract from latest_report)
        ssl_valid_count = sum(1 for e in entries if e.get('latest_report', {}).get('ssl_valid', False))
        ssl_expired_count = sum(1 for e in entries if e.get('latest_report', {}).get('ssl_expired', False))
        https_enforced_count = sum(1 for e in entries if e.get('latest_report', {}).get('https_enforced', False))
        hsts_enabled_count = sum(1 for e in entries if e.get('latest_report', {}).get('hsts_enabled', False))

        # Shame wall statistics (extract from latest_report)
        shame_worthy_count = sum(1 for e in entries if e.get('latest_report', {}).get('shame_worthy', False))
        ssl_shame_count = sum(1 for e in entries if e.get('latest_report', {}).get('ssl_shame_worthy', False))

        # Carbon footprint statistics (extract from latest_report)
        carbon_ratings = [e.get('latest_report', {}).get('carbon_rating') for e in entries if e.get('latest_report', {}).get('carbon_rating')]
        carbon_rating_counts = {}
        for rating in ['A+', 'A', 'B', 'C', 'D', 'F']:
            carbon_rating_counts[rating] = carbon_ratings.count(rating)

        avg_carbon_co2 = sum(e.get('latest_report', {}).get('carbon_co2_grams', 0) for e in entries) / websites_scanned if websites_scanned > 0 else 0

        # Top and bottom performers
        top_performers = sorted(entries, key=lambda x: x.get('overall_score', 0), reverse=True)[:5]
        bottom_performers = sorted(entries, key=lambda x: x.get('overall_score', 0))[:5]

        # Get most recent scan date
        most_recent_scan = None
        if entries:
            scan_dates = [e.get('scan_date') for e in entries if e.get('scan_date')]
            if scan_dates:
                most_recent_scan = max(scan_dates)

        return {
            "summary": {
                "total_websites": total_websites,
                "websites_scanned": websites_scanned,
                "websites_not_scanned": total_websites - websites_scanned,
                "scan_coverage_percent": round((websites_scanned / total_websites * 100), 2) if total_websites > 0 else 0,
                "most_recent_scan": most_recent_scan
            },
            "performance": {
                "average_performance_score": round(avg_performance, 2),
                "average_accessibility_score": round(avg_accessibility, 2),
                "average_best_practices_score": round(avg_best_practices, 2),
                "average_seo_score": round(avg_seo, 2),
                "average_overall_score": round(avg_overall, 2)
            },
            "security": {
                "ssl_valid_count": ssl_valid_count,
                "ssl_expired_count": ssl_expired_count,
                "https_enforced_count": https_enforced_count,
                "hsts_enabled_count": hsts_enabled_count,
                "ssl_compliance_percent": round((ssl_valid_count / websites_scanned * 100), 2) if websites_scanned > 0 else 0,
                "https_enforcement_percent": round((https_enforced_count / websites_scanned * 100), 2) if websites_scanned > 0 else 0
            },
            "shame_wall": {
                "total_shame_worthy": shame_worthy_count,
                "ssl_shame_worthy": ssl_shame_count,
                "shame_percentage": round((shame_worthy_count / websites_scanned * 100), 2) if websites_scanned > 0 else 0
            },
            "carbon_footprint": {
                "average_co2_grams": round(avg_carbon_co2, 2),
                "rating_distribution": carbon_rating_counts,
                "message": f"Average website emits {round(avg_carbon_co2, 2)}g of CO2 per page load"
            },
            "top_performers": [
                {
                    "name": p.get('name'),
                    "url": p.get('url'),
                    "overall_score": round(p.get('overall_score', 0), 2),
                    "performance_score": p.get('performance_score'),
                    "carbon_rating": p.get('latest_report', {}).get('carbon_rating')
                }
                for p in top_performers
            ],
            "bottom_performers": [
                {
                    "name": p.get('name'),
                    "url": p.get('url'),
                    "overall_score": round(p.get('overall_score', 0), 2),
                    "performance_score": p.get('performance_score'),
                    "shame_worthy": p.get('latest_report', {}).get('shame_worthy', False)
                }
                for p in bottom_performers
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")


@router.get("/summary")
async def get_summary():
    """
    Get a quick summary of key metrics (lighter endpoint for frequent polling)
    """
    try:
        websites = await db_service.get_all_websites(active_only=True)
        total_websites = len(websites)

        entries = await db_service.get_leaderboard(limit=total_websites)
        websites_scanned = len(entries)

        if not entries:
            return {
                "total_websites": total_websites,
                "websites_scanned": 0,
                "avg_score": 0,
                "message": "No data available"
            }

        avg_score = sum(e.get('overall_score', 0) for e in entries) / websites_scanned if websites_scanned > 0 else 0
        shame_count = sum(1 for e in entries if e.get('shame_worthy', False))

        return {
            "total_websites": total_websites,
            "websites_scanned": websites_scanned,
            "average_overall_score": round(avg_score, 2),
            "shame_worthy_count": shame_count,
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")