"""Groq AI client with API key rotation for rate limit handling."""

import os
from groq import Groq
from dotenv import load_dotenv
from prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

load_dotenv()

# Load all available API keys
API_KEYS = [
    v for k, v in sorted(os.environ.items()) if k.startswith("GROQ_API_KEY") and v
]
MODEL = "openai/gpt-oss-120b"


def generate_memorization_guide(content: str) -> str:
    """Generate memorization guide using Groq AI with key rotation."""
    if not API_KEYS:
        raise ValueError("No GROQ_API_KEY found in environment")

    last_error = None
    for key in API_KEYS:
        try:
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": USER_PROMPT_TEMPLATE.format(content=content),
                    },
                ],
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            if "rate_limit" in str(e).lower():
                continue  # Try next key
            raise

    raise last_error or Exception("All API keys exhausted")
