"""
Generate images from a prompts file using xAI grok-imagine.

Prompts file format — one prompt per section, separated by ---:
  A cinematic shot of ancient Tamil warships at sunrise...
  ---
  Rajaraja Chola standing at Nagapattinam harbour...

Usage:
  $env:XAI_API_KEY = "xai-..."
  python images_from_prompts.py <prompts_file.txt> <output_folder>

Example:
  python images_from_prompts.py "naval chola/image-prompts.txt" "naval chola/images"
"""

import sys, os, re, json, pathlib, base64
import requests

MODEL = "grok-imagine-image-quality"


def headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def generate_image(prompt: str, api_key: str, session: requests.Session) -> str:
    resp = session.post(
        "https://api.x.ai/v1/images/generations",
        headers=headers(api_key),
        json={"model": MODEL, "prompt": prompt},
        timeout=180,
    )
    resp.raise_for_status()
    item = resp.json()["data"][0]
    return item.get("url") or item.get("b64_json")


def save_image(url_or_b64: str, dest: pathlib.Path, session: requests.Session):
    if url_or_b64.startswith("http"):
        r = session.get(url_or_b64, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
    else:
        dest.write_bytes(base64.b64decode(url_or_b64))


def main():
    if len(sys.argv) < 3:
        print("Usage: python images_from_prompts.py <prompts_file.txt> <output_folder>")
        sys.exit(1)

    prompts_file = pathlib.Path(sys.argv[1])
    out_dir      = pathlib.Path(sys.argv[2])

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: XAI_API_KEY not set.")
    if not prompts_file.exists():
        raise SystemExit(f"Error: prompts file not found: {prompts_file}")

    raw = prompts_file.read_text(encoding="utf-8-sig")
    prompts = [p.strip() for p in re.split(r"^---+\s*$", raw, flags=re.MULTILINE)]
    prompts = [p for p in prompts if p]

    out_dir.mkdir(parents=True, exist_ok=True)

    # Find next available image number to avoid overwriting existing files
    existing = [int(f.stem.split("_")[1]) for f in out_dir.glob("image_*.jpg")
                if len(f.stem.split("_")) > 1 and f.stem.split("_")[1].isdigit()]
    next_num = max(existing, default=0) + 1

    print(f"Found {len(prompts)} prompts — saving images to '{out_dir}' (starting at image_{next_num:02d})\n")

    with requests.Session() as session:
        for i, prompt in enumerate(prompts, 0):
            num = next_num + i
            print(f"[{i+1}/{len(prompts)}] {prompt[:80]}...")
            try:
                result   = generate_image(prompt, api_key, session)
                img_path = out_dir / f"image_{num:02d}.jpg"
                save_image(result, img_path, session)
                print(f"  Saved: {img_path.name} ({img_path.stat().st_size/1024:.1f} KB)\n")
            except requests.HTTPError as e:
                print(f"  API error {e.response.status_code}: {e.response.text}\n")
            except Exception as e:
                print(f"  Error: {e}\n")

    print("Done.")


if __name__ == "__main__":
    main()
