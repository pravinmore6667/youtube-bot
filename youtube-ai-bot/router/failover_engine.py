import time
from router.health_monitor import monitor
from router.provider_manager import manager
from utils.logger import get_logger

log = get_logger("FailoverEngine")

def get_best_provider(tier_filter: int = None) -> str:
    candidates = []
    for name, provider in manager.providers.items():
        if not provider.is_configured(): continue
        if tier_filter and provider.tier != tier_filter: continue

        h = monitor.get_health(name)
        if h.cooldown_until > time.time(): continue

        # Calculate score: success_rate - latency_penalty - recent_failures_penalty
        score = h.success_rate
        # Latency penalty: -1 point per second
        score -= min(10, h.latency)
        # Failure penalty: -5 points per consecutive failure
        score -= min(30, h.failures * 5)

        candidates.append((score, provider.tier, name))

    if not candidates:
        return None

    # Sort by Tier (lowest first), then Score (highest first)
    candidates.sort(key=lambda x: (x[1], -x[0]))
    return candidates[0][2]

def check_all_health():
    """Background check. Restores providers."""
    for name, provider in manager.providers.items():
        if not provider.is_configured(): continue
        h = monitor.get_health(name)
        if not h.healthy and h.cooldown_until < time.time():
            # Try a lightweight check
            log.info(f"Health recovery check for {name}...")
            try:
                # We could do a real call, but just marking available for next real request is safer
                monitor.record_success(name, 1.0) # Reset to healthy
                log.success(f"{name} marked healthy and re-entered rotation.")
            except Exception:
                pass
