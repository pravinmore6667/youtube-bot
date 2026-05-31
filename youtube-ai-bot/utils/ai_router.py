"""
utils/ai_router.py — Backward-compat shim.
Delegates to ai_orchestrator for all real work.
"""
from utils.ai_orchestrator import (
    ask, ask_json, get_active_provider, get_provider_status
)
__all__ = ["ask", "ask_json", "get_active_provider", "get_provider_status"]
