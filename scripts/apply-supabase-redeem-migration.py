"""Apply QuantLab cross-site card redemption migration to shared Supabase DB.

Requires CARD_POOL_DATABASE_URL in .env (Postgres connection string from Supabase
Dashboard → Project Settings → Database → Connection string URI).

If only CARD_POOL_SUPABASE_URL + CARD_POOL_SERVICE_KEY are set, this script probes
whether external_user_ref already exists via PostgREST.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = ROOT / "scripts" / "sql" / "migration-quantlab-redeem.sql"


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def probe_postgrest() -> bool:
    base = (os.environ.get("CARD_POOL_SUPABASE_URL") or "").rstrip("/")
    key = os.environ.get("CARD_POOL_SERVICE_KEY") or ""
    if not base or not key:
        return False
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{base}/rest/v1/membership_redemptions",
                params={"select": "external_user_ref", "limit": "1"},
                headers=headers,
            )
        return resp.status_code < 400
    except httpx.HTTPError:
        return False


def apply_via_psycopg(db_url: str) -> None:
    import psycopg

    sql = SQL_FILE.read_text(encoding="utf-8")
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("Migration applied successfully via CARD_POOL_DATABASE_URL.")


def main() -> int:
    load_dotenv()
    if not SQL_FILE.is_file():
        print(f"Missing SQL file: {SQL_FILE}", file=sys.stderr)
        return 1

    db_url = os.environ.get("CARD_POOL_DATABASE_URL", "").strip()
    if db_url:
        try:
            apply_via_psycopg(db_url)
            return 0
        except Exception as exc:
            print(f"Database migration failed: {exc}", file=sys.stderr)
            return 1

    if probe_postgrest():
        print("Migration already applied (external_user_ref column exists).")
        return 0

    print("Card pool migration NOT applied yet.")
    print()
    print("Option A — Supabase SQL Editor (one-time):")
    print("  1. Open Supabase Dashboard → SQL → New query")
    print(f"  2. Paste contents of: {SQL_FILE}")
    print("  3. Run")
    print()
    print("Option B — add to .env and re-run this script:")
    print("  CARD_POOL_DATABASE_URL=postgresql://postgres.[ref]:[password]@...")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
