import os
import re
import sys
from contextlib import asynccontextmanager
from datetime import timezone
from email.utils import format_datetime
from io import BytesIO
from pathlib import Path
import unicodedata

BASE_DIR = Path(__file__).resolve().parent

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import requests
import uvicorn
from nufi_bana_classification import normalize_bana_to_standard, normalize_ton_bas
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
from scripts import generate_training_lexical_reports as tlr

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
_AUDIO_CACHE_CONTROL = "public, max-age=2592000, stale-while-revalidate=86400"
_AUDIO_REDIRECT_CACHE_CONTROL = "no-store"
_AUDIO_PRESIGNED_URL_TTL_SECONDS = max(
    1,
    min(604800, int(os.environ.get("AUDIO_PRESIGNED_URL_TTL_SECONDS", "3600"))),
)
_AUDIO_TIMEOUT = (5, 30)
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


class CleanNufiTextRequest(BaseModel):
    text: str = ""


MODEL_PATH = BASE_DIR / "data" / "Nufi" / "Nufi_language_model_api.pickle"
_CLEAN_NUFI_ALLOWED_FILE_EXTENSIONS = {".txt", ".docx"}


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


def _build_audio_redirect_url(audio_filename: str) -> str:
    key = f"{audio_filename}.mp3"
    if _S3_CLIENT is None:
        return _build_audio_s3_url(audio_filename)

    try:
        return _S3_CLIENT.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": key,
                "ResponseCacheControl": _AUDIO_CACHE_CONTROL,
                "ResponseContentType": "audio/mpeg",
            },
            ExpiresIn=_AUDIO_PRESIGNED_URL_TTL_SECONDS,
        )
    except NoCredentialsError:
        return _build_audio_s3_url(audio_filename)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail="audio storage unavailable") from exc


def _audio_redirect_headers() -> dict[str, str]:
    return {"Cache-Control": _AUDIO_REDIRECT_CACHE_CONTROL}


def _audio_response_headers(upstream: requests.Response | None = None) -> dict[str, str]:
    headers = {
        "Cache-Control": _AUDIO_CACHE_CONTROL,
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
        last_modified = upstream.headers.get("Last-Modified")
        if last_modified:
            headers["Last-Modified"] = last_modified
    else:
        headers["Content-Type"] = "audio/mpeg"
    return headers


def _s3_audio_headers(response: dict) -> dict[str, str]:
    headers = {
        "Cache-Control": _AUDIO_CACHE_CONTROL,
        "Accept-Ranges": "bytes",
        "Content-Type": response.get("ContentType", "audio/mpeg"),
    }
    content_length = response.get("ContentLength")
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    etag = response.get("ETag")
    if etag:
        headers["ETag"] = etag
    last_modified = response.get("LastModified")
    if last_modified is not None:
        if last_modified.tzinfo is None:
            last_modified = last_modified.replace(tzinfo=timezone.utc)
        else:
            last_modified = last_modified.astimezone(timezone.utc)
        headers["Last-Modified"] = format_datetime(last_modified, usegmt=True)
    return headers


def _resolve_wordcloud_image_path() -> Path | None:
    candidates = [
        BASE_DIR / "data" / "nufi_wordcloud_real.png",
        BASE_DIR / "data" / "_nufi_wordcloud_real.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _clean_nufi_text(text: str) -> str:
    normalized = nm.normalize_text(text or "")
    normalized = normalize_bana_to_standard(normalized)
    normalized = normalize_ton_bas(normalized)
    return unicodedata.normalize("NFC", normalized)


def _safe_download_stem(filename: str | None) -> str:
    raw_stem = Path(filename or "cleaned").stem or "cleaned"
    normalized = unicodedata.normalize("NFKD", raw_stem).encode("ascii", "ignore").decode("ascii")
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", normalized).strip("._-")
    return sanitized or "cleaned"


def _cleaned_download_name(filename: str | None) -> str:
    return f"{_safe_download_stem(filename)}_clean_nufi.txt"


def _decode_uploaded_text(raw_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="ignore")


def _extract_upload_text(filename: str | None, raw_bytes: bytes) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension in {"", ".txt"}:
        return _decode_uploaded_text(raw_bytes)
    if extension == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise HTTPException(status_code=500, detail="docx support unavailable") from exc

        document = Document(BytesIO(raw_bytes))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    allowed = ", ".join(sorted(_CLEAN_NUFI_ALLOWED_FILE_EXTENSIONS))
    raise HTTPException(status_code=400, detail=f"unsupported file type; use {allowed}")


def _is_not_found_s3_error(exc: Exception) -> bool:
    if not isinstance(exc, ClientError):
        return False
    code = str(exc.response.get("Error", {}).get("Code", ""))
    return code in {"404", "NoSuchKey", "NotFound"}


def load_runtime_state():
    global CLEANED, CLEANED_SET, TOKENS, MODEL, SENTENCE_SOURCES, LEXICAL_STATS
    _startup_log("Loading and cleaning corpus (large files may take a few minutes)...")
    bundle = nm.load_corpus_bundle(BASE_DIR)
    CLEANED = bundle["cleaned"]
    TOKENS = bundle["tokens"]
    SENTENCE_SOURCES = bundle["sentence_sources"]
    CLEANED_SET = set(CLEANED)
    _startup_log(f"Corpus: {len(CLEANED)} sentences, {sum(len(t) for t in TOKENS)} tokens.")
    MODEL = _load_api_model(TOKENS)
    LEXICAL_STATS = tlr.build_lexical_report_data(SENTENCE_SOURCES)
    _startup_log("Ready.")


@asynccontextmanager
async def lifespan(_app):
    load_runtime_state()
    yield


app = FastAPI(title="Nufī N-gram API", lifespan=lifespan)

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


@app.post("/api/clean-nufi/text")
def api_clean_nufi_text(req: CleanNufiTextRequest):
    return {
        "input_text": req.text,
        "cleaned_text": _clean_nufi_text(req.text),
    }


@app.post("/api/clean-nufi/file")
async def api_clean_nufi_file(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    source_text = _extract_upload_text(file.filename, raw_bytes)
    cleaned_text = _clean_nufi_text(source_text)
    headers = {
        "Content-Disposition": f'attachment; filename="{_cleaned_download_name(file.filename)}"',
    }
    return Response(
        content=cleaned_text.encode("utf-8-sig"),
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )


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

    return RedirectResponse(
        url=_build_audio_redirect_url(audio_filename),
        status_code=302,
        headers=_audio_redirect_headers(),
    )


@app.get("/api/stats/lexical")
def api_stats_lexical():
    top_words = []
    for item in LEXICAL_STATS["top_words"]:
        word, count = str(item).split("\t", 1)
        top_words.append({"word": word, "count": int(count)})

    top_alpha_words = []
    for item in LEXICAL_STATS["top_alpha_words"]:
        word, count = str(item).split("\t", 1)
        top_alpha_words.append({"word": word, "count": int(count)})

    preview_words = []
    for item in LEXICAL_STATS["top_alpha_preview"]:
        word, count = str(item).split("\t", 1)
        preview_words.append({"word": word, "count": int(count)})

    return {
        "total_tokens": LEXICAL_STATS["total_tokens"],
        "total_alpha_tokens": LEXICAL_STATS["total_alpha_tokens"],
        "unique_word_count": len(LEXICAL_STATS["unique_words"]),
        "unique_alpha_word_count": len(LEXICAL_STATS["unique_alpha_words"]),
        "wordcloud_image_url": "/api/stats/wordcloud-image",
        "top_words": top_words,
        "top_alpha_words": top_alpha_words,
        "top_alpha_preview": preview_words,
    }


@app.get("/api/stats/wordcloud-image")
def api_stats_wordcloud_image():
    image_path = _resolve_wordcloud_image_path()
    if image_path is None:
        raise HTTPException(status_code=404, detail="word cloud image not found")
    return FileResponse(image_path, media_type="image/png")


@app.get("/")
def index():
    html_path = BASE_DIR / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return {"status": "ok", "message": "Put a static/index.html file to serve the frontend."}


@app.get("/stats")
def stats_page():
    html_path = BASE_DIR / "static" / "stats.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="stats page not found")


@app.get("/clean-nufi")
def clean_nufi_page():
    html_path = BASE_DIR / "static" / "clean-nufi.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="clean nufi page not found")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=APP_PORT, reload=True)
