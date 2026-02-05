#!/usr/bin/env python3
"""LLM client for Groq API with shared rate limiting."""

import os
import time
import threading
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
    "moonshotai/kimi-k2-instruct-0905": (262144, 16384, 60, 10000),
    "groq/compound": (131072, 8192, 200, 200000),
    # "openai/gpt-oss-20b": (131072, 65536, 1000, 250000),
    # "meta-llama/llama-4-maverick-17b-128e-instruct": (131072, 8192, 1000, 250000),
    # "meta-llama/llama-4-scout-17b-16e-instruct": (131072, 8192, 1000, 250000),
    # "moonshotai/kimi-k2-instruct": (131072, 8192, 60, 10000),
    # "groq/compound-mini": (131072, 8192, 200, 200000),
}
MODELS = list(MODEL_SPECS.keys())



class LLMClient:
    """LLM client with per-key rate limiting."""

    # Class-level storage for per-key cooldowns: {(key_hash, model): expiry_time}
    _cooldowns = {}
    _lock = threading.Lock()

    def __init__(self, **_):
        self.api_keys = [
            v for k, v in sorted(os.environ.items()) if k.startswith("GROQ_API_KEY")
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

    def _key_hash(self):
        """Short hash of current API key for tracking."""
        return self.api_keys[self.key_idx][:12] if self.api_keys else ""

    def _set_cooldown(self, model: str, seconds: float):
        """Set cooldown for current key + model."""
        with self._lock:
            self._cooldowns[(self._key_hash(), model)] = time.time() + seconds

    def _can_request(self, model: str) -> bool:
        """Check if current key can request this model."""
        with self._lock:
            expiry = self._cooldowns.get((self._key_hash(), model), 0)
            return time.time() >= expiry

    def _find_available_model(self) -> str:
        """Find a model available for current key."""
        for m in MODELS:
            if self._can_request(m):
                return m
        return None

    @property
    def current_model(self):
        return self._find_available_model() or MODELS[0]

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

        for attempt in range(20):
            # Try each API key to find one with an available model
            for key_attempt in range(len(self.api_keys)):
                model = self._find_available_model()
                if model:
                    break
                # Rotate to next key
                self.key_idx = (self.key_idx + 1) % len(self.api_keys)
                self._client = self._make_client()
            else:
                # No key has an available model, wait
                print("   ⏳ All keys/models busy. Waiting 10s...")
                time.sleep(10)
                continue

            if key_attempt > 0:
                print(f"   🔄 Using API key {self.key_idx + 1}/{len(self.api_keys)}")

            ctx, max_out, _, _ = MODEL_SPECS[model]
            if tokens > ctx * 0.9:
                self._set_cooldown(model, 60)
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
                return resp.choices[0].message.content, False

            except groq.RateLimitError as e:
                retry = 60.0
                try:
                    retry = (
                        float(e.response.headers.get("retry-after", 60))
                        if e.response
                        else 60
                    )
                except Exception:
                    pass
                print(f"   ⚠️  Rate limit {model}: {min(retry, 120):.0f}s cooldown")
                self._set_cooldown(model, min(retry, 120))

            except groq.APIStatusError as e:
                cd = 300 if e.status_code == 413 else 30
                print(f"   ⚠️  API {e.status_code} {model}")
                self._set_cooldown(model, cd)

            except Exception as e:
                print(f"   ⚠️  Error {model}: {str(e)[:50]}")
                self._set_cooldown(model, 15)

        raise RuntimeError("Exhausted all LLM attempts")


def create_llm_client(**kw) -> LLMClient:
    return LLMClient(**kw)
