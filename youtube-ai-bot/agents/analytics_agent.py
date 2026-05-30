"""
agents/analytics_agent.py
──────────────────────────
Analytics + Learning Agent (100% FREE).
Fetches CTR, views, watch time from YouTube Studio API.
Uses Gemini to analyse patterns and update weekly strategy.
Feeds learnings back into strategy + script agents.
"""

from datetime import datetime
from utils.gemini import ask_json
from utils.logger import get_logger
from database import db
from config import config

log = get_logger("AnalyticsAgent")


def collect_all_analytics():
    """Fetch latest stats for all uploaded videos and update DB."""
    from agents.upload_agent import fetch_analytics
    jobs = db.get_recent_jobs(50)
    updated = 0
    for job in jobs:
        vid_id = job.get("video_id")
        if vid_id and job.get("status") == "success":
            stats = fetch_analytics(vid_id)
            if stats:
                db.update_analytics(vid_id, stats)
                updated += 1
    log.success(f"Analytics collected for {updated} videos")
    return updated


def analyse_and_learn() -> dict:
    """
    Deep performance analysis using Gemini.
    Returns actionable insights to update strategy.
    """
    perf = db.get_performance_data()
    if not perf or len(perf) < 3:
        log.info("Not enough data for analysis yet (need 3+ videos)")
        return {}

    # Prepare data for analysis
    data_str = "\n".join([
        f"• \"{v['title']}\" — {v['views']} views, "
        f"{v['likes']} likes, {v['avg_view_duration_pct']:.0f}% retention"
        for v in sorted(perf, key=lambda x: x["views"], reverse=True)
    ])

    log.info("🧠 Analysing performance with Gemini...")
    result = ask_json(f"""YouTube channel performance analyst.
Channel: {config.CHANNEL_NAME} | Niche: {config.CHANNEL_NICHE}

Video performance data:
{data_str}

Analyse patterns and return actionable insights as JSON:
{{
  "top_performing_patterns": ["what the best videos have in common"],
  "underperforming_reasons": ["why some videos didn't perform"],
  "best_title_style": "description of what title styles get most clicks",
  "best_topic_types": ["topic category 1", "topic category 2"],
  "optimal_video_length": "ideal duration in minutes based on data",
  "improvement_actions": ["action 1 for next video", "action 2", "action 3"],
  "avoid_next_week": ["what to avoid based on low performers"],
  "predicted_next_winner": "topic idea most likely to outperform based on patterns"
}}""")

    # Update strategy with learnings
    strategy = db.get_current_strategy() or {}
    if result.get("avoid_next_week"):
        strategy["avoid_topics"] = result["avoid_next_week"]
    if result.get("best_topic_types"):
        strategy["top_topics"] = result["best_topic_types"]
    strategy["niche"] = config.CHANNEL_NICHE
    db.save_strategy(strategy)

    log.success(f"Analysis complete — predicted winner: {result.get('predicted_next_winner','')[:60]}")
    return result
