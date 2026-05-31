"""
config.py — Central configuration.
All settings can be overridden via .env or the dashboard settings page.
"""
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    _warned = False
    # ── AI Providers (priority order) ────────────────────────
    GROQ_API_KEY        = os.getenv("GROQ_API_KEY",        "")
    GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY",      "")
    CEREBRAS_API_KEY    = os.getenv("CEREBRAS_API_KEY",    "")
    OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY",  "")
    GROK_API_KEY        = os.getenv("GROK_API_KEY",        "")
    SAMBANOVA_API_KEY   = os.getenv("SAMBANOVA_API_KEY",   "")
    NVIDIA_API_KEY      = os.getenv("NVIDIA_API_KEY",      "")
    TOGETHER_API_KEY    = os.getenv("TOGETHER_API_KEY",    "")
    DEEPINFRA_API_KEY   = os.getenv("DEEPINFRA_API_KEY",   "")
    POLLINATIONS_ENABLED = os.getenv("POLLINATIONS_ENABLED", "true").lower() == "true"
    PUTER_ENABLED        = os.getenv("PUTER_ENABLED",        "true").lower() == "true"
    AI_HORDE_ENABLED     = os.getenv("AI_HORDE_ENABLED",     "true").lower() == "true"


    # ── Media APIs ────────────────────────────────────────────
    PEXELS_API_KEY      = os.getenv("PEXELS_API_KEY",      "")
    PIXABAY_API_KEY     = os.getenv("PIXABAY_API_KEY",     "")

    # ── YouTube ───────────────────────────────────────────────
    YOUTUBE_CLIENT_ID      = os.getenv("YOUTUBE_CLIENT_ID",     "")
    YOUTUBE_CLIENT_SECRET  = os.getenv("YOUTUBE_CLIENT_SECRET",  "")
    YOUTUBE_REFRESH_TOKEN  = os.getenv("YOUTUBE_REFRESH_TOKEN",  "")

    # ── Channel ───────────────────────────────────────────────
    CHANNEL_NICHE     = os.getenv("CHANNEL_NICHE",    "technology")
    CHANNEL_NAME      = os.getenv("CHANNEL_NAME",     "AI Channel")
    CHANNEL_LANGUAGE  = os.getenv("CHANNEL_LANGUAGE", "en")
    CHANNEL_TONE      = os.getenv("CHANNEL_TONE",     "engaging and informative")
    TARGET_AUDIENCE   = os.getenv("TARGET_AUDIENCE",  "general audience")

    # ── Script settings ───────────────────────────────────────
    TARGET_WORD_COUNT_MIN = int(os.getenv("TARGET_WORD_COUNT_MIN", "800"))
    TARGET_WORD_COUNT_MAX = int(os.getenv("TARGET_WORD_COUNT_MAX", "1200"))
    TARGET_DURATION_MIN   = int(os.getenv("TARGET_DURATION_MIN",   "5"))
    TARGET_DURATION_MAX   = int(os.getenv("TARGET_DURATION_MAX",   "7"))

    # ── Provider settings ─────────────────────────────────────
    PROVIDER_ORDER      = os.getenv("PROVIDER_ORDER",   "gemini,grok,cerebras,sambanova,nvidia,together,deepinfra,openrouter")
    MAX_RETRIES         = int(os.getenv("MAX_RETRIES",   "3"))
    RETRY_DELAY_SEC     = float(os.getenv("RETRY_DELAY",  "2"))

    # ── Caching ───────────────────────────────────────────────
    CACHE_ENABLED       = os.getenv("CACHE_ENABLED",    "true").lower() == "true"
    CACHE_TTL_DAYS      = int(os.getenv("CACHE_TTL_DAYS",  "7"))
    CACHE_SIMILARITY_THRESHOLD = float(os.getenv("CACHE_SIMILARITY", "0.65"))

    # ── Voice ─────────────────────────────────────────────────
    TTS_VOICE_EN_MALE   = os.getenv("TTS_VOICE_EN_MALE",   "en-US-GuyNeural")
    TTS_VOICE_EN_FEMALE = os.getenv("TTS_VOICE_EN_FEMALE", "en-US-JennyNeural")
    TTS_VOICE_HI_MALE   = os.getenv("TTS_VOICE_HI_MALE",   "hi-IN-MadhurNeural")
    TTS_VOICE_HI_FEMALE = os.getenv("TTS_VOICE_HI_FEMALE", "hi-IN-SwaraNeural")
    TTS_VOICE_GENDER    = os.getenv("TTS_VOICE_GENDER",    "male")
    TTS_RATE            = os.getenv("TTS_RATE",    "+5%")
    TTS_VOLUME          = os.getenv("TTS_VOLUME",  "+0%")
    TTS_PITCH           = os.getenv("TTS_PITCH",   "+0Hz")

    @classmethod
    def get_tts_voice(cls):
        lang   = cls.CHANNEL_LANGUAGE.lower()
        gender = cls.TTS_VOICE_GENDER.lower()
        if lang == "hi":
            return cls.TTS_VOICE_HI_MALE if gender == "male" else cls.TTS_VOICE_HI_FEMALE
        return cls.TTS_VOICE_EN_MALE if gender == "male" else cls.TTS_VOICE_EN_FEMALE

    # ── Schedule ──────────────────────────────────────────────
    UPLOAD_HOUR    = int(os.getenv("UPLOAD_HOUR",    "10"))
    UPLOAD_MINUTE  = int(os.getenv("UPLOAD_MINUTE",  "0"))
    VIDEOS_PER_DAY = int(os.getenv("VIDEOS_PER_DAY", "1"))

    # ── Video ─────────────────────────────────────────────────
    VIDEO_WIDTH         = int(os.getenv("VIDEO_WIDTH",         "1920"))
    VIDEO_HEIGHT        = int(os.getenv("VIDEO_HEIGHT",        "1080"))
    VIDEO_FPS           = int(os.getenv("VIDEO_FPS",           "30"))
    ENABLE_MUSIC        = os.getenv("ENABLE_MUSIC",        "true").lower() == "true"
    MUSIC_VOLUME        = float(os.getenv("MUSIC_VOLUME",      "0.12"))
    ENABLE_ZOOM_EFFECTS = os.getenv("ENABLE_ZOOM_EFFECTS", "true").lower() == "true"
    MAX_WORKERS         = int(os.getenv("MAX_WORKERS",         "4"))

    # ── Paths ─────────────────────────────────────────────────
    OUTPUT_VIDEO     = "output/videos"
    OUTPUT_AUDIO     = "output/audio"
    OUTPUT_THUMBNAIL = "output/thumbnails"
    OUTPUT_CAPTIONS  = "output/captions"
    OUTPUT_MUSIC     = "output/music"
    LOGS_DIR         = "logs"
    DB_PATH          = "database/bot.db"

    # ── Dashboard ─────────────────────────────────────────────
    PORT       = int(os.getenv("PORT",       "5000"))
    SECRET_KEY = os.getenv("SECRET_KEY",  "change_me_in_production")

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


config = Config()


def load_live_config():
    """Load channel settings from DB (set via dashboard)."""
    try:
        from database.db import get_all_settings
        s = get_all_settings()
        if s.get("CHANNEL_NICHE"):         config.CHANNEL_NICHE         = s["CHANNEL_NICHE"]
        if s.get("CHANNEL_NAME"):          config.CHANNEL_NAME          = s["CHANNEL_NAME"]
        if s.get("CHANNEL_LANGUAGE"):      config.CHANNEL_LANGUAGE      = s["CHANNEL_LANGUAGE"]
        if s.get("CHANNEL_TONE"):          config.CHANNEL_TONE          = s["CHANNEL_TONE"]
        if s.get("TARGET_AUDIENCE"):       config.TARGET_AUDIENCE       = s["TARGET_AUDIENCE"]
        if s.get("TTS_VOICE_GENDER"):      config.TTS_VOICE_GENDER      = s["TTS_VOICE_GENDER"]
        if s.get("UPLOAD_HOUR"):           config.UPLOAD_HOUR           = int(s["UPLOAD_HOUR"])
        if s.get("UPLOAD_MINUTE"):         config.UPLOAD_MINUTE         = int(s["UPLOAD_MINUTE"])
        if s.get("ENABLE_MUSIC"):          config.ENABLE_MUSIC          = s["ENABLE_MUSIC"] == "true"
        if s.get("CACHE_ENABLED"):         config.CACHE_ENABLED         = s["CACHE_ENABLED"] == "true"
        if s.get("CACHE_TTL_DAYS"):        config.CACHE_TTL_DAYS        = int(s["CACHE_TTL_DAYS"])
        if s.get("TARGET_WORD_COUNT_MIN"): config.TARGET_WORD_COUNT_MIN = int(s["TARGET_WORD_COUNT_MIN"])
        if s.get("TARGET_WORD_COUNT_MAX"): config.TARGET_WORD_COUNT_MAX = int(s["TARGET_WORD_COUNT_MAX"])
        if s.get("PROVIDER_ORDER"):        config.PROVIDER_ORDER        = s["PROVIDER_ORDER"]
        if s.get("MAX_RETRIES"):           config.MAX_RETRIES           = int(s["MAX_RETRIES"])
        if s.get("LOG_LEVEL"):             config.LOG_LEVEL             = s["LOG_LEVEL"]
    except Exception:
        pass

def check_keys():
    import logging
    if Config._warned: return
    Config._warned = True
    missing = []
    if not Config.GEMINI_API_KEY and not Config.GROQ_API_KEY and not Config.CEREBRAS_API_KEY and not Config.OPENROUTER_API_KEY and not Config.GROK_API_KEY and not Config.SAMBANOVA_API_KEY and not Config.NVIDIA_API_KEY and not Config.TOGETHER_API_KEY and not Config.DEEPINFRA_API_KEY:
        missing.append("At least one AI API KEY (GROQ, GEMINI, etc)")
    if not Config.PEXELS_API_KEY and not Config.PIXABAY_API_KEY:
        missing.append("At least one Media API KEY (PEXELS, PIXABAY)")
    if missing:
        logging.warning("Missing required configuration keys: " + ", ".join(missing))

check_keys()
