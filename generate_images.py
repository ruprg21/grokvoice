"""
Script → xAI Grok Imagine image generator

Reads a .txt script, splits into sections by --- dividers,
uses grok chat to craft a visual prompt for each section,
then generates one image per section with grok-imagine.

Usage:
  $env:XAI_API_KEY = "xai-..."
  python generate_images.py script1.txt
"""

import pathlib, re, sys, os
import requests

# ── Visual style applied to every image ──────────────────────────────────────
STYLE = (
    "Cinematic documentary aesthetic. "
    "Dramatic lighting — golden hour sunlight or flickering torchlight. "
    "Painterly, epic historical illustration style. "
    "Rich warm tones: ochre, deep red, burnt sienna, gold. "
    "Ancient South India setting. "
    "No text, no watermarks, no captions, no writing."
)

PROMPT_SYSTEM = (
    "You are a visual art director for a cinematic documentary about ancient Indian history. "
    "Given a section of narration, write ONE concise image prompt (max 2 sentences, under 200 words) "
    "capturing the most visually striking moment. "
    "Style: cinematic documentary, dramatic golden hour or torchlight, painterly epic historical illustration, "
    "rich warm tones of ochre deep red and gold, ancient South Indian setting, no text no watermarks. "
    "Output only the image prompt, nothing else."
)
# ─────────────────────────────────────────────────────────────────────────────


def headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def chat_to_prompt(section_text: str, api_key: str, session: requests.Session) -> str:
    resp = session.post(
        "https://api.x.ai/v1/chat/completions",
        headers=headers(api_key),
        json={
            "model": "grok-3",
            "messages": [
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user",   "content": section_text[:2000]},
            ],
            "max_tokens": 180,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate_image(prompt: str, api_key: str, session: requests.Session) -> str:
    resp = session.post(
        "https://api.x.ai/v1/images/generations",
        headers=headers(api_key),
        json={"model": "grok-imagine-image-quality", "prompt": prompt},
        timeout=120,
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
        import base64
        dest.write_bytes(base64.b64decode(url_or_b64))


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else "script1.txt"
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: XAI_API_KEY not set.")

    raw = pathlib.Path(input_file).read_text(encoding="utf-8")

    # Split by --- section dividers, drop empty
    sections = [s.strip() for s in re.split(r"^---+\s*$", raw, flags=re.MULTILINE)]
    sections = [s for s in sections if s]
    print(f"Found {len(sections)} sections in {input_file}\n")

    out_dir = pathlib.Path(pathlib.Path(input_file).stem + "_images")
    out_dir.mkdir(exist_ok=True)
    log_lines = []

    with requests.Session() as session:
        for i, section in enumerate(sections, start=1):
            print(f"[{i}/{len(sections)}] Crafting prompt from section...")
            try:
                scene_prompt = chat_to_prompt(section, api_key, session)
                print(f"  Prompt: {scene_prompt[:120]}...")

                print(f"  Generating image with grok-imagine-image-quality...")
                result = generate_image(scene_prompt, api_key, session)
                ext    = "jpeg" if result.endswith(".jpeg") else "jpg"

                img_path = out_dir / f"section_{i:02d}.{ext}"
                save_image(result, img_path, session)
                print(f"  Saved: {img_path}\n")

                log_lines.append(f"--- Section {i} ---\n{scene_prompt}\n")

            except requests.HTTPError as e:
                msg = e.response.text if e.response else str(e)
                print(f"  API error {e.response.status_code}: {msg}\n")
                log_lines.append(f"--- Section {i} --- ERROR: {msg}\n")
            except Exception as e:
                print(f"  Error: {e}\n")
                log_lines.append(f"--- Section {i} --- ERROR: {e}\n")

    # Save prompt log so you can review / tweak
    log_path = out_dir / "prompts_log.txt"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Done. Images + prompt log saved to ./{out_dir}/")


if __name__ == "__main__":
    main()
