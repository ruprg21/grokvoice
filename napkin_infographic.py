"""
One-off: B2B SaaS technical infographic via Napkin AI (napkin_elegant).

Does not use Google Sheets. Reads prompt from infographic/*.txt. Uses grokapi.env.

  python napkin_infographic.py
  python napkin_infographic.py --prompt-file infographic/info_script.txt --style napkin_elegant
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from datetime import datetime

import requests

from linkedin_images_watcher import (
    build_napkin_content,
    generate_napkin_bytes,
    resize_for_linkedin_fit,
)

PROJECT_DIR = pathlib.Path(__file__).parent
DEFAULT_PROMPT = PROJECT_DIR / "infographic" / "info_script.txt"
DEFAULT_OUT_DIR = PROJECT_DIR / "infographic"
ENV_FILES = ("grokapi.env", ".env", ".env.example")

STYLE_PREFIX = """B2B SaaS technical infographic (dense one-pager, NOT a Gantt chart, NOT a timeline,
NOT a project schedule). Flat corporate design: navy header with title, four color-coded pillar
icons in a row, four innovation cards, side-by-side BEFORE (red, X icons) vs AFTER (green,
checkmarks) columns, time-savings callout, horizontal workflow arrows left-to-right, footer with
key takeaways bullets and a small tech-stack table. Wide landscape layout. Readable labels on
every box. No photorealistic people.

PAGE CONTENT TO LAYOUT:

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


def slug_from_path(path: pathlib.Path) -> str:
    return path.stem.replace(" ", "_")[:40]


def main() -> int:
    parser = argparse.ArgumentParser(description="Napkin B2B SaaS infographic")
    parser.add_argument(
        "--prompt-file",
        default=str(DEFAULT_PROMPT),
        help="Prompt text file (default: infographic/info_script.txt)",
    )
    parser.add_argument(
        "--style",
        default="napkin_elegant",
        choices=("napkin_elegant", "napkin", "napkin_sketch", "napkin_corporate"),
    )
    parser.add_argument(
        "--format",
        default="landscape",
        choices=("landscape", "square"),
        help="LinkedIn output shape (default landscape 1200x627)",
    )
    parser.add_argument("--out", help="Output JPEG path")
    parser.add_argument(
        "--raw-png",
        action="store_true",
        help="Save Napkin PNG without LinkedIn letterbox resize",
    )
    args = parser.parse_args()

    load_env_file()
    token = os.environ.get("NAPKIN_API_TOKEN", "").strip()
    if not token:
        print("Error: NAPKIN_API_TOKEN not set in grokapi.env", file=sys.stderr)
        return 1

    prompt_path = pathlib.Path(args.prompt_file)
    if not prompt_path.is_file():
        print(f"Error: prompt file not found: {prompt_path}", file=sys.stderr)
        return 1

    script = prompt_path.read_text(encoding="utf-8-sig").strip()
    lines = [ln.strip() for ln in script.splitlines() if ln.strip()]
    post = " ".join(lines[:3])[:500] if lines else "B2B SaaS infographic"
    direction = STYLE_PREFIX + script

    content = build_napkin_content(post, direction, args.format)
    print(f"Style: {args.style}")
    print(f"Format: {args.format}")
    print(f"Prompt file: {prompt_path}")
    print("Calling Napkin (may take 30-120s)...")

    with requests.Session() as session:
        raw = generate_napkin_bytes(content, args.format, args.style, session, token)

    if args.raw_png:
        out = pathlib.Path(args.out) if args.out else None
        if not out:
            DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = DEFAULT_OUT_DIR / f"{slug_from_path(prompt_path)}_{stamp}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        print(f"Saved: {out}")
        return 0

    jpeg = resize_for_linkedin_fit(raw, args.format)
    out = pathlib.Path(args.out) if args.out else None
    if not out:
        DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = DEFAULT_OUT_DIR / f"{slug_from_path(prompt_path)}_{stamp}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(jpeg)
    print(f"Saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
