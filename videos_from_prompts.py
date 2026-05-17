"""
Generate videos from a prompts file using xAI grok-imagine-video.

Prompts file format — one prompt per section, separated by ---:
  Text-to-video:
    Slow aerial pullback... | duration: 10 | aspect_ratio: 16:9 | resolution: 720p

  Image-to-video (animate an existing image):
    Slow cinematic zoom into the king... | image: image_04.jpg | duration: 8 | aspect_ratio: 16:9 | resolution: 720p

  The image: path is relative to the prompts file folder, or use an absolute path.

Usage:
  $env:XAI_API_KEY = "xai-..."
  python videos_from_prompts.py <prompts_file.txt> <output_folder>
"""

import sys, os, re, json, pathlib, time, base64
import requests

MODEL         = "grok-imagine-video"
POLL_INTERVAL = 15   # seconds between status checks
POLL_TIMEOUT  = 600  # max wait per video (10 minutes)
BASE_URL      = "https://api.x.ai/v1"

DEFAULTS = {"duration": 5, "resolution": "720p", "aspect_ratio": "16:9"}


def auth(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def parse_prompt(raw: str, prompts_dir: pathlib.Path) -> tuple[str, dict, str | None]:
    """Split 'prompt text | key: val | ...' into (clean_prompt, settings, image_path_or_None)."""
    settings   = dict(DEFAULTS)
    image_path = None
    parts      = [p.strip() for p in raw.split("|")]
    prompt_text = parts[0]

    for part in parts[1:]:
        if ":" in part:
            k, v = part.split(":", 1)
            k, v = k.strip(), v.strip()
            if k == "duration":
                settings["duration"] = int(v)
            elif k in ("aspect_ratio", "resolution"):
                settings[k] = v
            elif k == "image":
                img = pathlib.Path(v)
                image_path = img if img.is_absolute() else prompts_dir / img

    return prompt_text, settings, image_path


def image_to_data_uri(img_path: pathlib.Path) -> str:
    ext = img_path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    b64 = base64.b64encode(img_path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def submit_video(prompt: str, settings: dict, api_key: str, session: requests.Session,
                 image_path: pathlib.Path | None = None) -> str:
    body = {
        "model":        MODEL,
        "prompt":       prompt,
        "duration":     settings["duration"],
        "resolution":   settings["resolution"],
        "aspect_ratio": settings["aspect_ratio"],
    }
    if image_path:
        body["image"] = {"url": image_to_data_uri(image_path)}

    resp = session.post(f"{BASE_URL}/videos/generations", headers=auth(api_key),
                        json=body, timeout=300)
    resp.raise_for_status()
    return resp.json()["request_id"]


def poll_video(request_id: str, api_key: str, session: requests.Session) -> dict:
    resp = session.get(f"{BASE_URL}/videos/{request_id}", headers=auth(api_key), timeout=60)
    resp.raise_for_status()
    return resp.json()


def wait_for_video(request_id: str, api_key: str, session: requests.Session) -> str | None:
    elapsed = 0
    while elapsed < POLL_TIMEOUT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        try:
            result = poll_video(request_id, api_key, session)
        except Exception as e:
            print(f"    Poll error: {e} — retrying...")
            continue

        status = result.get("status", "unknown")
        print(f"    [{elapsed}s] Status: {status}")

        if status == "done":
            return result.get("video", {}).get("url")
        if status == "failed":
            print(f"    Failed: {result.get('error', 'unknown error')}")
            return None

    print(f"    Timed out after {POLL_TIMEOUT}s")
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python videos_from_prompts.py <prompts_file.txt> <output_folder>")
        sys.exit(1)

    prompts_file = pathlib.Path(sys.argv[1])
    out_dir      = pathlib.Path(sys.argv[2])

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: XAI_API_KEY not set.")
    if not prompts_file.exists():
        raise SystemExit(f"Error: prompts file not found: {prompts_file}")

    prompts_dir = prompts_file.parent
    raw         = prompts_file.read_text(encoding="utf-8-sig")
    entries     = [p.strip() for p in re.split(r"^---+\s*$", raw, flags=re.MULTILINE)]
    entries     = [p for p in entries if p]

    out_dir.mkdir(parents=True, exist_ok=True)

    # Find next available video number to avoid overwriting existing files
    existing = [int(f.stem.split("_")[1]) for f in out_dir.glob("video_*.mp4")
                if f.stem.split("_")[1].isdigit()]
    next_num = max(existing, default=0) + 1

    print(f"Found {len(entries)} prompts — saving videos to '{out_dir}' (starting at video_{next_num:02d})\n")

    with requests.Session() as session:
        for i, entry in enumerate(entries, 0):
            prompt, settings, image_path = parse_prompt(entry, prompts_dir)
            num  = next_num + i
            mode = f"image-to-video ({image_path.name})" if image_path else "text-to-video"
            print(f"[{i+1}/{len(entries)}] [{mode}] {prompt[:70]}...")
            print(f"  Settings: {settings['duration']}s, {settings['resolution']}, {settings['aspect_ratio']}")

            if image_path and not image_path.exists():
                print(f"  ERROR: image not found: {image_path}\n")
                continue

            try:
                request_id = submit_video(prompt, settings, api_key, session, image_path)
                print(f"  Job ID: {request_id} — waiting...")

                video_url = wait_for_video(request_id, api_key, session)
                if not video_url:
                    continue

                vid_path = out_dir / f"video_{num:02d}.mp4"
                print(f"  Downloading...")
                r = session.get(video_url, timeout=120)
                r.raise_for_status()
                vid_path.write_bytes(r.content)
                print(f"  Saved: {vid_path.name} ({vid_path.stat().st_size/1024/1024:.1f} MB)\n")

            except requests.HTTPError as e:
                print(f"  API error {e.response.status_code}: {e.response.text}\n")
            except Exception as e:
                print(f"  Error: {e}\n")

    print("Done.")


if __name__ == "__main__":
    main()
