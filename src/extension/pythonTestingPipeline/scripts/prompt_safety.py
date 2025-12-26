import os
from pathlib import Path

# Load .env
for line in (Path(__file__).parent / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

try:
    import groq
except ImportError:
    groq = None

MODELS = {
    "meta-llama/llama-guard-4-12b": 163840,
    "meta-llama/llama-prompt-guard-2-22m": 512,
    "meta-llama/llama-prompt-guard-2-86m": 512,
    "openai/gpt-oss-safeguard-20b": 128000,
}

HAZARDS = {
    "S1": "Violent Crimes",
    "S2": "Non-Violent Crimes",
    "S3": "Sex Crimes",
    "S4": "Child Exploitation",
    "S5": "Defamation",
    "S6": "Specialized Advice",
    "S7": "Privacy",
    "S8": "IP Violation",
    "S9": "Weapons",
    "S10": "Hate",
    "S11": "Self-Harm",
    "S12": "Sexual Content",
    "S13": "Elections",
    "S14": "Code Abuse",
}


class PromptSafetyChecker:
    def __init__(self, model: str = "meta-llama/llama-guard-4-12b"):
        self.model, self.ctx = model, MODELS.get(model, 163840)
        key = next(
            (v for k, v in os.environ.items() if k.startswith("GROQ_API_KEY")), None
        )
        self._client = groq.Groq(api_key=key, timeout=30.0) if groq and key else None

    def check(self, prompt: str) -> tuple[bool, str]:
        if not self._client:
            return True, "skipped"
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt[: self.ctx * 4]}],
                max_tokens=100,
            )
            result = resp.choices[0].message.content.strip().lower()
            if result.startswith("safe"):
                return True, "safe"
            code = result.split("\n")[1].strip().upper() if "\n" in result else ""
            return False, f"Unsafe: {HAZARDS.get(code, code or 'unknown')}"
        except Exception as e:
            return True, f"error: {e}"
