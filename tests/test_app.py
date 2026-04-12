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
