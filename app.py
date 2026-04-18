import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import requests
import uvicorn
try:
    import boto3
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
    from botocore.exceptions import NoCredentialsError
except ImportError:  # pragma: no cover - optional dependency for local dev fallback
    boto3 = None
    BotoCoreError = Exception
    ClientError = Exception
    NoCredentialsError = Exception
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency for local dev convenience
    load_dotenv = None

import nufi_audio as na
import nufi_model as nm

if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")


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
AUDIO_REGION = os.environ.get("AWS_REGION", "us-east-1").strip() or "us-east-1"
S3_BUCKET_NAME = (
    os.environ.get("S3_BUCKET_NAME", "dictionnaire-nufi-audio").strip()
    or "dictionnaire-nufi-audio"
)
_AUDIO_TIMEOUT = (5, 30)
_AUDIO_CHUNK_SIZE = 64 * 1024
_AUDIO_HTTP = requests.Session()
_AUDIO_HTTP.headers.update({"User-Agent": "nufi-gen-ai-audio-proxy/1.0"})
_S3_CLIENT = boto3.client("s3", region_name=AUDIO_REGION) if boto3 is not None else None


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


def _startup_log(msg: str) -> None:
    """Visible while uvicorn prints 'Waiting for application startup' (corpus/model can take minutes)."""
    print(f"[startup] {msg}", file=sys.stderr, flush=True)


def _load_api_model(tokens):
    if _model_needs_rebuild(MODEL_PATH):
        _startup_log("Rebuilding n-gram model (this can take several minutes)...")
        model = nm.build_combined_model(tokens, max_n=5)
        nm.save_model(model, MODEL_PATH)
        _startup_log("Model saved.")
        return model
    _startup_log("Loading model from pickle...")
    return nm.load_model(MODEL_PATH)


def _resolve_audio_filename(word: str, audio_id: str | None = None) -> str | None:
    trimmed_audio_id = "" if audio_id is None else audio_id.strip()
    if trimmed_audio_id:
        return trimmed_audio_id
    return na.get_audio_filename(word)


def _build_audio_s3_url(audio_filename: str) -> str:
    return na.build_s3_audio_url(
        audio_filename=audio_filename,
        bucket_name=S3_BUCKET_NAME,
        region=AUDIO_REGION,
    )


def _audio_response_headers(upstream: requests.Response | None = None) -> dict[str, str]:
    headers = {
        "Cache-Control": "private, max-age=3600",
        "Accept-Ranges": "bytes",
    }
    if upstream is not None:
        content_type = upstream.headers.get("Content-Type")
        if content_type:
            headers["Content-Type"] = content_type
        content_length = upstream.headers.get("Content-Length")
        if content_length:
            headers["Content-Length"] = content_length
        etag = upstream.headers.get("ETag")
        if etag:
            headers["ETag"] = etag
    else:
        headers["Content-Type"] = "audio/mpeg"
    return headers


def _s3_audio_headers(response: dict) -> dict[str, str]:
    headers = {
        "Cache-Control": "private, max-age=3600",
        "Accept-Ranges": "bytes",
        "Content-Type": response.get("ContentType", "audio/mpeg"),
    }
    content_length = response.get("ContentLength")
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    etag = response.get("ETag")
    if etag:
        headers["ETag"] = etag
    return headers


def _is_not_found_s3_error(exc: Exception) -> bool:
    if not isinstance(exc, ClientError):
        return False
    code = str(exc.response.get("Error", {}).get("Code", ""))
    return code in {"404", "NoSuchKey", "NotFound"}


def load_runtime_state():
    global CLEANED, CLEANED_SET, TOKENS, MODEL, SENTENCE_SOURCES
    _startup_log("Loading and cleaning corpus (large files may take a few minutes)...")
    bundle = nm.load_corpus_bundle(BASE_DIR)
    CLEANED = bundle["cleaned"]
    TOKENS = bundle["tokens"]
    SENTENCE_SOURCES = bundle["sentence_sources"]
    CLEANED_SET = set(CLEANED)
    _startup_log(f"Corpus: {len(CLEANED)} sentences, {sum(len(t) for t in TOKENS)} tokens.")
    MODEL = _load_api_model(TOKENS)
    _startup_log("Ready.")


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

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
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


@app.head("/api/audio/{word:path}")
def api_audio_head(word: str, audio_id: str | None = None):
    audio_filename = _resolve_audio_filename(word, audio_id=audio_id)
    if not audio_filename:
        return Response(status_code=404)

    key = f"{audio_filename}.mp3"
    if _S3_CLIENT is not None:
        try:
            upstream = _S3_CLIENT.head_object(Bucket=S3_BUCKET_NAME, Key=key)
            return Response(status_code=200, headers=_s3_audio_headers(upstream))
        except NoCredentialsError:
            pass
        except ClientError as exc:
            if _is_not_found_s3_error(exc):
                return Response(status_code=404)
            raise HTTPException(status_code=502, detail="audio storage unavailable") from exc
        except BotoCoreError as exc:
            raise HTTPException(status_code=502, detail="audio storage unavailable") from exc

    url = _build_audio_s3_url(audio_filename)
    try:
        upstream = _AUDIO_HTTP.head(url, timeout=_AUDIO_TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"audio storage unavailable: {exc}") from exc

    if upstream.status_code == 404:
        return Response(status_code=404)
    if not upstream.ok:
        raise HTTPException(
            status_code=502,
            detail=f"audio storage returned {upstream.status_code}",
        )

    return Response(status_code=200, headers=_audio_response_headers(upstream))


@app.get("/api/audio/{word:path}")
def api_audio_get(word: str, audio_id: str | None = None):
    audio_filename = _resolve_audio_filename(word, audio_id=audio_id)
    if not audio_filename:
        raise HTTPException(status_code=404, detail="audio not found")

    key = f"{audio_filename}.mp3"
    if _S3_CLIENT is not None:
        try:
            upstream = _S3_CLIENT.get_object(Bucket=S3_BUCKET_NAME, Key=key)

            def stream_audio():
                body = upstream["Body"]
                try:
                    while True:
                        chunk = body.read(_AUDIO_CHUNK_SIZE)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    body.close()

            return StreamingResponse(
                stream_audio(),
                media_type=upstream.get("ContentType", "audio/mpeg"),
                headers=_s3_audio_headers(upstream),
            )
        except NoCredentialsError:
            pass
        except ClientError as exc:
            if _is_not_found_s3_error(exc):
                raise HTTPException(status_code=404, detail="audio file not found") from exc
            raise HTTPException(status_code=502, detail="audio storage unavailable") from exc
        except BotoCoreError as exc:
            raise HTTPException(status_code=502, detail="audio storage unavailable") from exc

    url = _build_audio_s3_url(audio_filename)
    try:
        upstream = _AUDIO_HTTP.get(
            url,
            stream=True,
            timeout=_AUDIO_TIMEOUT,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"audio storage unavailable: {exc}") from exc

    if upstream.status_code == 404:
        upstream.close()
        raise HTTPException(status_code=404, detail="audio file not found")
    if not upstream.ok:
        upstream.close()
        raise HTTPException(
            status_code=502,
            detail=f"audio storage returned {upstream.status_code}",
        )

    def stream_audio():
        try:
            for chunk in upstream.iter_content(chunk_size=_AUDIO_CHUNK_SIZE):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    return StreamingResponse(
        stream_audio(),
        media_type=upstream.headers.get("Content-Type", "audio/mpeg"),
        headers=_audio_response_headers(upstream),
    )


@app.get("/")
def index():
    html_path = BASE_DIR / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return {"status": "ok", "message": "Put a static/index.html file to serve the frontend."}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=APP_PORT, reload=True)
