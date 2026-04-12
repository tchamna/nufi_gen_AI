# Deploy the Nufi API on Azure App Service (Linux + Python)

## 1. Create the web app

1. Azure Portal → **Create a resource** → **Web App**.
2. **Runtime stack**: Python 3.11 or 3.12 (Linux).
3. **Region**: choose one close to users.
4. **App Service plan**: start with **B1** or higher if the n-gram model is large (RAM matters).
5. Create.

## 2. Configure startup

**Configuration** → **General settings** → **Startup Command**:

```bash
bash startup.sh
```

Or without the script:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port ${PORT}
```

Azure injects `PORT`; `app.py` also reads `PORT` / `WEBSITES_PORT`.

## 3. Application settings (environment variables)

| Name | Example | Purpose |
|------|---------|---------|
| `ALLOWED_ORIGINS` | `https://your-frontend.com,https://www.your-frontend.com` | CORS for browser clients. Use `*` only for quick tests. |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Let Oryx run `pip install` on deploy (if using Git). |

Optional: `WEBSITES_PORT` is usually set automatically; do not override unless you know why.

## 4. Deploy the code + data

The API needs the full repo including **`data/`**, corpus files, and (ideally) the prebuilt **`data/Nufi/Nufi_language_model_api.pickle`**. First cold start may **rebuild** the pickle if sources are newer than the file (can be slow or hit timeouts).

**Options:**

- **GitHub Actions** → deploy to App Service (zip or `azure/webapps-deploy`).
- **VS Code** Azure extension → deploy from folder.
- **ZIP deploy**: include `app.py`, `nufi_model.py`, `requirements.txt`, `startup.sh`, `static/`, `data/`, corpora, etc.

Ensure `requirements.txt` is installed on the server (`pip install -r requirements.txt` during build or in a custom deploy step).

## 5. HTTPS URL

After deploy, the API base URL looks like:

`https://<your-app-name>.azurewebsites.net`

Endpoints (same as local):

- `GET /`
- `POST /api/generate`
- `POST /api/suggest` (if exposed in `app.py`)
- `POST /api/keyboard/suggest`

## 6. Integrate clients

### Web (`static/index.html`)

If the site is served **from the same App Service** (FastAPI serves `static/index.html`), keep relative URLs like `/api/...` — no change.

If the UI is hosted **elsewhere** (another domain), either:

- Call the full API URL: `https://<your-app>.azurewebsites.net/api/...`, or  
- Set `ALLOWED_ORIGINS` to that UI origin and use `fetch` with the Azure base URL.

### Android keyboard

In the keyboard app, open **settings** and set the API base URL to:

`https://<your-app>.azurewebsites.net`

(no trailing slash). Release builds should use **HTTPS** only; turn off cleartext traffic for production.

### React / `App.tsx` bundle

Configure your API base URL at build time or runtime to the Azure HTTPS origin, and add that origin to `ALLOWED_ORIGINS`.

## 7. Troubleshooting

- **504 / timeout**: increase **Always On**, scale up RAM/CPU, or ensure the model is prebuilt and not rebuilding on every deploy.
- **502**: check **Log stream** and **Diagnose and solve problems**; verify startup command and that `PORT` is used.
- **CORS errors**: fix `ALLOWED_ORIGINS` to include the exact browser origin (scheme + host + port).
