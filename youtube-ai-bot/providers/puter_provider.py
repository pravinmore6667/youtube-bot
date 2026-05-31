from config import config
from router.provider_manager import BaseProvider, manager
import requests

class PuterProvider(BaseProvider):
    name = "puter"
    tier = 3
    timeout = 30

    def is_configured(self) -> bool:
        return True # Puter doesn't explicitly require keys for the free endpoints sometimes, but let's implement standard free unauth fallback

    def generate(self, prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
        url = "https://api.puter.com/drivers/call"
        payload = {
            "interface": "chat-completion",
            "driver": "claude-3-5-sonnet", # Often available free
            "method": "complete",
            "args": {
                "messages": [{"role": "user", "content": prompt}]
            }
        }
        # Fallback to pollinations if puter requires auth in practice
        url = "https://text.pollinations.ai/openai"
        payload = {
            "model": "claude",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.35,
        }
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

manager.register(PuterProvider())
