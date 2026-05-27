"""
One-time setup: authorize Google Drive with your personal Google account.

Requires client_secret.json (OAuth Desktop client) from Google Cloud Console.
Creates drive_token.json (gitignored) used by linkedin_images_watcher.py.

Run:
  python setup_drive_oauth.py
"""

import pathlib
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

PROJECT_DIR = pathlib.Path(__file__).parent
CLIENT_SECRETS = PROJECT_DIR / "client_secret.json"
TOKEN_FILE = PROJECT_DIR / "drive_token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    if not CLIENT_SECRETS.exists():
        raise SystemExit(
            "Error: client_secret.json not found.\n"
            "Google Cloud Console -> APIs & Services -> Credentials ->\n"
            "Create OAuth client ID (Desktop app) -> download JSON ->\n"
            "save as client_secret.json in this folder."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
    print("Opening browser to sign in with your Google account...")
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print(f"Saved {TOKEN_FILE.name}. You can run linkedin_images_watcher.py now.")


if __name__ == "__main__":
    main()
