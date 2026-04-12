# GitHub Actions (CI / CD)

## CI

On every push or pull request to `main` / `master`, **pytest** runs (`tests/`).

## Deploy to Azure (optional)

After tests pass on a push to `main` or `master`, the workflow can deploy the repo root as a zip to **Azure App Service**.

### One-time setup

1. Create the Web App in Azure (Linux, Python 3.11+). Configure **Startup command** (see `docs/azure-deploy.md`).
2. In GitHub: **Settings → Secrets and variables → Actions**
   - **Variables → New repository variable**
     - Name: `AZURE_WEBAPP_NAME`  
     - Value: your app name only (e.g. `nufi-api`, not the full URL).
   - **Secrets → New repository secret**
     - Name: `AZURE_WEBAPP_PUBLISH_PROFILE`  
     - Value: paste the full contents of the **Publish profile** file from Azure (Web App → **Get publish profile** / download `.PublishSettings` and open in a text editor).

3. Push to `main`. The **deploy-azure** job runs only if `AZURE_WEBAPP_NAME` is set; the deploy step uses the publish profile secret.

If you do not use Azure, leave `AZURE_WEBAPP_NAME` unset; the deploy step is skipped and CI still passes.

## Manual run

**Actions → CI → Run workflow** to run tests (and deploy on `main` if configured).
