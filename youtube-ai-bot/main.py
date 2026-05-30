"""
main.py — Single entry point.

python main.py                           → 24/7 bot (scheduler + dashboard)
python main.py --run-now                 → One video now (auto topic)
python main.py --run-now --topic "X"     → One video on topic X
python main.py --niche technology        → Set niche then start bot
python main.py --dashboard               → Dashboard only
python main.py --strategy                → Run weekly strategy
python main.py --analyse                 → Run analytics + learning
python main.py --list-voices             → List TTS voices
python main.py --setup-check            → Verify all API keys
python main.py --cache-stats             → Show cache statistics
python main.py --library                 → Show content library stats
"""

import sys, os
from colorama import Fore, Style, init
init()

from config import config, load_live_config
from database import db
from utils.logger import get_logger

log = get_logger("Main")


def banner():
    load_live_config()
    from agents.niche_profiles import get_profile
    profile    = get_profile(config.CHANNEL_NICHE)
    lang_label = "Hindi 🇮🇳" if config.CHANNEL_LANGUAGE == "hi" else "English 🇺🇸"

    # Detect configured providers
    providers = []
    if config.GROQ_API_KEY and not config.GROQ_API_KEY.startswith("your_"):
        providers.append("Groq")
    if config.GEMINI_API_KEY and not config.GEMINI_API_KEY.startswith("your_"):
        providers.append("Gemini")
    if config.CEREBRAS_API_KEY and not config.CEREBRAS_API_KEY.startswith("your_"):
        providers.append("Cerebras")
    if config.OPENROUTER_API_KEY and not config.OPENROUTER_API_KEY.startswith("your_"):
        providers.append("OpenRouter")
    prov_str = " → ".join(providers) if providers else "⚠ No providers configured!"

    print(f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║   🤖  YouTube AI Bot  v4.0  ·  Multi-Provider Edition     ║
╠═══════════════════════════════════════════════════════════╣
║  Industry: {profile['emoji']} {profile['label']:<46}║
║  Channel:  {config.CHANNEL_NAME:<48}║
║  Language: {lang_label:<48}║
║  Voice:    {config.get_tts_voice():<48}║
╠═══════════════════════════════════════════════════════════╣
║  AI:        {prov_str:<46}║
║  Script:    {config.TARGET_WORD_COUNT_MIN}-{config.TARGET_WORD_COUNT_MAX} words (~{config.TARGET_DURATION_MIN}-{config.TARGET_DURATION_MAX} min){'':<28}║
║  AI Calls:  1 per video (unified agent, was 9+)           ║
║  Cache:     {'✓ Enabled (SQLite)' if config.CACHE_ENABLED else '✗ Disabled':<46}║
║  Voice:     edge-tts Microsoft Neural (free, unlimited)   ║
║  Footage:   Pexels + Pixabay (free)                       ║
║  Trends:    Google Trends + HackerNews + News RSS + Wiki  ║
║  Thumbnails:Pollinations.ai (free, unlimited)             ║
╠═══════════════════════════════════════════════════════════╣
║  Dashboard: http://0.0.0.0:{config.PORT:<31}║
║  Daily post:{config.UPLOAD_HOUR:02d}:{config.UPLOAD_MINUTE:02d} UTC{' '*42}║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")


def main():
    db.init_db()
    args = sys.argv[1:]

    # ── List voices ───────────────────────────────────────────
    if "--list-voices" in args:
        import subprocess
        print("\n🎙️  Available voices:\n")
        subprocess.run(["edge-tts", "--list-voices"])
        return

    # ── Setup check ───────────────────────────────────────────
    if "--setup-check" in args:
        from utils.check_setup import run_all
        run_all()
        return

    # ── Show videos ───────────────────────────────────────────
    if "--videos" in args:
        from utils.show_videos import show
        show()
        return

    # ── Cache stats ───────────────────────────────────────────
    if "--cache-stats" in args:
        from utils.cache import get_stats
        s = get_stats()
        print(f"\n📦 Cache Statistics:")
        print(f"  Entries:    {s['total_entries']}")
        print(f"  Today hits: {s['today_hits']}")
        print(f"  Today miss: {s['today_misses']}")
        print(f"  Hit rate:   {s['hit_rate_pct']}%")
        print(f"  Saves:      {s['saves_today']}\n")
        return

    # ── Library stats ─────────────────────────────────────────
    if "--library" in args:
        from utils.content_library import get_library_stats
        s = get_library_stats()
        print(f"\n📚 Content Library:")
        print(f"  Total entries:   {s['total_entries']}")
        print(f"  Research facts:  {s['research_facts']}")
        print(f"  By type:  {s['by_type']}")
        print(f"  By niche: {s['by_niche']}\n")
        return

    # ── Set niche ─────────────────────────────────────────────
    if "--niche" in args:
        idx = args.index("--niche")
        if idx + 1 < len(args):
            niche = args[idx + 1]
            from agents.niche_profiles import get_profile, NICHE_PROFILES
            if niche not in NICHE_PROFILES:
                print(f"Unknown niche '{niche}'. Options: {', '.join(NICHE_PROFILES.keys())}")
                return
            profile = get_profile(niche)
            db.set_setting("CHANNEL_NICHE",    niche)
            db.set_setting("CHANNEL_LANGUAGE", profile.get("force_language", "en"))
            db.set_setting("CHANNEL_TONE",     profile["tone"])
            load_live_config()
            print(f"✅ Niche set to: {profile['emoji']} {profile['label']}")
            if "--run-now" not in args:
                return

    banner()

    # ── One-shot run ──────────────────────────────────────────
    if "--run-now" in args:
        topic = None
        if "--topic" in args:
            idx = args.index("--topic")
            if idx + 1 < len(args):
                topic = args[idx + 1]
        from pipeline import run
        log.info(f"Manual run — topic: {topic or 'auto'}")
        job = run(manual_topic=topic)
        print(f"\nResult:  {job['status']}")
        if job.get("video_url"): print(f"Video:   {job['video_url']}")
        if job.get("error"):     print(f"Error:   {job['error']}")
        return

    # ── Dashboard only ────────────────────────────────────────
    if "--dashboard" in args:
        from dashboard.app import start_dashboard
        log.info(f"Dashboard only → http://0.0.0.0:{config.PORT}")
        start_dashboard(background=False)
        return

    # ── Weekly strategy ───────────────────────────────────────
    if "--strategy" in args:
        from agents.strategy_agent import generate_weekly_strategy
        generate_weekly_strategy()
        return

    # ── Analytics ─────────────────────────────────────────────
    if "--analyse" in args:
        from agents.analytics_agent import collect_all_analytics, analyse_and_learn
        collect_all_analytics()
        analyse_and_learn()
        return

    # ── Full 24/7 mode ────────────────────────────────────────
    from dashboard.app import start_dashboard
    start_dashboard(background=True)

    from scheduler.jobs import build_scheduler
    scheduler = build_scheduler(blocking=True)
    log.success(f"Bot live 24/7 — dashboard: http://0.0.0.0:{config.PORT}")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped.")


if __name__ == "__main__":
    main()
