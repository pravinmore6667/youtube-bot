from config import config
from router.provider_manager import BaseProvider, manager
import openai

class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    tier = 2
    timeout = 20

    def is_configured(self) -> bool:
        return bool(config.OPENROUTER_API_KEY) and not config.OPENROUTER_API_KEY.startswith("your_")

    def generate(self, prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
        client = openai.OpenAI(api_key=config.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        models = [
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "qwen/qwen-2.5-7b-instruct:free"
        ]
        model = models[0]

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.35,
        )
        return resp.choices[0].message.content.strip()

manager.register(OpenRouterProvider())
