from config import config
from router.provider_manager import BaseProvider, manager
import google.genai as genai

class GeminiProvider(BaseProvider):
    name = "gemini"
    tier = 1
    timeout = 20

    def is_configured(self) -> bool:
        return bool(config.GEMINI_API_KEY) and not config.GEMINI_API_KEY.startswith("your_")

    def generate(self, prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = "gemini-2.0-flash" if is_fast else "gemini-2.5-pro" # or whatever reasoning model

        # Fallback to flash if pro fails/not found. Actually we'll just use flash since it's free tier best.
        model = "gemini-2.0-flash"

        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config={'temperature': 0.35, 'max_output_tokens': max_tokens}
        )
        return resp.text.strip()

manager.register(GeminiProvider())
