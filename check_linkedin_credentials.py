"""
Check point-2 credentials for linkedin_images_watcher.py (no secrets printed).
Run: python check_linkedin_credentials.py
"""

import json
import os
import pathlib
import sys

PROJECT_DIR = pathlib.Path(__file__).parent
SA_FILE = PROJECT_DIR / "service_account.json"
def load_env_file():
    env_file = None
    for name in ("grokapi.env", ".env", ".env.example"):
        candidate = PROJECT_DIR / name
        if candidate.exists():
            env_file = candidate
            break
    if env_file is None:
        return
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main():
    load_env_file()
    ok = True

    if SA_FILE.exists():
        try:
            data = json.loads(SA_FILE.read_text(encoding="utf-8"))
            email = data.get("client_email", "(no client_email)")
            print(f"[OK] service_account.json found")
            print(f"     Share Sheet + Drive folder with: {email}")
        except json.JSONDecodeError:
            print("[FAIL] service_account.json is not valid JSON")
            ok = False
    else:
        print("[FAIL] service_account.json missing in project folder")
        print("       Download from Google Cloud > IAM > Service Accounts > Keys")
        ok = False

    key = os.environ.get("XAI_API_KEY", "")
    if key and key.startswith("xai-") and "your-key" not in key:
        print(f"[OK] XAI_API_KEY set (length {len(key)})")
    elif not key:
        print("[FAIL] XAI_API_KEY empty in grokapi.env / .env / .env.example")
        ok = False
    elif "your-key" in key:
        print("[FAIL] XAI_API_KEY looks like a placeholder; set your real key")
        ok = False
    else:
        print("[FAIL] XAI_API_KEY not set")
        print("       Copy .env.example to .env and add your key, or:")
        print('       $env:XAI_API_KEY = "xai-..."')
        ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
