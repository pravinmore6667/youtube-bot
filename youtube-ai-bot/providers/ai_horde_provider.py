from config import config
from router.provider_manager import BaseProvider, manager
import requests, time

class AIHordeProvider(BaseProvider):
    name = "ai_horde"
    tier = 4
    timeout = 120 # Horde is slow, needs longer timeout

    def is_configured(self) -> bool:
        return True # Anonymous mode

    def generate(self, prompt: str, is_fast: bool = False, max_tokens: int = 4096) -> str:
        # Submit task
        submit_url = "https://aihorde.net/api/v2/generate/text/async"
        headers = {"apikey": "0000000000"} # Anonymous
        payload = {
            "prompt": prompt,
            "params": {"max_context_length": max_tokens, "temperature": 0.35}
        }
        r = requests.post(submit_url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        task_id = r.json().get("id")
        if not task_id: raise RuntimeError("Horde failed to give task ID")

        # Poll for result
        check_url = f"https://aihorde.net/api/v2/generate/text/status/{task_id}"
        t0 = time.time()
        while time.time() - t0 < self.timeout:
            time.sleep(5)
            r = requests.get(check_url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("done"):
                    generations = data.get("generations", [])
                    if generations:
                        return generations[0].get("text", "").strip()
                    break
        raise RuntimeError("AI Horde timed out or returned empty")

manager.register(AIHordeProvider())
