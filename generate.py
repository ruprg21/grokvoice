import sys, os, re, urllib.request, json, pathlib

input_file = sys.argv[1] if len(sys.argv) > 1 else None
if not input_file:
    print("Usage: python generate.py <script.txt>")
    sys.exit(1)

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    print("Error: XAI_API_KEY environment variable is not set.")
    sys.exit(1)

raw = pathlib.Path(input_file).read_text(encoding="utf-8")
text = re.sub(r"^---+\s*$", "", raw, flags=re.MULTILINE)
text = re.sub(r"\n{3,}", "\n\n", text).strip()

print(f"Sending {len(text)} characters to xAI TTS (voice: leo)...")

payload = json.dumps({
    "text": text,
    "voice_id": "leo",
    "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 128000},
    "language": "en",
}).encode()

req = urllib.request.Request(
    "https://api.x.ai/v1/tts",
    data=payload,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        audio = resp.read()
except urllib.error.HTTPError as e:
    print(f"TTS error {e.code}: {e.read().decode()}")
    sys.exit(1)

output_file = pathlib.Path(input_file).stem + ".mp3"
pathlib.Path(output_file).write_bytes(audio)
print(f"Saved to {output_file} ({len(audio)/1024:.1f} KB)")
