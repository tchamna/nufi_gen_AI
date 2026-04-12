# Nufi N-gram Web App

This project contains a small n-gram model and a FastAPI server that exposes a `/api/generate` endpoint and a minimal frontend at `/`.

Quick start (Windows PowerShell):

```powershell
# create venv (only once)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# run the app
.\.venv\Scripts\python.exe app.py

# open http://127.0.0.1:8000/ in your browser
```

API:
- POST /api/generate with JSON {"text": "seed text", "n": 4}
- Returns {"result": "generated text"}

Files added:
- `nufi_model.py`: model loading/building and generation
- `app.py`: FastAPI server
- `static/index.html`: simple frontend

If you want me to run the server here, tell me and I'll start Uvicorn in the terminal.
