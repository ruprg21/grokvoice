"""
One-off: generate a notebook-style sketchnote via grok-imagine-image-quality.

Does not modify LinkedIn or YouTube scripts. Uses grokapi.env.

  python grok_notebook_sketch.py
  python grok_notebook_sketch.py --aspect square --out my_sketch.jpg
"""

from __future__ import annotations

import argparse
import base64
import os
import pathlib
import sys
from datetime import datetime

import requests

PROJECT_DIR = pathlib.Path(__file__).parent
DEFAULT_OUT_DIR = PROJECT_DIR / "notebook_sketches"
ENV_FILES = ("grokapi.env", ".env", ".env.example")
IMAGE_MODEL = "grok-imagine-image-quality"
ASPECT = {"landscape": "16:9", "square": "1:1", "portrait": "9:16"}

HEADLESS_CRM_PROMPT = """Spiral-bound lined notebook page, hand-drawn sketchnote infographic style,
green highlighter accents on headings, black ink doodle icons (API plugs, robots, clouds, gears),
professional but casual visual journalism. All text must be sharp and legible English typography.

TITLE (top, large, highlighted green):
HEADLESS CRM SIGNAL: Salesforce Without the Screens

SUBTITLE:
APIs, AI agents, and data fabric instead of classic UI clicks.

SECTION 1 - What changed
Heading: From UI-first to API-first
- Salesforce workloads now exposed as APIs and events.
- AI agents can read and write CRM data directly.
- Many tasks never touch the standard Salesforce screens.

SECTION 2 - Why it matters
Heading: Less clicking, more orchestration
- Repetitive admin workflows become background jobs.
- Screen time moves from humans to automations.
- Value shifts to clean data models and reliable APIs.

SECTION 3 - Impact on builders
Heading: New skill stack for admins & devs
- Strong API and integration literacy is a must.
- Prompt design and AI orchestration join the toolkit.
- Knowing when not to build UI becomes a design skill.

SECTION 4 - Impact on buyers
Heading: Buying a platform, not just a screen
- RFPs must ask about events, webhooks, and AI hooks.
- Vendor lock-in now hides in data and workflows.
- Total cost includes automation engineering, not only licenses.

SECTION 5 - Risks
Heading: Where this can go wrong
- Opaque automations that nobody can explain.
- Shadow AI agents changing records without governance.
- Over-automation breaking frontline trust in the system.

SECTION 6 - Worth watching
Heading: Signals to track in 2026
- Native headless SKUs from major CRM vendors.
- AppExchange-style marketplaces for AI agents.
- Job posts asking for CRM orchestration architect.

BOTTOM STRIP (footer banner):
Want the deeper breakdown? We unpack headless CRM, AI agents, and buyer implications every week in The CRM Signal.

Multi-column notebook layout, arrows connecting sections, no photorealistic people, no garbled text."""


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
            "prompt": prompt,
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Grok Imagine notebook sketchnote")
    parser.add_argument(
        "--aspect",
        choices=list(ASPECT),
        default="portrait",
        help="Image aspect ratio (default portrait 9:16 for notebook page)",
    )
    parser.add_argument("--out", help="Output path (.jpg or .png)")
    parser.add_argument("--prompt-file", help="Custom prompt text file")
    args = parser.parse_args()

    load_env_file()
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        print("Error: XAI_API_KEY not set in grokapi.env", file=sys.stderr)
        return 1

    prompt = HEADLESS_CRM_PROMPT
    if args.prompt_file:
        prompt = pathlib.Path(args.prompt_file).read_text(encoding="utf-8-sig").strip()

    out = pathlib.Path(args.out) if args.out else None
    if not out:
        DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = DEFAULT_OUT_DIR / f"headless_crm_signal_{stamp}.jpg"

    print(f"Model: {IMAGE_MODEL}")
    print(f"Aspect: {args.aspect} ({ASPECT[args.aspect]})")
    print("Generating notebook sketchnote (this may take 30-90s)...")

    with requests.Session() as session:
        raw = generate(api_key, prompt, args.aspect, session)

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".jpg", ".jpeg"):
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.save(out, format="JPEG", quality=92)
    else:
        out.write_bytes(raw)

    print(f"Saved: {out}")
    print("Note: Dense text in AI images may be imperfect; use Napkin or Canva for exact copy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
