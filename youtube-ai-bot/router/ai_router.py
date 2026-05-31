import time, json
from typing import Dict, Any
from utils.logger import get_logger
from router.provider_manager import manager
from router.health_monitor import monitor
from router.failover_engine import get_best_provider
import utils.check_setup

log = get_logger("AIRouter")

def _is_rate_limit(err: str) -> bool:
    kws = ["429", "rate_limit", "rate limit", "quota", "resource_exhausted", "too many requests"]
    return any(k in err.lower() for k in kws)

def ask(prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
    """Intelligent routing with failover."""
    last_err = None

    # We will try up to 4 different providers before giving up
    attempted = set()

    for attempt in range(4):
        provider_name = get_best_provider()
        if not provider_name:
            # If all are in cooldown, wait and retry
            wait = 10
            for name in manager.providers.keys():
                h = monitor.get_health(name)
                if h.cooldown_until > time.time():
                    w = h.cooldown_until - time.time()
                    if w < wait: wait = w
            log.warning(f"All providers exhausted/cooldown. Waiting {wait:.1f}s...")
            time.sleep(max(1, wait))
            provider_name = get_best_provider()
            if not provider_name:
                continue

        if provider_name in attempted:
            continue

        attempted.add(provider_name)
        provider = manager.providers[provider_name]

        t0 = time.time()
        try:
            log.debug(f"Routing to {provider_name} (tier {provider.tier})...")
            result = provider.generate(prompt, is_fast=is_fast, max_tokens=max_tokens)
            latency = time.time() - t0
            monitor.record_success(provider_name, latency)
            return result
        except Exception as e:
            err_str = str(e)
            is_rl = _is_rate_limit(err_str)
            monitor.record_failure(provider_name, err_str, is_rate_limit=is_rl)
            log.warning(f"{provider_name} failed: {err_str[:60]} -> switching provider")
            last_err = e

    raise RuntimeError(f"All AI providers failed. Last error: {last_err}")

import json, re

def _parse_json(raw: str) -> dict:
    if not raw: return {}
    s = raw.find('{')
    e = raw.rfind('}')
    if s != -1 and e != -1:
        raw = raw[s:e+1]

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Attempt heuristic cleanup
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    # Remove trailing commas
    raw = re.sub(r',\s*}', '}', raw)
    raw = re.sub(r',\s*]', ']', raw)
    return json.loads(raw)

def ask_json(prompt: str, is_fast: bool = False, max_tokens: int = 4096, retries: int = 2) -> dict:
    full_prompt = prompt + "\n\nIMPORTANT: Return STRICT JSON only. No markdown. No code blocks. Must be valid json.loads() input."
    last_err = None
    for attempt in range(retries + 1):
        try:
            raw = ask(full_prompt, is_fast=is_fast, max_tokens=max_tokens)
            return _parse_json(raw)
        except Exception as e:
            last_err = e
            log.warning(f"JSON parse failed (attempt {attempt+1}): {e}")
    raise ValueError(f"AI returned invalid JSON: {last_err}")

def get_status() -> dict:
    active = get_best_provider() or "none"
    healthy = sum(1 for p in manager.providers.keys() if monitor.get_health(p).healthy)
    failed = sum(1 for p in manager.providers.keys() if not monitor.get_health(p).healthy)

    total_calls = sum(monitor.get_health(p).total_calls for p in manager.providers.keys())
    total_success = sum(monitor.get_health(p).total_success for p in manager.providers.keys())
    sr = (total_success / total_calls * 100.0) if total_calls > 0 else 100.0

    return {
        "active_provider": active,
        "healthy_providers": healthy,
        "failed_providers": failed,
        "success_rate": round(sr, 1)
    }
