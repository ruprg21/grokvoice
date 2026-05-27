"""
Google Sheets -> xAI LinkedIn images -> Google Drive

Sheet layout (row 1 = header):
  A: post           LinkedIn post copy
  B: format         landscape or square
  C: approved       TRUE / YES / 1 to trigger
  D: status         auto-filled (processing, done, error: ...)
  E: drive_file_id  Google Drive file ID after upload
  F: image_style      preset name (optional, default b2b_clean) — see STYLE_PRESETS
  G: image_prompt     auto-filled: final prompt sent to image model
  H: image_direction  optional per-post visual brief (1-2 sentences, not the LinkedIn post)
  I: drive_url        auto-filled: https://drive.google.com/file/d/.../view link

Setup: see CLAUDE.md section 4 (LinkedIn post images)

Run (batch — processes all eligible rows once, then exits):
  python linkedin_images_watcher.py
"""

import base64
import io
import os
import pathlib
import time
from datetime import datetime

import gspread
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image, ImageStat

# -- Config -------------------------------------------------------------------
PROJECT_DIR = pathlib.Path(__file__).parent
SHEET_ID = "1ybagJYYkRFqWlwRTvwWiEEi6tIve5btWt8uBAW2Tsvg"
WORKSHEET_NAME = "Image Library"
DRIVE_FOLDER_ID = "18emOBgPL8Wovn1TxqQpnxiTGOBI0kmjA"
# oauth = personal Gmail My Drive (no Workspace). service_account = Shared Drive only.
DRIVE_AUTH = "oauth"
CLIENT_SECRETS_FILE = PROJECT_DIR / "client_secret.json"
DRIVE_TOKEN_FILE = PROJECT_DIR / "drive_token.json"

COL_POST = 1
COL_FORMAT = 2
COL_APPROVED = 3
COL_STATUS = 4
COL_DRIVE_FILE_ID = 5
COL_IMAGE_STYLE = 6
COL_IMAGE_PROMPT = 7
COL_IMAGE_DIRECTION = 8
COL_DRIVE_URL = 9

DEFAULT_IMAGE_STYLE = "b2b_clean"
DRIVE_VIEW_URL = "https://drive.google.com/file/d/{file_id}/view"

DONE_STATES = {"done", "processing"}
IMAGE_MODEL = "grok-imagine-image-quality"
CHAT_MODEL = "grok-3"

LINKEDIN_SIZES = {
    "landscape": (1200, 627),
    "square": (1080, 1080),
}
ASPECT_RATIOS = {
    "landscape": "16:9",
    "square": "1:1",
}

# Pick one in sheet column F (image_style). Keys are case-insensitive.
STYLE_PRESETS = {
    "b2b_clean": {
        "label": "B2B clean — default LinkedIn marketing look",
        "chat_system": (
            "You write image prompts for LinkedIn B2B feed ads. "
            "One concise prompt, max 2 sentences. "
            "Show a clear focal subject, generous negative space on the left third for mobile UI, "
            "soft corporate lighting, navy/teal/white palette, modern and trustworthy. "
            "No text, logos, watermarks, UI screenshots with readable words, or busy collages. "
            "Output only the image prompt."
        ),
        "imagine_suffix": (
            "LinkedIn B2B marketing image, premium corporate photography style, "
            "shallow depth of field, uncluttered composition, no text."
        ),
    },
    "executive_photo": {
        "label": "Executive / workplace photo",
        "chat_system": (
            "You write image prompts for LinkedIn thought-leadership posts. "
            "One concise prompt, max 2 sentences. "
            "Realistic professional setting: modern office, collaboration, leadership, diversity. "
            "Editorial stock-photo quality, natural light, authentic not cheesy. "
            "No text, logos, or watermarks. Output only the image prompt."
        ),
        "imagine_suffix": (
            "Professional editorial photograph for LinkedIn, photorealistic, "
            "natural lighting, 85mm lens look, no text."
        ),
    },
    "gradient_abstract": {
        "label": "Abstract gradient (native LinkedIn graphic)",
        "chat_system": (
            "You write image prompts for LinkedIn posts that use abstract brand graphics. "
            "One concise prompt, max 2 sentences. "
            "Smooth gradients, subtle geometric shapes, 2-3 brand colors derived from the post theme, "
            "minimal and elegant, large calm areas, no literal scenes. "
            "No text or logos. Output only the image prompt."
        ),
        "imagine_suffix": (
            "Abstract LinkedIn banner graphic, smooth gradient mesh, minimal geometric accents, "
            "modern SaaS aesthetic, no text, no people."
        ),
    },
    "saas_ui": {
        "label": "SaaS product / dashboard (no readable text)",
        "chat_system": (
            "You write image prompts for LinkedIn posts about software products. "
            "One concise prompt, max 2 sentences. "
            "Suggest a blurred or angled laptop/phone showing a generic dashboard UI with "
            "unreadable placeholder blocks only — never legible text. "
            "Clean desk, subtle glow, trustworthy tech brand feel. Output only the image prompt."
        ),
        "imagine_suffix": (
            "SaaS product marketing visual for LinkedIn, device mockup, UI with blurred placeholder "
            "content only, crisp and modern, no legible text."
        ),
    },
    "concept_metaphor": {
        "label": "Single strong metaphor",
        "chat_system": (
            "You write image prompts for LinkedIn posts using ONE simple visual metaphor "
            "for the post idea (e.g. bridge for connection, lighthouse for guidance). "
            "One concise prompt, max 2 sentences. Symbolic but professional, not childish fantasy. "
            "Centered subject, simple background. No text or logos. Output only the image prompt."
        ),
        "imagine_suffix": (
            "Conceptual LinkedIn illustration, single bold metaphor, clean background, "
            "professional tone, no text."
        ),
    },
    "stats_visual": {
        "label": "Data / growth visual (no labels)",
        "chat_system": (
            "You write image prompts for LinkedIn posts about metrics, growth, or analytics. "
            "One concise prompt, max 2 sentences. "
            "Abstract charts, rising curves, bar shapes without numbers or labels, "
            "corporate color palette, optimistic and clear. No text or logos. Output only the image prompt."
        ),
        "imagine_suffix": (
            "Abstract data visualization for LinkedIn, glowing charts without numbers or labels, "
            "dark or navy background, no text."
        ),
    },
}

# Napkin AI — infographics / diagrams (column F). Requires NAPKIN_API_TOKEN in grokapi.env
NAPKIN_API_BASE = "https://api.napkin.ai"
NAPKIN_POLL_INTERVAL = 3
NAPKIN_POLL_MAX_WAIT = 180

NAPKIN_STYLE_PRESETS = {
    "napkin": {
        "label": "Napkin infographic — corporate diagram (default)",
        "style_id": "CSQQ4VB1DGPPTVVEDXHPGWKFDNJJTSKCC5T0",  # Corporate Clean
    },
    "napkin_corporate": {
        "label": "Napkin — corporate clean diagrams",
        "style_id": "CSQQ4VB1DGPPTVVEDXHPGWKFDNJJTSKCC5T0",
    },
    "napkin_elegant": {
        "label": "Napkin — elegant outline",
        "style_id": "CSQQ4VB1DGPP4V31CDNJTVKFBXK6JV3C",
    },
    "napkin_sketch": {
        "label": "Napkin — hand-drawn sketch notes",
        "style_id": "D1GPWS1DDHMPWSBK",
    },
}

NAPKIN_ALIASES = {
    "diagram": "napkin",
    "infographic": "napkin",
    "napkin_diagram": "napkin",
}

STYLE_ALIASES = {
    "professional": "b2b_clean",
    "b2b": "b2b_clean",
    "clean": "b2b_clean",
    "corporate": "executive_photo",
    "photo": "executive_photo",
    "workplace": "executive_photo",
    "gradient": "gradient_abstract",
    "abstract": "gradient_abstract",
    "ui": "saas_ui",
    "saas": "saas_ui",
    "dashboard": "saas_ui",
    "metaphor": "concept_metaphor",
    "concept": "concept_metaphor",
    "data": "stats_visual",
    "stats": "stats_visual",
    "analytics": "stats_visual",
}

# drive (not drive.file) so uploads work to folders shared with the service account
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

SHARED_DRIVE_REQUIRED_MSG = (
    "Drive upload failed: service accounts cannot store files in personal My Drive. "
    "Without Google Workspace, set DRIVE_AUTH = 'oauth' and run: python setup_drive_oauth.py "
    "See LINKEDIN_IMAGES.md."
)
# -----------------------------------------------------------------------------


def api_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def connect_sheet():
    sa_file = PROJECT_DIR / "service_account.json"
    if not sa_file.exists():
        raise SystemExit("Error: service_account.json not found in project folder.")
    gc = gspread.service_account(filename=str(sa_file))
    return gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)


def connect_drive_oauth():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as UserCredentials

    if not DRIVE_TOKEN_FILE.exists():
        if CLIENT_SECRETS_FILE.exists():
            raise SystemExit(
                "Error: drive_token.json missing. Run once: python setup_drive_oauth.py"
            )
        raise SystemExit(
            "Error: for personal Gmail Drive, add client_secret.json and run:\n"
            "  python setup_drive_oauth.py\n"
            "See LINKEDIN_IMAGES.md (Personal Gmail - OAuth)."
        )
    creds = UserCredentials.from_authorized_user_file(str(DRIVE_TOKEN_FILE), DRIVE_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        DRIVE_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def connect_drive_service_account():
    sa_file = PROJECT_DIR / "service_account.json"
    creds = Credentials.from_service_account_file(str(sa_file), scopes=DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def connect_drive() -> tuple:
    """Returns (drive_service, uses_oauth)."""
    if DRIVE_AUTH == "oauth":
        return connect_drive_oauth(), True
    if DRIVE_AUTH == "service_account":
        return connect_drive_service_account(), False
    raise SystemExit("Error: DRIVE_AUTH must be 'oauth' or 'service_account'")


def verify_drive_folder(drive_service, uses_oauth: bool) -> None:
    folder = (
        drive_service.files()
        .get(
            fileId=DRIVE_FOLDER_ID,
            fields="id,name,driveId",
            supportsAllDrives=True,
        )
        .execute()
    )
    name = folder.get("name", "?")
    if uses_oauth:
        print(f"Drive folder OK (your My Drive): {name}")
        return
    if folder.get("driveId"):
        print(f"Drive folder OK (Shared Drive): {name}")
        return
    raise SystemExit(
        f"Error: folder '{name}' is in My Drive, not a Shared Drive.\n"
        f"{SHARED_DRIVE_REQUIRED_MSG}"
    )


def is_approved(value: str) -> bool:
    return value.strip().upper() in ("TRUE", "YES", "1")


def normalize_format(value: str) -> str | None:
    fmt = value.strip().lower()
    if fmt in LINKEDIN_SIZES:
        return fmt
    return None


def _style_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def resolve_style(value: str) -> tuple[str, str]:
    """Return (engine, style_key) where engine is 'grok' or 'napkin'."""
    key = _style_key(value)
    if not key:
        return "grok", DEFAULT_IMAGE_STYLE
    if key in NAPKIN_STYLE_PRESETS:
        return "napkin", key
    if key in NAPKIN_ALIASES:
        return "napkin", NAPKIN_ALIASES[key]
    if key in STYLE_PRESETS:
        return "grok", key
    if key in STYLE_ALIASES:
        return "grok", STYLE_ALIASES[key]
    return "grok", DEFAULT_IMAGE_STYLE


def _known_style_input(value: str) -> bool:
    key = _style_key(value)
    return (
        key in NAPKIN_STYLE_PRESETS
        or key in NAPKIN_ALIASES
        or key in STYLE_PRESETS
        or key in STYLE_ALIASES
    )


def list_style_presets() -> str:
    lines = ["Available image_style values (column F):", "", "Grok (xAI):"]
    for key, preset in STYLE_PRESETS.items():
        lines.append(f"  {key} — {preset['label']}")
    lines.append("")
    lines.append("Napkin (diagrams / infographics — needs NAPKIN_API_TOKEN):")
    for key, preset in NAPKIN_STYLE_PRESETS.items():
        if key == "napkin_corporate":
            continue
        lines.append(f"  {key} — {preset['label']}")
    lines.append("  diagram / infographic — alias for napkin")
    return "\n".join(lines)


def napkin_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def build_napkin_content(post: str, direction: str, fmt: str) -> str:
    parts = []
    if direction.strip():
        parts.append(f"Visual direction:\n{direction.strip()[:2000]}")
    parts.append(f"Topic (LinkedIn post):\n{post[:4000]}")
    if fmt == "landscape":
        parts.append(
            "Layout: wide horizontal infographic (~1.9:1 aspect), not tall/portrait. "
            "Spread content left-to-right; hub-and-spoke or flow with clear labels."
        )
    else:
        parts.append(
            "Layout: square infographic (~1:1). "
            "Balanced diagram with labels; avoid extra-tall vertical layout."
        )
    return "\n\n".join(parts)


def napkin_png_dimensions(fmt: str) -> dict:
    """Napkin ignores height when width is set — use one dimension per format."""
    target_w, target_h = LINKEDIN_SIZES[fmt]
    if fmt == "landscape":
        # Tall infographics at width=1200 get center-cropped; prefer height for 16:9
        return {"height": target_h}
    return {"width": target_w}


def generate_napkin_bytes(
    content: str,
    fmt: str,
    napkin_style_key: str,
    session: requests.Session,
    napkin_token: str,
) -> bytes:
    preset = NAPKIN_STYLE_PRESETS[napkin_style_key]
    body = {
        "format": "png",
        "content": content,
        "style_id": preset["style_id"],
        "language": "en-US",
        "number_of_visuals": 1,
        "transparent_background": False,
        **napkin_png_dimensions(fmt),
    }
    create = session.post(
        f"{NAPKIN_API_BASE}/v1/visual",
        headers=napkin_headers(napkin_token),
        json=body,
        timeout=90,
    )
    create.raise_for_status()
    data = create.json()
    request_id = data.get("id") or data.get("request_id")
    if not request_id:
        raise ValueError(f"Napkin create response missing id: {data}")

    elapsed = 0
    while elapsed < NAPKIN_POLL_MAX_WAIT:
        status_resp = session.get(
            f"{NAPKIN_API_BASE}/v1/visual/{request_id}/status",
            headers=napkin_headers(napkin_token),
            timeout=60,
        )
        status_resp.raise_for_status()
        st = status_resp.json()
        status = (st.get("status") or "").lower()
        if status in ("completed", "complete", "done", "success"):
            files = st.get("generated_files") or st.get("files") or []
            if not files:
                raise ValueError("Napkin completed but no generated_files")
            file_info = files[0]
            file_id = file_info.get("id")
            download_url = file_info.get("url") or file_info.get("download_url")
            if download_url:
                dl = session.get(
                    download_url, headers=napkin_headers(napkin_token), timeout=120
                )
            elif file_id:
                dl = session.get(
                    f"{NAPKIN_API_BASE}/v1/visual/{request_id}/file/{file_id}",
                    headers=napkin_headers(napkin_token),
                    timeout=120,
                )
            else:
                raise ValueError(f"Napkin file entry missing url/id: {file_info}")
            dl.raise_for_status()
            return dl.content
        if status in ("failed", "error"):
            raise RuntimeError(st.get("error") or st.get("message") or "Napkin failed")
        time.sleep(NAPKIN_POLL_INTERVAL)
        elapsed += NAPKIN_POLL_INTERVAL
    raise TimeoutError(f"Napkin visual timed out after {NAPKIN_POLL_MAX_WAIT}s")


def build_image_prompt(
    post: str,
    style_key: str,
    direction: str,
    api_key: str,
    session: requests.Session,
) -> str:
    preset = STYLE_PRESETS[style_key]
    user_parts = [f"LinkedIn post (caption context, not the image prompt itself):\n{post[:2000]}"]
    if direction.strip():
        user_parts.append(
            "Art direction for this image (follow closely):\n" + direction.strip()[:1000]
        )
    user_parts.append("Write the image prompt for this post.")
    resp = session.post(
        "https://api.x.ai/v1/chat/completions",
        headers=api_headers(api_key),
        json={
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": preset["chat_system"]},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
            "max_tokens": 180,
        },
        timeout=60,
    )
    resp.raise_for_status()
    scene = resp.json()["choices"][0]["message"]["content"].strip()
    return f"{scene} {preset['imagine_suffix']}"


def row_needs_processing(row: list) -> tuple[bool, str]:
    if len(row) < 3:
        return False, "missing columns"
    post = row[0].strip() if len(row) > 0 else ""
    fmt = row[1].strip() if len(row) > 1 else ""
    approved = row[2].strip() if len(row) > 2 else ""
    status = row[3].strip() if len(row) > 3 else ""
    file_id = row[4].strip() if len(row) > 4 else ""

    if not post:
        return False, "empty post"
    if not is_approved(approved):
        return False, "not approved"
    if file_id:
        return False, "already has drive_file_id"
    if status in DONE_STATES:
        return False, f"status is {status}"
    if status.startswith("error"):
        return False, "previous error"
    if not normalize_format(fmt):
        return False, "invalid format"
    return True, ""


def fetch_image_bytes(url_or_b64: str, session: requests.Session) -> bytes:
    if url_or_b64.startswith("http"):
        r = session.get(url_or_b64, timeout=120)
        r.raise_for_status()
        return r.content
    return base64.b64decode(url_or_b64)


def generate_image_bytes(
    prompt: str, fmt: str, api_key: str, session: requests.Session
) -> bytes:
    resp = session.post(
        "https://api.x.ai/v1/images/generations",
        headers=api_headers(api_key),
        json={
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "aspect_ratio": ASPECT_RATIOS[fmt],
            "resolution": "2k",
        },
        timeout=180,
    )
    resp.raise_for_status()
    item = resp.json()["data"][0]
    url_or_b64 = item.get("url") or item.get("b64_json")
    if not url_or_b64:
        raise ValueError("No image URL or b64_json in API response")
    return fetch_image_bytes(url_or_b64, session)


def resize_for_linkedin(image_bytes: bytes, fmt: str) -> bytes:
    """Center-crop to aspect ratio, then scale (used for Grok photos)."""
    target_w, target_h = LINKEDIN_SIZES[fmt]
    target_ratio = target_w / target_h

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_ratio < target_ratio:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def sample_edge_background(img: Image.Image) -> tuple[int, int, int]:
    """Average RGB from outer edge strips so letterbox matches Napkin canvas color."""
    w, h = img.size
    strip = max(1, min(12, w // 20, h // 20))
    edge_parts = (
        img.crop((0, 0, strip, h)),
        img.crop((w - strip, 0, w, h)),
        img.crop((0, 0, w, strip)),
        img.crop((0, h - strip, w, h)),
    )
    r_sum = g_sum = b_sum = 0
    pixel_count = 0
    for part in edge_parts:
        st = ImageStat.Stat(part)
        n = part.size[0] * part.size[1]
        r_sum += st.mean[0] * n
        g_sum += st.mean[1] * n
        b_sum += st.mean[2] * n
        pixel_count += n
    return (
        int(r_sum / pixel_count),
        int(g_sum / pixel_count),
        int(b_sum / pixel_count),
    )


def resize_for_linkedin_fit(image_bytes: bytes, fmt: str) -> bytes:
    """Scale to fit inside LinkedIn box with letterboxing (no crop). For Napkin diagrams."""
    target_w, target_h = LINKEDIN_SIZES[fmt]
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    bg = sample_edge_background(img)
    scale = min(target_w / w, target_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), bg)
    canvas.paste(img, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def upload_to_drive(jpeg_bytes: bytes, filename: str, drive_service) -> str:
    metadata = {"name": filename, "parents": [DRIVE_FOLDER_ID]}
    media = MediaIoBaseUpload(io.BytesIO(jpeg_bytes), mimetype="image/jpeg", resumable=True)
    try:
        created = (
            drive_service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        err = str(e)
        if e.resp.status == 403 and (
            "storageQuota" in err or "storage quota" in err.lower()
        ):
            raise RuntimeError(SHARED_DRIVE_REQUIRED_MSG) from e
        raise
    file_id = created.get("id")
    if not file_id:
        raise ValueError("Drive upload succeeded but no file id returned")
    return file_id


def drive_view_url(file_id: str) -> str:
    return DRIVE_VIEW_URL.format(file_id=file_id.strip())


def process_row(
    ws,
    row_index: int,
    row: list,
    api_key: str,
    session: requests.Session,
    drive_service,
) -> None:
    post = row[0].strip()
    fmt = normalize_format(row[1].strip())
    style_raw = row[5].strip() if len(row) > 5 else ""
    direction = row[7].strip() if len(row) > 7 else ""
    engine, style_key = resolve_style(style_raw)
    if not fmt:
        ws.update_cell(row_index, COL_STATUS, "error: format must be landscape or square")
        return

    ws.update_cell(row_index, COL_STATUS, "processing")
    if style_raw and not _known_style_input(style_raw):
        print(f"[row {row_index}] Unknown style {style_raw!r}, using grok {DEFAULT_IMAGE_STYLE}")
        engine, style_key = "grok", DEFAULT_IMAGE_STYLE
    dir_note = " + direction" if direction else ""
    print(f"[row {row_index}] Processing ({fmt}, {engine}/{style_key}{dir_note})...")

    try:
        if engine == "napkin":
            napkin_token = os.environ.get("NAPKIN_API_TOKEN", "").strip()
            if not napkin_token:
                raise RuntimeError(
                    "NAPKIN_API_TOKEN not set. Add to grokapi.env (Napkin account > Developers)."
                )
            napkin_content = build_napkin_content(post, direction, fmt)
            ws.update_cell(
                row_index,
                COL_IMAGE_PROMPT,
                f"[Napkin {style_key}]\n{napkin_content[:50000]}",
            )
            print(f"[row {row_index}] Napkin content: {napkin_content[:100]}...")
            raw_bytes = generate_napkin_bytes(
                napkin_content, fmt, style_key, session, napkin_token
            )
            napkin_img = Image.open(io.BytesIO(raw_bytes))
            print(f"[row {row_index}] Napkin PNG: {napkin_img.size[0]}x{napkin_img.size[1]}")
            jpeg_bytes = resize_for_linkedin_fit(raw_bytes, fmt)
        else:
            full_prompt = build_image_prompt(post, style_key, direction, api_key, session)
            ws.update_cell(row_index, COL_IMAGE_PROMPT, full_prompt[:50000])
            print(f"[row {row_index}] Prompt: {full_prompt[:120]}...")
            raw_bytes = generate_image_bytes(full_prompt, fmt, api_key, session)
            jpeg_bytes = resize_for_linkedin(raw_bytes, fmt)
        w, h = LINKEDIN_SIZES[fmt]
        print(f"[row {row_index}] LinkedIn output: {w}x{h}")

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_row_{row_index}_{stamp}.jpg"
        file_id = upload_to_drive(jpeg_bytes, filename, drive_service)
        file_url = drive_view_url(file_id)
        print(f"[row {row_index}] Uploaded: {filename} (id: {file_id})")
        print(f"[row {row_index}] Drive URL: {file_url}")

        ws.update_cell(row_index, COL_DRIVE_FILE_ID, file_id)
        ws.update_cell(row_index, COL_DRIVE_URL, file_url)
        ws.update_cell(row_index, COL_STATUS, "done")
    except requests.HTTPError as e:
        msg = e.response.text if e.response is not None else str(e)
        ws.update_cell(row_index, COL_STATUS, f"error: API {e.response.status_code}: {msg[:200]}")
        print(f"[row {row_index}] API error: {msg[:200]}")
    except Exception as e:
        ws.update_cell(row_index, COL_STATUS, f"error: {e}")
        print(f"[row {row_index}] Error: {e}")


ENV_FILES = ("grokapi.env", ".env", ".env.example")


def load_env_file():
    """Load grokapi.env, .env, or .env.example (first found). Does not override existing vars."""
    env_file = None
    for name in ENV_FILES:
        candidate = PROJECT_DIR / name
        if candidate.exists():
            env_file = candidate
            break
    if env_file is None:
        return
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def validate_config():
    if SHEET_ID == "YOUR_SHEET_ID_HERE":
        raise SystemExit("Error: set SHEET_ID in linkedin_images_watcher.py before running.")
    if DRIVE_FOLDER_ID == "YOUR_DRIVE_FOLDER_ID_HERE":
        raise SystemExit("Error: set DRIVE_FOLDER_ID in linkedin_images_watcher.py before running.")


def run_batch(ws, drive_service, api_key: str) -> int:
    """Process every eligible row once. Returns count processed."""
    try:
        rows = ws.get_all_values()
    except gspread.exceptions.APIError as e:
        raise SystemExit(f"Error reading sheet: {e}") from e
    except requests.RequestException as e:
        raise SystemExit(f"Error reading sheet (network): {e}") from e

    pending = [
        (i, row)
        for i, row in enumerate(rows[1:], start=2)
        if row_needs_processing(row)[0]
    ]

    if not pending:
        print("No rows to process (need post + format + approved=TRUE + empty file ID).")
        return 0

    print(f"Batch: {len(pending)} row(s) on '{WORKSHEET_NAME}'.\n")
    with requests.Session() as session:
        for i, row in pending:
            process_row(ws, i, row, api_key, session, drive_service)

    print(f"\nBatch finished. Processed {len(pending)} row(s).")
    return len(pending)


def main():
    load_env_file()
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: XAI_API_KEY not set.")

    validate_config()
    ws = connect_sheet()
    drive_service, uses_oauth = connect_drive()
    verify_drive_folder(drive_service, uses_oauth)

    run_batch(ws, drive_service, api_key)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list-styles":
        print(list_style_presets())
    else:
        main()
