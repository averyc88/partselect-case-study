"""FastAPI app entrypoint. Run with: uvicorn app.main:app --reload --port 8000"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config

app = FastAPI(title="PartSelect Chat Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Liveness check. Reports whether an Anthropic key is configured."""
    return {"status": "ok", "model": config.ANTHROPIC_MODEL, "api_key_set": config.has_api_key()}
