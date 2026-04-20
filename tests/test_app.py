from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi.testclient import TestClient
from docx import Document

import app
import nufi_model as nm


AUDIO_ROUTE_WORD = "/api/audio/m\u0251\u0301 k\u0251\u0301 l\u012b"


def test_generate_endpoint_returns_candidates_matches_and_sources(monkeypatch):
    cleaned = [
        "hello world",
        "hello there",
        "greetings friend",
    ]
    tokens = [sentence.split() for sentence in cleaned]
    model = nm.build_combined_model(tokens, max_n=3)
    sentence_sources = {
        "hello world": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
        "hello there": [{"path": "a.txt", "type": "txt", "reference": "line 2"}],
        "greetings friend": [{"path": "b.txt", "type": "txt", "reference": "line 1"}],
    }

    monkeypatch.setattr(
        app.nm,
        "load_corpus_bundle",
        lambda base_dir: {"cleaned": cleaned, "tokens": tokens, "sentence_sources": sentence_sources},
    )
    monkeypatch.setattr(app, "_load_api_model", lambda loaded_tokens: model)

    with TestClient(app.app) as client:
        response = client.post(
            "/api/generate",
            json={
                "text": "hello",
                "n": 3,
                "num_candidates": 3,
                "max_tokens": 4,
                "temperature": 0,
                "match_limit": 5,
                "max_sources_per_match": 2,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_text"] == "hello"
    assert payload["primary_candidate"]["status"] == "original"
    assert payload["candidates"]
    assert payload["matches"][0]["sources"][0]["path"] == "a.txt"
    assert payload["settings"]["num_candidates"] == 3


def test_suggest_endpoint_returns_ranked_suggestions(monkeypatch):
    cleaned = ["hello world", "hello there"]
    tokens = [sentence.split() for sentence in cleaned]
    model = nm.build_combined_model(tokens, max_n=3)
    sentence_sources = {
        "hello world": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
        "hello there": [{"path": "a.txt", "type": "txt", "reference": "line 2"}],
    }

    monkeypatch.setattr(
        app.nm,
        "load_corpus_bundle",
        lambda base_dir: {"cleaned": cleaned, "tokens": tokens, "sentence_sources": sentence_sources},
    )
    monkeypatch.setattr(app, "_load_api_model", lambda loaded_tokens: model)

    with TestClient(app.app) as client:
        response = client.post("/api/suggest", json={"text": "hello", "n": 3, "limit": 2, "example_limit": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_text"] == "hello"
    assert payload["suggestions"][0]["word"] in {"world", "there"}
    assert "examples" in payload["suggestions"][0]


def test_keyboard_suggest_endpoint_returns_compact_suggestions(monkeypatch):
    cleaned = ["hello world", "hello there"]
    tokens = [sentence.split() for sentence in cleaned]
    model = nm.build_combined_model(tokens, max_n=3)
    sentence_sources = {
        "hello world": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
        "hello there": [{"path": "a.txt", "type": "txt", "reference": "line 2"}],
    }

    monkeypatch.setattr(
        app.nm,
        "load_corpus_bundle",
        lambda base_dir: {"cleaned": cleaned, "tokens": tokens, "sentence_sources": sentence_sources},
    )
    monkeypatch.setattr(app, "_load_api_model", lambda loaded_tokens: model)

    with TestClient(app.app) as client:
        response = client.post("/api/keyboard/suggest", json={"text": "hello", "n": 3, "limit": 2})

    assert response.status_code == 200
    payload = response.json()
    assert payload["normalized_text"] == "hello"
    assert payload["suggestions"][0]["word"] in {"world", "there"}
    assert "score" in payload["suggestions"][0]
    assert "examples" not in payload["suggestions"][0]


def test_generate_endpoint_requires_text(monkeypatch):
    cleaned = ["hello world"]
    tokens = [sentence.split() for sentence in cleaned]
    model = nm.build_combined_model(tokens, max_n=3)

    monkeypatch.setattr(
        app.nm,
        "load_corpus_bundle",
        lambda base_dir: {"cleaned": cleaned, "tokens": tokens, "sentence_sources": {"hello world": []}},
    )
    monkeypatch.setattr(app, "_load_api_model", lambda loaded_tokens: model)

    with TestClient(app.app) as client:
        response = client.post("/api/generate", json={"text": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "text is required"


class _FakeAudioResponse:
    def __init__(self, status_code=200, content=b"audio-bytes", headers=None):
        self.status_code = status_code
        self._content = content
        self.headers = headers or {
            "Content-Type": "audio/mpeg",
            "Content-Length": str(len(content)),
        }
        self.ok = 200 <= status_code < 300
        self.closed = False

    def iter_content(self, chunk_size=65536):
        yield self._content

    def close(self):
        self.closed = True


class _FakeAudioHttp:
    def __init__(self, head_response=None):
        self.head_response = head_response or _FakeAudioResponse()

    def head(self, url, timeout=None, allow_redirects=None):
        return self.head_response


class _FakeS3Client:
    def __init__(self, presigned_url="https://signed.example/audio.mp3?sig=1"):
        self.presigned_url = presigned_url
        self.calls = []

    def generate_presigned_url(self, client_method, Params=None, ExpiresIn=None):
        self.calls.append(
            {
                "client_method": client_method,
                "Params": Params,
                "ExpiresIn": ExpiresIn,
            }
        )
        return self.presigned_url


def _stub_runtime(monkeypatch):
    cleaned = ["hello world"]
    tokens = [sentence.split() for sentence in cleaned]
    model = nm.build_combined_model(tokens, max_n=3)
    monkeypatch.setattr(
        app.nm,
        "load_corpus_bundle",
        lambda base_dir: {"cleaned": cleaned, "tokens": tokens, "sentence_sources": {"hello world": []}},
    )
    monkeypatch.setattr(app, "_load_api_model", lambda loaded_tokens: model)


def test_audio_head_endpoint_returns_headers(monkeypatch):
    _stub_runtime(monkeypatch)
    monkeypatch.setattr(app, "_S3_CLIENT", None)
    monkeypatch.setattr(app, "_AUDIO_HTTP", _FakeAudioHttp())
    monkeypatch.setattr(app, "_resolve_audio_filename", lambda word, audio_id=None: "makali")

    with TestClient(app.app) as client:
        response = client.head(AUDIO_ROUTE_WORD)

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["cache-control"] == "public, max-age=2592000, stale-while-revalidate=86400"


def test_audio_get_endpoint_redirects_to_signed_s3_url(monkeypatch):
    _stub_runtime(monkeypatch)
    fake_s3 = _FakeS3Client()
    monkeypatch.setattr(app, "_S3_CLIENT", fake_s3)
    monkeypatch.setattr(app, "_resolve_audio_filename", lambda word, audio_id=None: "makali")

    with TestClient(app.app) as client:
        response = client.get(AUDIO_ROUTE_WORD, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://signed.example/audio.mp3?sig=1"
    assert response.headers["cache-control"] == "no-store"
    assert fake_s3.calls == [
        {
            "client_method": "get_object",
            "Params": {
                "Bucket": app.S3_BUCKET_NAME,
                "Key": "makali.mp3",
                "ResponseCacheControl": "public, max-age=2592000, stale-while-revalidate=86400",
                "ResponseContentType": "audio/mpeg",
            },
            "ExpiresIn": app._AUDIO_PRESIGNED_URL_TTL_SECONDS,
        }
    ]


def test_audio_get_endpoint_redirects_to_public_s3_url_without_s3_client(monkeypatch):
    _stub_runtime(monkeypatch)
    monkeypatch.setattr(app, "_S3_CLIENT", None)
    monkeypatch.setattr(app, "_resolve_audio_filename", lambda word, audio_id=None: "makali")

    with TestClient(app.app) as client:
        response = client.get(AUDIO_ROUTE_WORD, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == (
        "https://dictionnaire-nufi-audio.s3.us-east-1.amazonaws.com/makali.mp3"
    )
    assert response.headers["cache-control"] == "no-store"


def test_audio_get_endpoint_returns_404_when_mapping_missing(monkeypatch):
    _stub_runtime(monkeypatch)
    monkeypatch.setattr(app, "_S3_CLIENT", None)
    monkeypatch.setattr(app, "_resolve_audio_filename", lambda word, audio_id=None: None)

    with TestClient(app.app) as client:
        response = client.get("/api/audio/unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "audio not found"


def test_s3_audio_headers_normalize_last_modified_to_utc():
    headers = app._s3_audio_headers(
        {
            "ContentType": "audio/mpeg",
            "ContentLength": 7,
            "ETag": '"abc123"',
            "LastModified": datetime(2026, 4, 18, 9, 30, tzinfo=timezone(timedelta(hours=-4))),
        }
    )

    assert headers["Cache-Control"] == "public, max-age=2592000, stale-while-revalidate=86400"
    assert headers["Last-Modified"] == "Sat, 18 Apr 2026 13:30:00 GMT"


def test_lexical_stats_endpoint_returns_summary(monkeypatch):
    _stub_runtime(monkeypatch)
    monkeypatch.setattr(
        app.tlr,
        "build_lexical_report_data",
        lambda sentence_sources: {
            "total_tokens": 120,
            "total_alpha_tokens": 100,
            "unique_words": ["mɑ́", "kɑ́"],
            "unique_alpha_words": ["mɑ́", "kɑ́"],
            "top_words": ["mɑ́\t40", "001\t20"],
            "top_alpha_words": ["mɑ́\t40", "kɑ́\t30"],
            "top_alpha_preview": ["mɑ́\t40", "kɑ́\t30"],
        },
    )

    with TestClient(app.app) as client:
        response = client.get("/api/stats/lexical")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_tokens"] == 120
    assert payload["unique_word_count"] == 2
    assert payload["wordcloud_image_url"] == "/api/stats/wordcloud-image"
    assert payload["top_alpha_words"][0] == {"word": "mɑ́", "count": 40}
    assert payload["top_words"][1] == {"word": "001", "count": 20}


def test_stats_page_route_serves_html(monkeypatch):
    _stub_runtime(monkeypatch)

    with TestClient(app.app) as client:
        response = client.get("/stats")

    assert response.status_code == 200
    assert "Word stats" in response.text
    assert "/api/stats/wordcloud-image" in response.text


def test_clean_nufi_text_endpoint_applies_bana_and_ton_bas(monkeypatch):
    _stub_runtime(monkeypatch)

    with TestClient(app.app) as client:
        response = client.post("/api/clean-nufi/text", json={"text": "sì hə̌ʼnzī"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["cleaned_text"] == "si hě'nzī"


def test_clean_nufi_file_endpoint_returns_cleaned_txt_download(monkeypatch):
    _stub_runtime(monkeypatch)

    with TestClient(app.app) as client:
        response = client.post(
            "/api/clean-nufi/file",
            files={"file": ("sample.txt", "sì hə̌ʼnzī".encode("utf-8"), "text/plain")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert 'filename="sample_clean_nufi.txt"' in response.headers["content-disposition"]
    assert response.content.decode("utf-8-sig") == "si hě'nzī"


def test_clean_nufi_file_endpoint_accepts_docx(monkeypatch):
    _stub_runtime(monkeypatch)
    buffer = BytesIO()
    document = Document()
    document.add_paragraph("sì hə̌ʼnzī")
    document.save(buffer)

    with TestClient(app.app) as client:
        response = client.post(
            "/api/clean-nufi/file",
            files={
                "file": (
                    "sample.docx",
                    buffer.getvalue(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert response.status_code == 200
    assert response.content.decode("utf-8-sig") == "si hě'nzī"


def test_clean_nufi_page_route_serves_html(monkeypatch):
    _stub_runtime(monkeypatch)

    with TestClient(app.app) as client:
        response = client.get("/clean-nufi")

    assert response.status_code == 200
    assert "Clean Nufi" in response.text
    assert "Drop a" in response.text


def test_wordcloud_image_route_serves_png(monkeypatch, tmp_path):
    _stub_runtime(monkeypatch)
    image_path = tmp_path / "nufi_wordcloud_real.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    monkeypatch.setattr(app, "_resolve_wordcloud_image_path", lambda: image_path)

    with TestClient(app.app) as client:
        response = client.get("/api/stats/wordcloud-image")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")
