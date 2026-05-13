"""
Google Sheets → xAI TTS watcher

Sheet layout (row 1 = header):
  A: filename     e.g. script1.txt
  B: approved     checkbox (TRUE/FALSE)
  C: status       auto-filled by this script

Setup:
  1. pip install gspread google-auth
  2. Create a Google service account and download service_account.json into this folder
     https://console.cloud.google.com → IAM → Service Accounts → Create
     Enable Google Sheets API, share your sheet with the service account email
  3. Set SHEET_ID below to your sheet's ID (from the URL)
  4. Run:
       $env:XAI_API_KEY = "xai-..."
       python watcher.py
"""

import gspread, time, os, re, json, pathlib, urllib.request, urllib.error

# ── Config ────────────────────────────────────────────────────────────────────
SHEET_ID        = "YOUR_SHEET_ID_HERE"   # from sheet URL: /d/<SHEET_ID>/edit
WORKSHEET_NAME  = "Sheet1"
SCRIPTS_FOLDER  = pathlib.Path(__file__).parent
POLL_INTERVAL   = 30   # seconds between checks
VOICE_ID        = "leo"
# ─────────────────────────────────────────────────────────────────────────────

COL_FILENAME = 1
COL_APPROVED = 2
COL_STATUS   = 3

DONE_STATES = {"done ✓", "processing"}


def generate_mp3(filename: str, api_key: str) -> tuple[bool, str]:
    txt_path = SCRIPTS_FOLDER / filename
    if not txt_path.exists():
        return False, f"file not found: {filename}"

    raw  = txt_path.read_text(encoding="utf-8")
    text = re.sub(r"^---+\s*$", "", raw, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    payload = json.dumps({
        "text": text,
        "voice_id": VOICE_ID,
        "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 128000},
        "language": "en",
    }).encode()

    req = urllib.request.Request(
        "https://api.x.ai/v1/tts",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as e:
        return False, f"API {e.code}: {e.read().decode()}"

    out = SCRIPTS_FOLDER / (pathlib.Path(filename).stem + ".mp3")
    out.write_bytes(audio)
    return True, out.name


def main():
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: XAI_API_KEY not set.")

    if SHEET_ID == "YOUR_SHEET_ID_HERE":
        raise SystemExit("Error: set SHEET_ID in watcher.py before running.")

    sa_file = SCRIPTS_FOLDER / "service_account.json"
    if not sa_file.exists():
        raise SystemExit("Error: service_account.json not found in project folder.")

    gc = gspread.service_account(filename=str(sa_file))
    ws = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    print(f"Watching '{WORKSHEET_NAME}' — polling every {POLL_INTERVAL}s. Ctrl+C to stop.\n")

    while True:
        try:
            rows = ws.get_all_values()
            for i, row in enumerate(rows[1:], start=2):   # skip header row
                if len(row) < 2:
                    continue
                filename = row[0].strip()
                approved = row[1].strip().upper() in ("TRUE", "YES", "1", "✓")
                status   = row[2].strip() if len(row) > 2 else ""

                if not filename or not approved:
                    continue
                if status in DONE_STATES or status.startswith("error"):
                    continue

                print(f"[row {i}] Processing {filename}...")
                ws.update_cell(i, COL_STATUS, "processing")
                ok, result = generate_mp3(filename, api_key)

                if ok:
                    ws.update_cell(i, COL_STATUS, "done ✓")
                    print(f"[row {i}] Saved → {result}")
                else:
                    ws.update_cell(i, COL_STATUS, f"error: {result}")
                    print(f"[row {i}] Error: {result}")

        except gspread.exceptions.APIError as e:
            print(f"Sheets API error: {e} — retrying next cycle")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
