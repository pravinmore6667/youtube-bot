from config import config
from router.provider_manager import BaseProvider, manager
from groq import Groq

class GroqProvider(BaseProvider):
    name = "groq"
    tier = 1
    timeout = 10

    def is_configured(self) -> bool:
        return bool(config.GROQ_API_KEY) and not config.GROQ_API_KEY.startswith("your_")

    def generate(self, prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
        client = Groq(api_key=config.GROQ_API_KEY, timeout=self.timeout)
        model = "llama-3.1-8b-instant" if is_fast else "llama-3.3-70b-versatile"
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.35,
        )
        return resp.choices[0].message.content.strip()

manager.register(GroqProvider())
