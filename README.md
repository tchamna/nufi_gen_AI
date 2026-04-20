# Nufi N-gram Web App

This repo has one main production flow:

1. `app.py` runs the FastAPI API.
2. `static/` provides the web UI served by the API.
3. `android-keyboard/` is a separate client that talks to the same API.
4. `.github/workflows/ci.yml` runs tests and optionally deploys to Azure.

Most other scripts are for corpus preparation, exports, and visualization. They are useful for maintenance, but they are not part of the runtime deploy path.

## Quick Start

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:8010/`.

## Tests And Tooling

Install the development dependencies when you need tests, corpus tooling, charts, or local maintenance scripts:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

## API

- `POST /api/generate`
- `POST /api/suggest`
- `POST /api/keyboard/suggest`
- `GET /api/audio/{word}`
- `HEAD /api/audio/{word}`

## Pipeline

The repo now uses one GitHub Actions workflow: `.github/workflows/ci.yml`.

- `push` and `pull_request` on `main` / `master`: run tests
- `push` to `main` / `master`: deploy to Azure only when the Azure repo settings are configured
- `workflow_dispatch`: run manually from GitHub Actions

Azure deploy uses:

- repository variable: `AZURE_WEBAPP_NAME`
- repository secret: `AZURE_WEBAPP_PUBLISH_PROFILE`

See `docs/github-actions.md` and `docs/azure-deploy.md`.

## Cleanup

Generated local artifacts and temp files are ignored in `.gitignore`.

Review `docs/repo-cleanup.md` before removing tracked maintenance files or generated exports from the repo.
