# 🤖 YouTube AI Bot v4.0 — Multi-Provider Edition

Automated YouTube channel bot with **1 AI call per video** (was 9+), 4-provider failover, intelligent caching, and a full-featured admin dashboard.

## What's New in v4.0

| Feature | Before | Now |
|---------|--------|-----|
| AI calls/video | 9+ | **1–2** |
| Tokens/video | ~25K | **~7K** |
| Providers | Groq + Gemini | **Groq + Gemini + Cerebras + OpenRouter** |
| Cache | None | **SQLite, 7-day TTL, similarity matching** |
| Content library | None | **FTS5 searchable, cross-project reuse** |
| Continuation | None | **Auto-resume on provider cutoff** |
| Dashboard | Flask (1 page) | **FastAPI (7 pages)** |
| Log rotation | None | **5MB × 3 backups** |
| Script length | 10–13 min | **5–7 min (YouTube sweet spot)** |

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up API keys
```bash
cp .env.example .env
# Edit .env and add your keys
```

**Required (at least one AI provider):**
- [Groq](https://console.groq.com/) — FREE, 14,400 req/day (recommended)
- [Gemini](https://aistudio.google.com/) — FREE, 1,500 req/day
- [Cerebras](https://cloud.cerebras.ai/) — FREE tier
- [OpenRouter](https://openrouter.ai/) — FREE models available

**Required (media):**
- [Pexels](https://www.pexels.com/api/) — FREE
- [Pixabay](https://pixabay.com/api/docs/) — FREE

**Required (upload):**
- YouTube OAuth2 credentials (see step 3)

### 3. YouTube OAuth setup
```bash
python auth_setup.py
```

### 4. Verify everything works
```bash
python main.py --setup-check
```

### 5. Make your first video
```bash
python main.py --run-now --topic "5 AI Tools That Replace Employees in 2025"
```

### 6. Start 24/7 bot
```bash
python main.py
# Dashboard: http://localhost:5000
```

---

## AI Provider Priority

The orchestrator picks the healthiest available provider automatically:

```
1. Groq       → llama-3.3-70b (14,400 req/day, ultra-fast)
2. Gemini     → gemini-2.0-flash (1,500 req/day, fast)
3. Cerebras   → llama3.1-70b (fast inference)
4. OpenRouter → free models (mistral-7b, qwen, llama-3.2)
```

Provider selection uses: `success_rate × 0.5 + speed × 0.3 + priority × 0.2`

---

## Dashboard Pages

| Page | URL | Features |
|------|-----|----------|
| Overview | `/` | Stats, active provider, cache, recent jobs, live logs |
| Providers | `/` → Providers | Health scores, token usage, error rates, cooldowns |
| Jobs & Queue | `/` → Jobs | Start/Stop/Retry, full job history |
| Outputs | `/` → Outputs | All videos with thumbnails, YouTube links |
| Library | `/` → Library | FTS search, reuse stats, content history |
| Live Logs | `/` → Logs | Real-time SSE stream, level filter |
| Settings | `/` → Settings | All settings, API keys, provider order |

---

## Commands

```bash
# Development
python main.py --run-now                      # Make one video (auto topic)
python main.py --run-now --topic "AI Jobs"    # Make one video (set topic)
python main.py --dashboard                    # Dashboard only (no bot)
python main.py --niche finance                # Switch niche

# Maintenance
python main.py --setup-check                  # Verify all API keys
python main.py --cache-stats                  # View cache performance
python main.py --library                      # View content library stats
python main.py --list-voices                  # List available TTS voices
python main.py --strategy                     # Run weekly strategy now
python main.py --analyse                      # Run analytics + learning
python main.py --videos                       # List generated videos

# 24/7 Production
python main.py                                # Full bot: scheduler + dashboard
```

---

## Configuration (via .env or Dashboard)

### AI Provider Settings
```env
PROVIDER_ORDER=groq,gemini,cerebras,openrouter  # priority order
MAX_RETRIES=3                                    # retries per provider
```

### Script Settings
```env
TARGET_WORD_COUNT_MIN=800    # minimum words (5-min video)
TARGET_WORD_COUNT_MAX=1200   # maximum words (7-min video)
```

### Cache Settings
```env
CACHE_ENABLED=true           # enable/disable caching
CACHE_TTL_DAYS=7             # cache expiry
CACHE_SIMILARITY=0.65        # topic similarity threshold (0–1)
```

### Logging
```env
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
```

All settings can also be changed in the Dashboard → Settings page without restarting.

---

## Caching & Content Reuse

### How caching works
1. Each generated output is hashed (topic + type + niche + lang)
2. On the next run for the same topic: returns cached result instantly
3. For similar topics (65%+ keyword overlap): returns partial match
4. Cache entries expire after 7 days (configurable)

### Content Library
All generated scripts, titles, descriptions, and tags are stored in a searchable SQLite FTS5 database.
Future videos can reuse research, facts, and SEO metadata from past runs.

To search the library:
- Via Dashboard → Library page (full text search)
- Via API: `GET /api/library/search?q=your+query`

---

## Smart Continuation

If a provider hits its token or rate limit mid-generation:

```
Without continuation:
  Groq generates 60% → hits limit → Gemini re-generates 100% = 160% cost

With continuation:
  Groq generates 60% → hits limit
  → detect_cutoff() saves progress
  → Gemini receives: "continue from section 3, here's what was generated"
  → Gemini generates remaining 40%
  Total cost = 100%  (saves 37.5%)
```

---

## Supported Niches

`technology` · `finance` · `science` · `history` · `health` · `gaming` · `motivation` · `business` · `documentary` · `news` · `education`

Change niche: `python main.py --niche finance` or via Dashboard → Settings.

---

## Migration from v3.x

1. Backup your database: `cp database/bot.db database/bot.db.bak`
2. Pull new files (or replace with new ZIP)
3. Install new requirements: `pip install -r requirements.txt`
4. Add new env vars to `.env` (see `.env.example` for new keys)
5. Run: `python main.py --setup-check`
6. Two new databases are created automatically:
   - `database/cache.db`
   - `database/content_library.db`
7. Your existing `database/bot.db` is fully compatible — no migration needed

---

## Architecture

```
main.py
  └── pipeline.py
        ├── strategy_agent.py        # Topic selection (no AI)
        ├── unified_agent.py          # ★ 1 AI call = everything
        │     ├── cache.py            # Cache check/store
        │     ├── content_library.py  # Library reuse
        │     └── continuation.py    # Auto-resume on cutoff
        ├── voice_agent.py            # edge-tts (parallel)
        ├── video_agent.py            # MoviePy (parallel)
        ├── thumbnail_agent.py        # Pollinations.ai (parallel)
        └── upload_agent.py           # YouTube Data API

utils/
  ├── ai_orchestrator.py  # Groq → Gemini → Cerebras → OpenRouter
  ├── cache.py            # SQLite key-value cache with TTL
  ├── content_library.py  # FTS5 searchable content store
  ├── continuation.py     # Cross-provider generation resume
  └── logger.py           # 4-level rotating logger

dashboard/
  └── app.py  # FastAPI + Bootstrap 5 (7 pages, SSE, API)
```

---

## License

MIT — Free to use for personal and commercial projects.
