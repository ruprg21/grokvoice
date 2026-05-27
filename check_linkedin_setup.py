"""Check points 2 and 3 for linkedin_images_watcher (no secrets printed)."""

import importlib.util
import json
import os
import pathlib
import sys

PROJECT_DIR = pathlib.Path(__file__).parent


def load_env_file():
    for name in ("grokapi.env", ".env", ".env.example"):
        env_file = PROJECT_DIR / name
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        break


def main():
    load_env_file()
    ok = True
    sa_file = PROJECT_DIR / "service_account.json"

    print("--- Point 2: credentials ---")
    if sa_file.exists():
        email = json.loads(sa_file.read_text(encoding="utf-8")).get("client_email", "?")
        print("[OK] service_account.json")
        print(f"     Service account: {email}")
    else:
        print("[FAIL] service_account.json missing")
        ok = False

    key = os.environ.get("XAI_API_KEY", "")
    if key and key.startswith("xai-") and "your-key" not in key:
        print(f"[OK] XAI_API_KEY (length {len(key)})")
    else:
        print("[FAIL] XAI_API_KEY not set or invalid")
        ok = False

    napkin = os.environ.get("NAPKIN_API_TOKEN", "").strip()
    if napkin and len(napkin) > 10:
        print(f"[OK] NAPKIN_API_TOKEN (length {len(napkin)})")
    else:
        print("[--] NAPKIN_API_TOKEN not set (required only for column F = napkin / diagram)")

    spec = importlib.util.spec_from_file_location(
        "linkedin_watcher", PROJECT_DIR / "linkedin_images_watcher.py"
    )
    w = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(w)

    print("\n--- Point 3: config in script ---")
    sheet_ok = w.SHEET_ID and w.SHEET_ID != "YOUR_SHEET_ID_HERE"
    drive_ok = w.DRIVE_FOLDER_ID and w.DRIVE_FOLDER_ID != "YOUR_DRIVE_FOLDER_ID_HERE"
    if sheet_ok:
        print(f"[OK] SHEET_ID set ({len(w.SHEET_ID)} chars)")
    else:
        print("[FAIL] SHEET_ID not set in linkedin_images_watcher.py")
        ok = False
    if drive_ok:
        print(f"[OK] DRIVE_FOLDER_ID set ({len(w.DRIVE_FOLDER_ID)} chars)")
    else:
        print("[FAIL] DRIVE_FOLDER_ID not set in linkedin_images_watcher.py")
        ok = False
    print(f"     WORKSHEET_NAME = {w.WORKSHEET_NAME!r}")
    print(f"     DRIVE_AUTH = {w.DRIVE_AUTH!r}")

    if not (sheet_ok and drive_ok and sa_file.exists()):
        sys.exit(1 if not ok else 0)

    print("\n--- Point 3: connectivity ---")
    import gspread
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    try:
        gc = gspread.service_account(filename=str(sa_file))
        ws = gc.open_by_key(w.SHEET_ID).worksheet(w.WORKSHEET_NAME)
        rows = ws.get_all_values()
        print(f"[OK] Google Sheet: {len(rows)} row(s), tab {w.WORKSHEET_NAME!r}")
        if len(rows) >= 1:
            print(f"     Header: {rows[0][:5]}")
    except Exception as e:
        print(f"[FAIL] Google Sheet: {e}")
        ok = False

    try:
        uses_oauth = getattr(w, "DRIVE_AUTH", "service_account") == "oauth"
        if uses_oauth:
            if not w.DRIVE_TOKEN_FILE.exists():
                print("[FAIL] drive_token.json missing for DRIVE_AUTH=oauth")
                print("       Run: python setup_drive_oauth.py")
                ok = False
            else:
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials as UserCredentials

                creds = UserCredentials.from_authorized_user_file(
                    str(w.DRIVE_TOKEN_FILE), w.DRIVE_SCOPES
                )
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                drive = build("drive", "v3", credentials=creds, cache_discovery=False)
                folder = (
                    drive.files()
                    .get(fileId=w.DRIVE_FOLDER_ID, fields="id,name", supportsAllDrives=True)
                    .execute()
                )
                print(f"[OK] Drive folder (OAuth / My Drive): {folder.get('name', '?')}")
        else:
            creds = Credentials.from_service_account_file(
                str(sa_file), scopes=w.DRIVE_SCOPES
            )
            drive = build("drive", "v3", credentials=creds, cache_discovery=False)
            folder = (
                drive.files()
                .get(
                    fileId=w.DRIVE_FOLDER_ID,
                    fields="id,name,driveId",
                    supportsAllDrives=True,
                )
                .execute()
            )
            name = folder.get("name", "?")
            if folder.get("driveId"):
                print(f"[OK] Drive folder (Shared Drive): {name}")
            else:
                print(f"[FAIL] Drive folder '{name}' is My Drive, not a Shared Drive")
                print("       Use DRIVE_AUTH='oauth' or a Shared Drive folder.")
                ok = False
    except Exception as e:
        print(f"[FAIL] Drive folder: {e}")
        ok = False

    print()
    if ok:
        print("All checks passed. Run batch: python linkedin_images_watcher.py")
    else:
        print("Fix failures above before running the watcher.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
