import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.crawler import WatchtowerCrawler
from app.core.config import settings

logger = logging.getLogger(__name__)


class WatchtowerScheduler:
    """
    Scheduler service for automated website scanning

    Features:
    - Weekly full scans of all websites (both mobile and desktop)
    - Configurable scan schedules
    - Automatic retry on failure
    - Logging and monitoring
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.crawler = WatchtowerCrawler()
        self.is_running = False

    async def weekly_scan_job(self):
        """
        Job that runs weekly to scan all websites
        This job runs scans for both mobile and desktop strategies
        """
        logger.info("=" * 80)
        logger.info("🚀 Starting scheduled weekly scan of all government websites")
        logger.info("=" * 80)

        try:
            # Scan with mobile strategy first
            logger.info("📱 Starting mobile scan...")
            mobile_result = await self.crawler.crawl_all_websites(strategy="mobile")
            logger.info(f"📱 Mobile scan completed: {mobile_result.get('websites_crawled', 0)} websites analyzed")

            # Wait a bit between scans to avoid rate limiting
            logger.info("⏳ Waiting 60 seconds before desktop scan...")
            await asyncio.sleep(60)

            # Scan with desktop strategy
            logger.info("💻 Starting desktop scan...")
            desktop_result = await self.crawler.crawl_all_websites(strategy="desktop")
            logger.info(f"💻 Desktop scan completed: {desktop_result.get('websites_crawled', 0)} websites analyzed")

            # Log summary
            logger.info("=" * 80)
            logger.info("✅ Weekly scan completed successfully")
            logger.info(f"   Mobile: {mobile_result.get('websites_crawled', 0)}/{mobile_result.get('total_websites', 0)} websites")
            logger.info(f"   Desktop: {desktop_result.get('websites_crawled', 0)}/{desktop_result.get('total_websites', 0)} websites")
            logger.info(f"   Total duration: {mobile_result.get('duration_seconds', 0) + desktop_result.get('duration_seconds', 0):.2f} seconds")
            logger.info("=" * 80)

            return {
                "status": "completed",
                "mobile_result": mobile_result,
                "desktop_result": desktop_result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Weekly scan failed: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def start(self):
        """
        Start the scheduler with configured jobs
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Schedule weekly scan
            # Default: Every Sunday at 2:00 AM UTC
            weekly_trigger = CronTrigger(
                day_of_week='sun',  # Sunday
                hour=2,             # 2 AM
                minute=0,           # At the top of the hour
                timezone='UTC'
            )

            self.scheduler.add_job(
                self.weekly_scan_job,
                trigger=weekly_trigger,
                id='weekly_scan',
                name='Weekly Government Website Scan',
                replace_existing=True,
                max_instances=1  # Only one scan can run at a time
            )

            logger.info("📅 Scheduled weekly scan: Every Sunday at 2:00 AM UTC")

            # For testing/development: optionally add a more frequent scan
            # Uncomment the following to run scans every hour (useful for testing)
            # if settings.DEBUG:
            #     hourly_trigger = IntervalTrigger(hours=1)
            #     self.scheduler.add_job(
            #         self.weekly_scan_job,
            #         trigger=hourly_trigger,
            #         id='hourly_scan',
            #         name='Hourly Scan (Debug)',
            #         replace_existing=True
            #     )
            #     logger.info("🔧 DEBUG MODE: Added hourly scan for testing")

            # Start the scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("✅ Scheduler started successfully")
            logger.info(f"   Active jobs: {len(self.scheduler.get_jobs())}")

            # Log next run time
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                next_run = job.next_run_time
                logger.info(f"   Next '{job.name}' run: {next_run}")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """
        Stop the scheduler gracefully
        """
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("🛑 Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}", exc_info=True)

    def get_status(self):
        """
        Get current scheduler status and job information
        """
        if not self.is_running:
            return {
                "status": "stopped",
                "jobs": []
            }

        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "status": "running",
            "jobs": jobs_info,
            "job_count": len(jobs_info)
        }

    async def trigger_scan_now(self, strategy: str = "mobile"):
        """
        Manually trigger a scan (useful for testing)
        """
        logger.info(f"🔥 Manual scan triggered with {strategy} strategy")
        return await self.crawler.crawl_all_websites(strategy=strategy)


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> WatchtowerScheduler:
    """
    Get or create the global scheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = WatchtowerScheduler()
    return _scheduler_instance