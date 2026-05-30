"""
scheduler/jobs.py — All 24/7 automated tasks

UTC Schedule:
  Daily UPLOAD_HOUR     → Full pipeline (research → upload)
  Daily UPLOAD_HOUR+2h  → Analytics collection
  Sunday  08:00         → Weekly strategy + learning analysis
  Daily   03:00         → Analytics deep analysis + learning
  Saturday 02:00        → Database vacuum
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import config
from utils.logger import get_logger

log = get_logger("Scheduler")


def job_daily_video():
    log.info("⏰ Daily video pipeline triggered")
    from pipeline import run
    run()


def job_collect_analytics():
    log.info("📊 Collecting analytics...")
    from agents.analytics_agent import collect_all_analytics
    collect_all_analytics()


def job_deep_analysis():
    log.info("🧠 Running deep performance analysis + learning...")
    from agents.analytics_agent import analyse_and_learn

    insights = analyse_and_learn()

    if insights:
        log.info(
            f"Predicted winner: "
            f"{insights.get('predicted_next_winner', '')[:60]}"
        )


def job_weekly_strategy():
    log.info("📅 Weekly strategy review")

    from agents.strategy_agent import generate_weekly_strategy

    generate_weekly_strategy()
    job_deep_analysis()


def job_db_maintenance():
    log.info("🗄️ DB maintenance")

    import sqlite3

    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("VACUUM")
    conn.close()

    log.info("Database vacuumed")


def build_scheduler(blocking: bool = True):
    Cls = BlockingScheduler if blocking else BackgroundScheduler

    scheduler = Cls(timezone="UTC")

    scheduler.add_job(
        job_daily_video,
        CronTrigger(
            hour=config.UPLOAD_HOUR,
            minute=config.UPLOAD_MINUTE
        ),
        id="daily_video",
        name="Daily Video Pipeline",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600
    )

    scheduler.add_job(
        job_collect_analytics,
        CronTrigger(
            hour=(config.UPLOAD_HOUR + 2) % 24,
            minute=30
        ),
        id="analytics",
        name="Analytics Collection",
        max_instances=1
    )

    scheduler.add_job(
        job_deep_analysis,
        CronTrigger(hour=3, minute=0),
        id="deep_analysis",
        name="Daily Deep Analysis + Learning"
    )

    scheduler.add_job(
        job_weekly_strategy,
        CronTrigger(day_of_week="sun", hour=8, minute=0),
        id="weekly_strategy",
        name="Weekly Strategy Review"
    )

    scheduler.add_job(
        job_db_maintenance,
        CronTrigger(day_of_week="sat", hour=2, minute=0),
        id="db_maintenance",
        name="DB Maintenance"
    )

    log.info(
        f"Scheduler ready — {len(scheduler.get_jobs())} jobs"
    )

    for job in scheduler.get_jobs():
        try:
            next_run = getattr(job, "next_run_time", "N/A")
        except Exception:
            next_run = "N/A"

        log.info(
            f" • {job.name:<35} next: {next_run}"
        )

    return scheduler