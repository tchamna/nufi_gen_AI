"""Resolve app name and service-principal fields for Azure deploy (used from ci.yml only)."""
from __future__ import annotations

import json
import os
import sys

_ENV_DELIM = "__AZURE_DEPLOY_ENV__"


def _emit_output(name: str, value: str) -> None:
    path = os.environ["GITHUB_OUTPUT"]
    with open(path, "a", encoding="utf-8") as f:
        if "\n" in value:
            f.write(f"{name}<<{_ENV_DELIM}\n{value}\n{_ENV_DELIM}\n")
        else:
            f.write(f"{name}={value}\n")


def _emit_env(name: str, value: str) -> None:
    path = os.environ["GITHUB_ENV"]
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{name}<<{_ENV_DELIM}\n{value}\n{_ENV_DELIM}\n")


def _normalize_cred_obj(c: dict) -> dict:
    out = dict(c)
    if not out.get("clientId") and out.get("appId"):
        out["clientId"] = out["appId"]
    if not out.get("clientSecret") and out.get("password"):
        out["clientSecret"] = out["password"]
    if not out.get("tenantId") and out.get("tenant"):
        out["tenantId"] = out["tenant"]
    return out


def main() -> int:
    app = (os.environ.get("APP_VAR") or "").strip()
    if not app:
        app = (os.environ.get("APP_SECRET") or "").strip()

    cid = (os.environ.get("AZURE_CLIENT_ID") or "").strip()
    csec = (os.environ.get("AZURE_CLIENT_SECRET") or "").strip()
    sub = (os.environ.get("AZURE_SUBSCRIPTION_ID") or "").strip()
    ten = (os.environ.get("AZURE_TENANT_ID") or "").strip()
    split_ok = bool(cid and csec and sub and ten)

    raw_json = (os.environ.get("AZURE_CREDENTIALS") or "").strip()

    if not split_ok and raw_json:
        try:
            c = _normalize_cred_obj(json.loads(raw_json))
        except json.JSONDecodeError:
            print(
                "::error::AZURE_CREDENTIALS is not valid JSON. Use the full output of "
                "`az ad sp create-for-rbac ... --sdk-auth`, or set secrets AZURE_CLIENT_ID, "
                "AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID, and AZURE_TENANT_ID.",
                file=sys.stderr,
            )
            return 1
        cid = (c.get("clientId") or "").strip()
        csec = (c.get("clientSecret") or "").strip()
        sub = (c.get("subscriptionId") or "").strip()
        ten = (c.get("tenantId") or "").strip()

    if not app:
        _emit_output("deploy", "false")
        print(
            "::notice::Set repository variable or secret AZURE_WEBAPP_NAME to enable deploy. "
            "See docs/github-actions.md"
        )
        return 0

    if not all([cid, csec, sub, ten]):
        _emit_output("deploy", "false")
        if not raw_json and not split_ok:
            print(
                "::notice::Add AZURE_CREDENTIALS (JSON from `az ad sp create-for-rbac ... --sdk-auth`) "
                "or secrets AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID."
            )
        else:
            print(
                "::notice::Azure credentials are incomplete. "
                "JSON must include clientId, clientSecret, subscriptionId, and tenantId "
                "(see docs/github-actions.md)."
            )
        return 0

    _emit_output("deploy", "true")
    _emit_env("DEPLOY_APP_NAME", app)
    _emit_env("AZURE_LOGIN_CLIENT_ID", cid)
    _emit_env("AZURE_LOGIN_CLIENT_SECRET", csec)
    _emit_env("AZURE_LOGIN_TENANT_ID", ten)
    _emit_env("AZURE_LOGIN_SUBSCRIPTION_ID", sub)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
