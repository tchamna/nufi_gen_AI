from fastapi.testclient import TestClient

import app
import nufi_model as nm


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
    def __init__(self, head_response=None, get_response=None):
        self.head_response = head_response or _FakeAudioResponse()
        self.get_response = get_response or _FakeAudioResponse()

    def head(self, url, timeout=None, allow_redirects=None):
        return self.head_response

    def get(self, url, stream=None, timeout=None, allow_redirects=None):
        return self.get_response


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
        response = client.head("/api/audio/mɑ́ kɑ́ lī")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["cache-control"] == "private, max-age=3600"


def test_audio_get_endpoint_streams_mp3(monkeypatch):
    _stub_runtime(monkeypatch)
    monkeypatch.setattr(app, "_S3_CLIENT", None)
    upstream = _FakeAudioResponse(content=b"mp3-data")
    monkeypatch.setattr(app, "_AUDIO_HTTP", _FakeAudioHttp(get_response=upstream))
    monkeypatch.setattr(app, "_resolve_audio_filename", lambda word, audio_id=None: "makali")

    with TestClient(app.app) as client:
        response = client.get("/api/audio/mɑ́ kɑ́ lī")

    assert response.status_code == 200
    assert response.content == b"mp3-data"
    assert response.headers["content-type"] == "audio/mpeg"
    assert upstream.closed is True


def test_audio_get_endpoint_returns_404_when_mapping_missing(monkeypatch):
    _stub_runtime(monkeypatch)
    monkeypatch.setattr(app, "_S3_CLIENT", None)
    monkeypatch.setattr(app, "_resolve_audio_filename", lambda word, audio_id=None: None)

    with TestClient(app.app) as client:
        response = client.get("/api/audio/unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "audio not found"
