#!/bin/bash
# Azure App Service (Linux) startup — uses PORT from the platform.
set -e
cd "${HOME}/site/wwwroot" 2>/dev/null || true
PORT="${PORT:-8000}"
exec python -m uvicorn app:app --host 0.0.0.0 --port "${PORT}"
