from config import config
from router.provider_manager import BaseProvider, manager
import requests

class PollinationsProvider(BaseProvider):
    name = "pollinations"
    tier = 3
    timeout = 30

    def is_configured(self) -> bool:
        # Pollinations is completely free and requires no API key!
        return True

    def generate(self, prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
        # Uses standard OpenAI format but hosted by pollinations
        url = "https://text.pollinations.ai/openai"
        payload = {
            "model": "mistral" if is_fast else "searchgpt",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.35,
        }
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

manager.register(PollinationsProvider())
