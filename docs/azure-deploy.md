# Azure App Service Deploy

## Required Runtime Files

Azure needs the runtime path only:

- `app.py`
- `nufi_model.py`
- `requirements.txt`
- `startup.sh`
- `static/`
- `data/`
- corpus files consumed by `nufi_model.py`

`requirements.txt` is the production dependency set. Use `requirements-dev.txt` only for tests and local maintenance scripts.

## Recommended GitHub Flow

Use `.github/workflows/ci.yml`.

Required GitHub settings:

- repository variable or secret: `AZURE_WEBAPP_NAME`
- `AZURE_CREDENTIALS` (JSON) or the four secrets `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID` — see `docs/github-actions.md`

## Startup Command

Use either:

```bash
bash startup.sh
```

or:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port ${PORT}
```

## Notes

- Keep `SCM_DO_BUILD_DURING_DEPLOYMENT=true` if Azure should install `requirements.txt` during deploy.
- First cold start can be slow if the API rebuilds `data/Nufi/Nufi_language_model_api.pickle`.
- If the web UI is served from the same app, keep browser calls relative as `/api/...`.
