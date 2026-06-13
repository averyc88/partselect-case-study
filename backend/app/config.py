"""Application configuration, loaded from the environment / `.env`."""

import os

from dotenv import load_dotenv

# Load backend/.env once. `.env` is gitignored; see `.env.example`.
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Sonnet 4.6: strong tool-calling, fast/cheap enough for tight tool loops.
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Frontend dev server origins for CORS.
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


def has_api_key() -> bool:
    """True if a real (non-placeholder) Anthropic key is set."""
    return bool(ANTHROPIC_API_KEY) and ANTHROPIC_API_KEY != "your-key-here"
