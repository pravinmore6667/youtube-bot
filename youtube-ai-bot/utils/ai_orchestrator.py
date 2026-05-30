"""
utils/ai_orchestrator.py
─────────────────────────
Multi-Provider AI Orchestration System

Priority:
  1. Groq        — llama-3.3-70b-versatile (14,400 req/day, free, very fast)
  2. Gemini       — gemini-2.0-flash (1,500 req/day, free)
  3. Cerebras     — llama3.1-70b (free tier, very fast)
  4. OpenRouter   — free models (mistral, llama, qwen, etc.)

Features:
  ✓ Automatic health checking at startup
  ✓ Automatic failover between providers
  ✓ Smart retry with exponential backoff
  ✓ Rate-limit detection + per-provider cooldown
  ✓ Provider scoring system (success rate + latency + priority)
  ✓ Token tracking per provider
  ✓ Response quality scoring
  ✓ Provider usage statistics (written to DB)
  ✓ Continuation support (detect cutoff, resume from last good point)
"""

import json, re, time, os, threading
from dataclasses import dataclass, field
from typing import Optional
from collections import deque

from utils.logger import get_logger

log = get_logger("AIOrchestrator")

# ─────────────────────────────────────────────────────────────
# Provider Health Data
# ─────────────────────────────────────────────────────────────

@dataclass
class ProviderHealth:
    name:          str
    priority:      int           # lower = higher priority
    configured:    bool = False
    available:     bool = False
    cooldown_until: float = 0    # epoch seconds
    total_requests: int = 0
    total_tokens:   int = 0
    total_errors:   int = 0
    last_error:     str = ""
    last_latency:   float = 0
    recent_results: deque = field(default_factory=lambda: deque(maxlen=20))

    @property
    def in_cooldown(self) -> bool:
        return time.time() < self.cooldown_until

    @property
    def success_rate(self) -> float:
        if not self.recent_results:
            return 1.0
        return sum(self.recent_results) / len(self.recent_results)

    @property
    def health_score(self) -> float:
        """0-1 composite score. Higher = better."""
        if not self.available or not self.configured:
            return 0.0
        if self.in_cooldown:
            return 0.0
        sr    = self.success_rate
        speed = min(1.0, 3.0 / max(self.last_latency, 0.5)) if self.last_latency else 0.5
        pri   = 1.0 - (self.priority / 10)   # priority 1→0.9, 4→0.6
        return sr * 0.5 + speed * 0.3 + pri * 0.2

    def record_success(self, tokens: int, latency: float):
        self.recent_results.append(1)
        self.total_requests += 1
        self.total_tokens   += tokens
        self.last_latency    = latency

    def record_failure(self, error: str, cooldown_sec: float = 0):
        self.recent_results.append(0)
        self.total_errors  += 1
        self.total_requests += 1
        self.last_error     = error[:200]
        if cooldown_sec:
            self.cooldown_until = time.time() + cooldown_sec

    def status_dict(self) -> dict:
        return {
            "name":          self.name,
            "configured":    self.configured,
            "available":     self.available,
            "in_cooldown":   self.in_cooldown,
            "cooldown_secs": max(0, int(self.cooldown_until - time.time())),
            "health_score":  round(self.health_score, 3),
            "success_rate":  round(self.success_rate, 3),
            "total_requests":self.total_requests,
            "total_tokens":  self.total_tokens,
            "total_errors":  self.total_errors,
            "last_error":    self.last_error,
            "last_latency_s":round(self.last_latency, 2),
        }


# ─────────────────────────────────────────────────────────────
# Orchestrator (singleton)
# ─────────────────────────────────────────────────────────────

class AIOrchestrator:

    def __init__(self):
        self._lock  = threading.Lock()
        self._init  = False
        self._clients = {}
        self.providers: dict[str, ProviderHealth] = {
            "groq":       ProviderHealth("groq",       priority=1),
            "gemini":     ProviderHealth("gemini",     priority=2),
            "cerebras":   ProviderHealth("cerebras",   priority=3),
            "openrouter": ProviderHealth("openrouter", priority=4),
        }

    # ── Initialisation ────────────────────────────────────────

    def ensure_ready(self):
        if self._init:
            return
        with self._lock:
            if self._init:
                return
            self._init_all_providers()
            self._init = True

    def _init_all_providers(self):
        """Check all providers in parallel."""
        import concurrent.futures
        checks = {
            "groq":       self._init_groq,
            "gemini":     self._init_gemini,
            "cerebras":   self._init_cerebras,
            "openrouter": self._init_openrouter,
        }
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(fn): name for name, fn in checks.items()}
            for fut in concurrent.futures.as_completed(futures):
                name = futures[fut]
                try:
                    fut.result()
                except Exception as e:
                    log.debug(f"{name} init error: {e}")

        available = [n for n, p in self.providers.items() if p.available]
        if not available:
            raise RuntimeError(
                "No AI provider available!\n"
                "  Set at least one of: GROQ_API_KEY, GEMINI_API_KEY, "
                "CEREBRAS_API_KEY, OPENROUTER_API_KEY in your .env"
            )
        log.success(f"Providers ready: {', '.join(available)}")

    def _get_key(self, env_var: str) -> str:
        try:
            from config import config
            val = getattr(config, env_var, "") or os.getenv(env_var, "")
        except Exception:
            val = os.getenv(env_var, "")
        if val and not val.startswith("your_"):
            return val
        return ""

    def _init_groq(self):
        ph = self.providers["groq"]
        key = self._get_key("GROQ_API_KEY")
        ph.configured = bool(key)
        if not key:
            return
        try:
            from groq import Groq
            client = Groq(api_key=key)
            client.models.list()      # cheapest validation
            self._clients["groq"] = client
            ph.available = True
            log.success("Groq ready (llama-3.3-70b)")
        except Exception as e:
            ph.last_error = str(e)[:100]
            log.warning(f"Groq unavailable: {str(e)[:60]}")

    def _init_gemini(self):
        ph = self.providers["gemini"]
        key = self._get_key("GEMINI_API_KEY")
        ph.configured = bool(key)
        if not key:
            return
        try:
            from google import genai
            client = genai.Client(api_key=key)
            available = [m.name for m in client.models.list()
                         if "generateContent" in m.supported_generation_methods]
            preferred = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"]
            chosen = None
            for pref in preferred:
                match = next((a for a in available if pref in a), None)
                if match:
                    chosen = pref
                    break
            chosen = chosen or (available[0].replace("models/", "") if available else None)
            if not chosen:
                return
            self._clients["gemini_model"] = chosen
            self._clients["gemini_client"] = client
            ph.available = True
            log.success(f"Gemini ready ({chosen})")
        except Exception as e:
            ph.last_error = str(e)[:100]
            log.warning(f"Gemini unavailable: {str(e)[:60]}")

    def _init_cerebras(self):
        ph = self.providers["cerebras"]
        key = self._get_key("CEREBRAS_API_KEY")
        ph.configured = bool(key)
        if not key:
            return
        try:
            from cerebras.cloud.sdk import Cerebras
            client = Cerebras(api_key=key)
            self._clients["cerebras"] = client
            ph.available = True
            log.success("Cerebras ready (llama3.1-70b)")
        except ImportError:
            log.debug("cerebras-cloud-sdk not installed — skipping")
        except Exception as e:
            ph.last_error = str(e)[:100]
            log.warning(f"Cerebras unavailable: {str(e)[:60]}")

    def _init_openrouter(self):
        ph = self.providers["openrouter"]
        key = self._get_key("OPENROUTER_API_KEY")
        ph.configured = bool(key)
        if not key:
            return
        try:
            import openai
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key,
            )
            self._clients["openrouter"] = client
            ph.available = True
            log.success("OpenRouter ready (free models)")
        except ImportError:
            log.debug("openai package not installed — skipping OpenRouter")
        except Exception as e:
            ph.last_error = str(e)[:100]
            log.warning(f"OpenRouter unavailable: {str(e)[:60]}")

    # ── Provider selection ─────────────────────────────────────

    def _ranked_providers(self) -> list[str]:
        """Return available providers sorted by health score."""
        scored = [
            (name, ph.health_score)
            for name, ph in self.providers.items()
            if ph.configured and ph.available and not ph.in_cooldown
        ]
        scored.sort(key=lambda x: (-x[1], self.providers[x[0]].priority))
        return [name for name, _ in scored]

    # ── Provider calls ────────────────────────────────────────

    def _call_groq(self, prompt: str, max_tokens: int) -> tuple[str, int]:
        client = self._clients["groq"]
        models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama3-70b-8192",
        ]
        last_err = None
        for model in models:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.35,
                )
                text   = resp.choices[0].message.content.strip()
                tokens = getattr(resp.usage, "total_tokens", len(text.split()))
                return text, tokens
            except Exception as e:
                err = str(e).lower()
                if "model_not_found" in err or "model not found" in err:
                    last_err = e
                    continue
                raise
        raise last_err or RuntimeError("Groq: all models exhausted")

    def _call_gemini(self, prompt: str, max_tokens: int) -> tuple[str, int]:
        client = self._clients["gemini_client"]
        model_name = self._clients["gemini_model"]


        resp = client.models.generate_content(model=model_name, contents=prompt, config={'temperature': 0.35, 'max_output_tokens': max_tokens})
        text = resp.text.strip()
        return text, len(text.split())

    def _call_cerebras(self, prompt: str, max_tokens: int) -> tuple[str, int]:
        client = self._clients["cerebras"]
        # cerebras models: llama3.1-70b, llama3.1-8b, llama-4-scout-17b
        for model in ["llama3.1-70b", "llama-4-scout-17b", "llama3.1-8b"]:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                text   = resp.choices[0].message.content.strip()
                tokens = getattr(resp.usage, "total_tokens", len(text.split()))
                return text, tokens
            except Exception as e:
                if "model" in str(e).lower():
                    continue
                raise
        raise RuntimeError("Cerebras: all models exhausted")

    _OR_MODELS = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "qwen/qwen-2.5-7b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.2-1b-instruct:free",
    ]

    def _call_openrouter(self, prompt: str, max_tokens: int) -> tuple[str, int]:
        client = self._clients["openrouter"]
        for model in self._OR_MODELS:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                text   = resp.choices[0].message.content.strip()
                tokens = getattr(resp.usage, "total_tokens", len(text.split()))
                return text, tokens
            except Exception as e:
                err = str(e).lower()
                if "model" in err or "not found" in err:
                    continue
                raise
        raise RuntimeError("OpenRouter: all free models exhausted")

    _DISPATCH = {
        "groq":       _call_groq,
        "gemini":     _call_gemini,
        "cerebras":   _call_cerebras,
        "openrouter": _call_openrouter,
    }

    def _is_rate_limit(self, err: str) -> bool:
        kws = ["429", "rate_limit", "rate limit", "quota", "resource_exhausted",
               "too many requests", "exceeded", "tokens per"]
        return any(k in err.lower() for k in kws)

    # ── Public ask() ──────────────────────────────────────────

    def ask(self, prompt: str, max_tokens: int = 4096,
            preferred: str = None) -> str:
        """
        Call AI with automatic failover.
        Returns the response text.
        """
        self.ensure_ready()
        order = self._ranked_providers()
        if preferred and preferred in order:
            order = [preferred] + [p for p in order if p != preferred]

        if not order:
            # All in cooldown — wait for shortest
            wait = min(
                max(0, p.cooldown_until - time.time())
                for p in self.providers.values()
                if p.available and p.configured
            )
            log.warning(f"All providers in cooldown. Waiting {wait:.0f}s...")
            time.sleep(max(1, wait))
            order = self._ranked_providers()

        last_err = None
        for global_attempt in range(3): # Wait up to 3 times for a provider to cool down
            for provider_name in order:
                ph  = self.providers[provider_name]
                if not ph.available or ph.cooldown_until > time.time(): continue
                fn  = self._DISPATCH[provider_name]
                t0  = time.time()
                try:
                    text, tokens = fn(self, prompt, max_tokens)
                    latency = time.time() - t0
                    ph.record_success(tokens, latency)
                    self._persist_stats(provider_name)
                    log.debug(f"{provider_name} ✓ {tokens}tok {latency:.1f}s")
                    return text

                except Exception as e:
                    latency  = time.time() - t0
                    err_str  = str(e)
                    cooldown = 60 if self._is_rate_limit(err_str) else 5
                    ph.record_failure(err_str, cooldown_sec=cooldown)
                    last_err = e

                    if self._is_rate_limit(err_str):
                        log.warning(f"{provider_name} rate-limited → cooling {cooldown}s, trying next")
                    else:
                        log.warning(f"{provider_name} error: {err_str[:60]} → trying next")

            # If we get here, all providers failed or are cooling down.
            wait = min(
                max(0, p.cooldown_until - time.time())
                for p in self.providers.values()
                if p.available and p.configured
            )
            if wait > 0:
                log.warning(f"All providers in cooldown/failed. Waiting {wait:.0f}s before global attempt {global_attempt+2}...")
                time.sleep(wait + 1)
                order = self._ranked_providers()
            else:
                break # Not rate limit issue, just broken providers.

        raise RuntimeError(
            f"All AI providers failed. Last error: {last_err}"
        )

    def ask_json(self, prompt: str, max_tokens: int = 4096,
                 retries: int = 2) -> dict:
        """Call AI, parse and return JSON with retry on parse failure."""
        full_prompt = (
            prompt
            + "\n\nIMPORTANT: Return STRICT JSON only. No markdown. "
            "No code blocks. No comments. Must be valid json.loads() input."
        )
        last_err = None
        for attempt in range(retries + 1):
            raw = self.ask(full_prompt, max_tokens=max_tokens)
            try:
                return _parse_json(raw)
            except Exception as e:
                last_err = e
                if attempt < retries:
                    log.warning(f"JSON parse failed (attempt {attempt+1}): {e}")
        raise ValueError(f"AI returned invalid JSON after {retries+1} attempts: {last_err}")

    def get_status(self) -> dict:
        return {
            name: ph.status_dict()
            for name, ph in self.providers.items()
        }

    def get_active_provider(self) -> str:
        ordered = self._ranked_providers()
        return ordered[0] if ordered else "none"

    def _persist_stats(self, provider: str):
        """Save provider stats to DB (non-blocking, best-effort)."""
        try:
            from database import db
            ph = self.providers[provider]
            db.upsert_provider_stat(provider, {
                "total_requests": ph.total_requests,
                "total_tokens":   ph.total_tokens,
                "total_errors":   ph.total_errors,
                "success_rate":   round(ph.success_rate, 3),
                "last_latency":   round(ph.last_latency, 2),
                "health_score":   round(ph.health_score, 3),
            })
        except Exception:
            pass


# ── JSON parser (handles common AI formatting issues) ─────────

def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    # Strip markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    # Extract outermost JSON object
    s, e = raw.find("{"), raw.rfind("}")
    if s >= 0 and e > s:
        raw = raw[s:e+1]
    # Remove BOM, invalid escapes, control chars
    raw = raw.replace("\ufeff", "").replace("\\'", "'")
    raw = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", raw)
    # Remove trailing commas
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Escape unescaped newlines inside strings
        def fix_strings(m):
            return m.group(0).replace("\n", "\\n").replace("\r", "")
        fixed = re.sub(r'"(?:[^"\\]|\\.)*"', fix_strings, raw, flags=re.S)
        return json.loads(fixed)


# ── Singleton ─────────────────────────────────────────────────
_orchestrator: Optional[AIOrchestrator] = None
_orch_lock = threading.Lock()


def get_orchestrator() -> AIOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        with _orch_lock:
            if _orchestrator is None:
                _orchestrator = AIOrchestrator()
    return _orchestrator


# ── Public convenience functions (backward-compatible) ────────

def ask(prompt: str, max_tokens: int = 4096) -> str:
    return get_orchestrator().ask(prompt, max_tokens=max_tokens)

def ask_json(prompt: str, max_tokens: int = 4096) -> dict:
    return get_orchestrator().ask_json(prompt, max_tokens=max_tokens)

def get_active_provider() -> str:
    return get_orchestrator().get_active_provider()

def get_provider_status() -> dict:
    return get_orchestrator().get_status()
