#!/usr/bin/env python3
"""LLM client for Groq API with shared rate limiting."""

import os, time, threading
from pathlib import Path

try:
    import groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Load .env
_env = Path(__file__).parent / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# Model specs: context, max_output, rpm, tpm
MODEL_SPECS = {
    "openai/gpt-oss-120b": (131072, 65536, 1000, 250000),
    "openai/gpt-oss-20b": (131072, 65536, 1000, 250000),
    "meta-llama/llama-4-maverick-17b-128e-instruct": (131072, 8192, 1000, 250000),
    "meta-llama/llama-4-scout-17b-16e-instruct": (131072, 8192, 1000, 250000),
    "moonshotai/kimi-k2-instruct-0905": (262144, 16384, 60, 10000),
    "moonshotai/kimi-k2-instruct": (131072, 8192, 60, 10000),
    "groq/compound": (131072, 8192, 200, 200000),
    "groq/compound-mini": (131072, 8192, 200, 200000),
}
MODELS = list(MODEL_SPECS.keys())


class _RateLimiter:
    """Thread-safe singleton rate limiter."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    inst = super().__new__(cls)
                    inst._lock = threading.Lock()
                    inst.history = {m: [] for m in MODELS}
                    inst.cooldowns = {m: 0.0 for m in MODELS}
                    cls._instance = inst
        return cls._instance

    def set_cooldown(self, model: str, seconds: float):
        with self._lock:
            self.cooldowns[model] = time.time() + seconds

    def can_request(self, model: str, tokens: int) -> bool:
        now = time.time()
        if now < self.cooldowns.get(model, 0):
            return False
        spec = MODEL_SPECS.get(model)
        if not spec:
            return True
        ctx, _, rpm, tpm = spec
        with self._lock:
            self.history[model] = [
                (t, c) for t, c in self.history[model] if now - t < 60
            ]
            if len(self.history[model]) >= rpm * 0.8:
                return False
            if sum(c for _, c in self.history[model]) + tokens >= tpm * 0.8:
                return False
        return True

    def record(self, model: str, tokens: int):
        with self._lock:
            self.history[model].append((time.time(), tokens))

    def wait_time(self) -> float:
        now = time.time()
        waits = []
        for m in MODELS:
            cd = self.cooldowns.get(m, 0) - now
            if cd > 0:
                waits.append(cd)
            elif self.history[m]:
                oldest = min(t for t, _ in self.history[m])
                waits.append(max(0, 60 - (now - oldest)))
        return min(waits) if waits else 5.0


_rl = _RateLimiter()


class LLMClient:
    def __init__(self, **_):
        self.api_keys = [
            v for k, v in os.environ.items() if k.startswith("GROQ_API_KEY")
        ]
        if not self.api_keys:
            print("⚠️  No GROQ_API_KEYs found.")
        self.key_idx = 0
        self._client = self._make_client()

    def _make_client(self):
        if GROQ_AVAILABLE and self.api_keys:
            return groq.Groq(
                api_key=self.api_keys[self.key_idx % len(self.api_keys)],
                max_retries=0,
                timeout=90.0,
            )
        return None

    @property
    def current_model(self):
        for m in MODELS:
            if _rl.can_request(m, 0):
                return m
        return MODELS[0]

    @property
    def current_api_key(self):
        k = self.api_keys[self.key_idx] if self.api_keys else None
        return f"{k[:8]}...{k[-4:]}" if k else None

    def call(self, sys_p: str, usr_p: str, temp: float = 0.2) -> tuple[str, bool]:
        if not GROQ_AVAILABLE:
            raise ImportError("pip install groq")
        if not self._client:
            raise RuntimeError("No API keys")

        tokens = len(sys_p + usr_p) // 4

        for _ in range(20):
            model = next((m for m in MODELS if _rl.can_request(m, tokens)), None)
            if not model:
                wait = min(_rl.wait_time(), 30)
                print(f"   ⏳ All models busy. Waiting {wait:.0f}s...")
                time.sleep(wait)
                continue

            ctx, max_out, _, _ = MODEL_SPECS[model]
            if tokens > ctx * 0.9:
                print(f"   ⏭️  {model}: tokens exceed context")
                _rl.set_cooldown(model, 60)
                continue

            try:
                resp = self._client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": sys_p},
                        {"role": "user", "content": usr_p},
                    ],
                    temperature=temp,
                    max_tokens=min(max_out, 8192),
                )
                _rl.record(
                    model, resp.usage.total_tokens if resp.usage else tokens + 500
                )
                return resp.choices[0].message.content, False

            except groq.RateLimitError as e:
                retry = 60.0
                try:
                    retry = (
                        float(e.response.headers.get("retry-after", 60))
                        if e.response
                        else 60
                    )
                except:
                    pass
                print(f"   ⚠️  Rate limit {model}: {min(retry, 120):.0f}s cooldown")
                _rl.set_cooldown(model, min(retry, 120))

            except groq.APIStatusError as e:
                cd = 300 if e.status_code == 413 else 30
                print(f"   ⚠️  API {e.status_code} {model}")
                _rl.set_cooldown(model, cd)

            except Exception as e:
                print(f"   ⚠️  Error {model}: {str(e)[:50]}")
                _rl.set_cooldown(model, 15)

        raise RuntimeError("Exhausted all LLM attempts")


def create_llm_client(**kw) -> LLMClient:
    return LLMClient(**kw)
