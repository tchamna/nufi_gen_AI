import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

import nufi_model as nm


def _parse_port() -> int:
    """Azure App Service sets PORT; local dev can omit it (default 8010)."""
    for key in ("PORT", "WEBSITES_PORT"):
        v = os.environ.get(key)
        if v:
            return int(v)
    return 8010


def _cors_origins() -> list[str]:
    """Comma-separated list, or * for all. Set ALLOWED_ORIGINS in production."""
    raw = os.environ.get("ALLOWED_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


APP_PORT = _parse_port()


class GenerateRequest(BaseModel):
    text: str
    n: int = Field(default=4, ge=2, le=6)
    num_candidates: int = Field(default=5, ge=1, le=12)
    max_tokens: int = Field(default=40, ge=1, le=120)
    temperature: float = Field(default=1.0, ge=0.0, le=3.0)
    match_limit: int = Field(default=8, ge=0, le=20)
    max_sources_per_match: int = Field(default=3, ge=1, le=10)


class SuggestRequest(BaseModel):
    text: str
    n: int = Field(default=4, ge=2, le=6)
    limit: int = Field(default=6, ge=1, le=12)
    example_limit: int = Field(default=2, ge=0, le=5)
    max_sources_per_example: int = Field(default=2, ge=1, le=10)


class KeyboardSuggestRequest(BaseModel):
    text: str
    n: int = Field(default=4, ge=2, le=6)
    limit: int = Field(default=5, ge=1, le=8)


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "data" / "Nufi" / "Nufi_language_model_api.pickle"


def _corpus_sources():
    candidates = [
        BASE_DIR / "corpus_vocabulaire_nufi_test.txt",
        BASE_DIR / "main_file.txt",
        BASE_DIR / "data" / "Nufi" / "conversation_base_nufi.txt",
        BASE_DIR / "data" / "Nufi" / "phrasebooknufi.txt",
    ]
    return [path for path in candidates if path.exists()]


def _model_needs_rebuild(model_path):
    if not model_path.exists():
        return True

    model_mtime = model_path.stat().st_mtime
    for source in _corpus_sources():
        if source.stat().st_mtime > model_mtime:
            return True

    try:
        model = nm.load_model(model_path)
    except Exception:
        return True

    key_lengths = {len(key) for key in model if isinstance(key, tuple)}
    return not key_lengths or min(key_lengths) > 1


def _load_api_model(tokens):
    if _model_needs_rebuild(MODEL_PATH):
        model = nm.build_combined_model(tokens, max_n=5)
        nm.save_model(model, MODEL_PATH)
        return model
    return nm.load_model(MODEL_PATH)


def load_runtime_state():
    global CLEANED, CLEANED_SET, TOKENS, MODEL, SENTENCE_SOURCES
    bundle = nm.load_corpus_bundle(BASE_DIR)
    CLEANED = bundle["cleaned"]
    TOKENS = bundle["tokens"]
    SENTENCE_SOURCES = bundle["sentence_sources"]
    CLEANED_SET = set(CLEANED)
    MODEL = _load_api_model(TOKENS)


@asynccontextmanager
async def lifespan(_app):
    load_runtime_state()
    yield


app = FastAPI(title="Nufi N-gram API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    if not nm.clean_text(req.text):
        raise HTTPException(status_code=400, detail="text is required")

    normalized_text, candidates = nm.generate_candidates(
        MODEL,
        req.text,
        n=req.n,
        known_sentences=CLEANED_SET,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        num_candidates=req.num_candidates,
    )
    matches = nm.find_corpus_matches_with_sources(
        SENTENCE_SOURCES,
        normalized_text,
        limit=req.match_limit,
        max_sources=req.max_sources_per_match,
    )

    return {
        "normalized_text": normalized_text,
        "settings": {
            "n": req.n,
            "num_candidates": req.num_candidates,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "match_limit": req.match_limit,
            "max_sources_per_match": req.max_sources_per_match,
        },
        "primary_candidate": candidates[0] if candidates else None,
        "candidates": candidates,
        "matches": matches,
        "match_count": len(matches),
    }


@app.post("/api/suggest")
def api_suggest(req: SuggestRequest):
    if not nm.clean_text(req.text):
        return {"normalized_text": "", "used_context": 0, "suggestions": []}

    payload = nm.suggest_next_words(MODEL, req.text, n=req.n, limit=req.limit)
    suggestions = []
    for item in payload["suggestions"]:
        query = f"{payload['normalized_text']} {item['word']}".strip()
        suggestions.append(
            {
                "word": item["word"],
                "probability": item["probability"],
                "examples": nm.find_corpus_matches_with_sources(
                    SENTENCE_SOURCES,
                    query,
                    limit=req.example_limit,
                    max_sources=req.max_sources_per_example,
                ),
            }
        )

    return {
        "normalized_text": payload["normalized_text"],
        "used_context": payload["used_context"],
        "suggestions": suggestions,
    }


@app.post("/api/keyboard/suggest")
def api_keyboard_suggest(req: KeyboardSuggestRequest):
    if not nm.clean_text(req.text):
        return {"normalized_text": "", "used_context": 0, "suggestions": []}

    payload = nm.suggest_next_words(MODEL, req.text, n=req.n, limit=req.limit)
    return {
        "normalized_text": payload["normalized_text"],
        "used_context": payload["used_context"],
        "suggestions": [
            {
                "word": item["word"],
                "score": item["probability"],
            }
            for item in payload["suggestions"]
        ],
    }


@app.get("/")
def index():
    html_path = BASE_DIR / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return {"status": "ok", "message": "Put a static/index.html file to serve the frontend."}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=APP_PORT, reload=True)
