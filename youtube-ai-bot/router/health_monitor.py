import json, os, time, threading
from dataclasses import dataclass, asdict

METRICS_FILE = "logs/provider_metrics.log"
HEALTH_FILE = "provider_health.json"

@dataclass
class ProviderHealthData:
    healthy: bool = False
    latency: float = 0.0
    success_rate: float = 100.0
    failures: int = 0
    total_calls: int = 0
    total_success: int = 0
    last_failure_time: float = 0.0
    cooldown_until: float = 0.0

class HealthMonitor:
    def __init__(self):
        self._lock = threading.Lock()
        self.health_data: dict[str, ProviderHealthData] = {}
        os.makedirs("logs", exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(HEALTH_FILE):
            try:
                with open(HEALTH_FILE, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.health_data[k] = ProviderHealthData(**v)
            except Exception:
                pass

    def _save(self):
        with self._lock:
            with open(HEALTH_FILE, "w") as f:
                json.dump({k: asdict(v) for k, v in self.health_data.items()}, f, indent=2)

    def init_provider(self, name: str):
        with self._lock:
            if name not in self.health_data:
                self.health_data[name] = ProviderHealthData()
        self._save()

    def record_success(self, name: str, latency: float):
        with self._lock:
            p = self.health_data.get(name)
            if not p:
                p = ProviderHealthData()
                self.health_data[name] = p
            p.total_calls += 1
            p.total_success += 1
            p.success_rate = (p.total_success / p.total_calls) * 100.0
            p.latency = (p.latency * 0.8) + (latency * 0.2) if p.total_calls > 1 else latency
            p.failures = 0
            p.healthy = True
            p.cooldown_until = 0.0
        self._log_metric(name, latency, True, "")
        self._save()

    def record_failure(self, name: str, error: str, is_rate_limit: bool = False):
        with self._lock:
            p = self.health_data.get(name)
            if not p:
                p = ProviderHealthData()
                self.health_data[name] = p
            p.total_calls += 1
            p.success_rate = (p.total_success / p.total_calls) * 100.0
            p.failures += 1
            p.last_failure_time = time.time()
            if is_rate_limit:
                p.cooldown_until = time.time() + 60.0
            else:
                p.cooldown_until = time.time() + min(300, (2 ** p.failures))

            p.healthy = False
        self._log_metric(name, 0.0, False, error)
        self._save()

    def _log_metric(self, name: str, latency: float, success: bool, error: str):
        try:
            with open(METRICS_FILE, "a") as f:
                ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                status = "SUCCESS" if success else "FAILURE"
                f.write(f"[{ts}] provider={name} latency={latency:.2f}s status={status} error={error}\\n")
        except Exception:
            pass

    def get_health(self, name: str) -> ProviderHealthData:
        with self._lock:
            if name not in self.health_data:
                self.health_data[name] = ProviderHealthData()
        return self.health_data[name]

monitor = HealthMonitor()
