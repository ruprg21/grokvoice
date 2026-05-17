"""
Batch TTS generator — processes multiple script files and saves MP3s alongside each script.
Usage:
  $env:XAI_API_KEY = "xai-..."
  python generate_batch.py "path/to/folder" script-intro.txt script-1.txt script-2.txt script-3.txt
"""

import sys, os, re, json, pathlib
import urllib.request, urllib.error

VOICE_ID    = "leo"
TIMEOUT_SEC = 180   # 3 minutes per file

def generate_mp3(txt_path: pathlib.Path, api_key: str) -> pathlib.Path:
    raw  = txt_path.read_text(encoding="utf-8")
    text = re.sub(r"^---+\s*$", "", raw, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    print(f"  Sending {len(text)} chars to xAI TTS (voice: {VOICE_ID})...")

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

    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        audio = resp.read()

    out = txt_path.with_suffix(".mp3")
    out.write_bytes(audio)
    return out


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_batch.py <folder> <file1.txt> [file2.txt ...]")
        sys.exit(1)

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: XAI_API_KEY not set.")

    folder = pathlib.Path(sys.argv[1])
    files  = sys.argv[2:]

    print(f"Batch: {len(files)} files in '{folder.name}'\n")

    for i, fname in enumerate(files, 1):
        txt_path = folder / fname
        print(f"[{i}/{len(files)}] {fname}")
        if not txt_path.exists():
            print(f"  ERROR: file not found — skipping\n")
            continue
        try:
            out = generate_mp3(txt_path, api_key)
            print(f"  Saved: {out.name} ({out.stat().st_size/1024:.1f} KB)\n")
        except urllib.error.HTTPError as e:
            print(f"  API error {e.code}: {e.read().decode()}\n")
        except Exception as e:
            print(f"  Error: {e}\n")

    print("Done.")


if __name__ == "__main__":
    main()
