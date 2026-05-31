from config import config
from router.provider_manager import BaseProvider, manager
from cerebras.cloud.sdk import Cerebras

class CerebrasProvider(BaseProvider):
    name = "cerebras"
    tier = 2
    timeout = 30

    def is_configured(self) -> bool:
        return bool(config.CEREBRAS_API_KEY) and not config.CEREBRAS_API_KEY.startswith("your_")

    def generate(self, prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
        client = Cerebras(api_key=config.CEREBRAS_API_KEY)
        model = "llama3.1-8b" if is_fast else "llama3.1-70b"
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.35,
        )
        return resp.choices[0].message.content.strip()

manager.register(CerebrasProvider())
