"""
One-off: B2B SaaS technical infographic via Grok Imagine (grok-imagine-image-quality).

Reads infographic/*.txt. Uses grokapi.env (XAI_API_KEY).

  python grok_infographic.py
  python grok_infographic.py --prompt-file infographic/info_script.txt --aspect landscape
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import pathlib
import sys
from datetime import datetime

import requests
from PIL import Image

PROJECT_DIR = pathlib.Path(__file__).parent
DEFAULT_PROMPT = PROJECT_DIR / "infographic" / "info_script.txt"
DEFAULT_OUT_DIR = PROJECT_DIR / "infographic"
ENV_FILES = ("grokapi.env", ".env", ".env.example")
IMAGE_MODEL = "grok-imagine-image-quality"
ASPECT = {"landscape": "16:9", "square": "1:1", "portrait": "9:16"}

STYLE_PREFIX = """Professional B2B SaaS technical infographic, dense vertical one-pager layout
on wide landscape canvas. Flat corporate design: dark navy header band with bold white title,
Salesforce cloud logo area, four color-coded circular pillar icons in a row (Identity,
Intelligence, Action, Engagement), section of four feature cards with flat icons, large
BEFORE vs AFTER comparison table (left column red header with X marks, right column green
header with checkmarks), time savings metric (days to minutes), horizontal workflow arrow
strip with labeled steps, footer with key takeaways bullets and tech stack status table.
Clean sans-serif typography, high contrast teal and blue accents, no photorealistic people,
all text sharp and legible English. NOT a Gantt chart, NOT a timeline, NOT a single metaphor
illustration only.

Exact content to render on the infographic:

"""


def load_env_file() -> None:
    for name in ENV_FILES:
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


def generate(api_key: str, prompt: str, aspect: str, session: requests.Session) -> bytes:
    ratio = ASPECT.get(aspect, "16:9")
    resp = session.post(
        "https://api.x.ai/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": IMAGE_MODEL,
            "prompt": prompt[:12000],
            "aspect_ratio": ratio,
            "resolution": "2k",
        },
        timeout=180,
    )
    resp.raise_for_status()
    item = resp.json()["data"][0]
    url_or_b64 = item.get("url") or item.get("b64_json")
    if not url_or_b64:
        raise ValueError("No image in API response")
    if url_or_b64.startswith("http"):
        r = session.get(url_or_b64, timeout=120)
        r.raise_for_status()
        return r.content
    return base64.b64decode(url_or_b64)


def slug_from_path(path: pathlib.Path) -> str:
    return path.stem.replace(" ", "_")[:40]


def main() -> int:
    parser = argparse.ArgumentParser(description="Grok Imagine B2B SaaS infographic")
    parser.add_argument(
        "--prompt-file",
        default=str(DEFAULT_PROMPT),
        help="Content file (default: infographic/info_script.txt)",
    )
    parser.add_argument(
        "--aspect",
        choices=list(ASPECT),
        default="landscape",
        help="Aspect ratio (default landscape 16:9 for LinkedIn)",
    )
    parser.add_argument("--out", help="Output path (.jpg or .png)")
    args = parser.parse_args()

    load_env_file()
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        print("Error: XAI_API_KEY not set in grokapi.env", file=sys.stderr)
        return 1

    prompt_path = pathlib.Path(args.prompt_file)
    if not prompt_path.is_file():
        print(f"Error: prompt file not found: {prompt_path}", file=sys.stderr)
        return 1

    script = prompt_path.read_text(encoding="utf-8-sig").strip()
    prompt = STYLE_PREFIX + script

    out = pathlib.Path(args.out) if args.out else None
    if not out:
        DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = DEFAULT_OUT_DIR / f"{slug_from_path(prompt_path)}_grok_{stamp}.jpg"

    print(f"Model: {IMAGE_MODEL}")
    print(f"Aspect: {args.aspect} ({ASPECT[args.aspect]})")
    print(f"Prompt file: {prompt_path}")
    print(f"Prompt length: {len(prompt)} chars")
    print("Generating via Grok Imagine (may take 30-90s)...")

    with requests.Session() as session:
        raw = generate(api_key, prompt, args.aspect, session)

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".jpg", ".jpeg"):
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.save(out, format="JPEG", quality=92)
    else:
        out.write_bytes(raw)

    print(f"Saved: {out}")
    print("Note: Dense text may have typos; refine in Canva or compare with Napkin output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
