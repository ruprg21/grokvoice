# xAI Voice, Image & Video — Chronicles of Indus YouTube Pipeline

## Project Goal
Build a full YouTube content pipeline using xAI APIs: TTS voiceover, AI image generation, and AI video generation.
User: Rupesh (ruprg21@gmail.com) — GitHub: https://github.com/ruprg21/grokvoice

## Pipelines in this repo

This repo holds **multiple workflows**. They share `grokapi.env` / `XAI_API_KEY` but use different scripts and outputs.

| Pipeline | Branch (typical) | Scripts | Output |
|----------|------------------|---------|--------|
| **Chronicles of Indus — YouTube** | `main` | `generate*.py`, `images_from_prompts.py`, `videos_from_prompts.py`, `watcher.py` | MP3, JPG, MP4 in project folders |
| **LinkedIn images** | `linkedin-grok` | `linkedin_images_watcher.py`, `setup_drive_oauth.py` | JPEG on Google Drive + sheet columns E, I, G |
| **Notebook sketchnote** | `linkedin-grok` | `grok_notebook_sketch.py` | Local JPG in `notebook_sketches/` |
| **X (Twitter) research** | `linkedin-grok` | `grok_x_query.py` | `.txt` reports in `x_query_outputs/` |

**Quick doc index:** [SCRIPTS.md](SCRIPTS.md) (all commands) · §§1–3 YouTube · §4 LinkedIn · §5 X search · §6 notebook · [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md) · [GROK_X_QUERY.md](GROK_X_QUERY.md) · [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md)

**Prompt template (git):** `notebook_sketches/headless_crm_signal_prompt.txt` — style block + section copy for sketchnotes.

## Platform
- **Python 3.14** — all scripts use Python (Node.js not installed)
- **Auth:** Bearer token via env var `XAI_API_KEY` (file `grokapi.env` in project root; see §4 and §5)
- **Optional:** `NAPKIN_API_TOKEN` in `grokapi.env` for LinkedIn column F = Napkin styles
- **Key rule:** Always use `requests.Session()` — urllib gets blocked by Cloudflare on xAI endpoints

---

## Scripts

| Script | Purpose | Run command |
|--------|---------|-------------|
| `generate.py` | Single script TTS → MP3 | `python generate.py script1.txt` |
| `generate_batch.py` | Multiple scripts → MP3s | `python generate_batch.py <folder> file1.txt file2.txt ...` |
| `generate_images.py` | Script file → images (uses grok-3 to craft prompts) | `python generate_images.py script1.txt` |
| `images_from_prompts.py` | Prompts txt → images | `python images_from_prompts.py prompts.txt output_folder` |
| `videos_from_prompts.py` | Prompts txt → videos (text-to-video or image-to-video) | `python videos_from_prompts.py prompts.txt output_folder` |
| `watcher.py` | Google Sheet → TTS polling (YouTube; set `SHEET_ID` in script) | `python watcher.py` |
| `linkedin_images_watcher.py` | Sheet → LinkedIn images → Drive (batch) | `python linkedin_images_watcher.py` |
| `setup_drive_oauth.py` | One-time Drive OAuth (personal Gmail) | `python setup_drive_oauth.py` |
| `check_linkedin_setup.py` | Verify sheet + Drive + API setup | `python check_linkedin_setup.py` |
| `check_linkedin_credentials.py` | Light check (API key + service account only) | `python check_linkedin_credentials.py` |
| `grok_notebook_sketch.py` | Notebook sketchnote JPG (standalone, no sheet) | `python grok_notebook_sketch.py --prompt-file notebook_sketches\prompt.txt` |
| `grok_x_query.py` | X sentiment / research via Grok `x_search` | `python grok_x_query.py "Your question"` |

**All scripts:** [SCRIPTS.md](SCRIPTS.md)

---

## 1. Audio — TTS API

- **Endpoint:** `POST https://api.x.ai/v1/tts`
- **Output:** MP3 saved alongside the script file

### Default Voice Settings
```json
{
  "voice_id": "leo",
  "language": "en",
  "output_format": { "codec": "mp3", "sample_rate": 44100, "bit_rate": 128000 }
}
```

### Voices Available
| Voice | Personality |
|-------|-------------|
| `leo` | Authoritative & strong — current default |
| `eve` | Energetic & upbeat |
| `ara` | Warm & friendly |
| `rex` | Confident & clear |
| `sal` | Smooth & balanced |

### Speech Tags
**Inline:** `[pause]` `[long-pause]` `[laugh]` `[chuckle]` `[breath]` `[sigh]`

**Wrapping:** `<soft>` `<whisper>` `<loud>` `<build-intensity>` `<decrease-intensity>`
`<higher-pitch>` `<lower-pitch>` `<slow>` `<fast>` `<emphasis>`

---

## 2. Images — grok-imagine API

- **Endpoint:** `POST https://api.x.ai/v1/images/generations`
- **Model:** `grok-imagine-image-quality`
- **Output:** JPEG saved to specified folder

### Request
```python
session.post("https://api.x.ai/v1/images/generations",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={"model": "grok-imagine-image-quality", "prompt": prompt},
    timeout=180)
# Response: data[0].url or data[0].b64_json
```

### Prompts file format (`images_from_prompts.py`)
One prompt per section, separated by `---`:
```
Wide establishing shot of ancient Tamil seaport at sunrise...
---
Silhouette of Chola king on fortress wall overlooking warfleet...
```

---

## 3. Video — grok-imagine-video API

- **Endpoint:** `POST https://api.x.ai/v1/videos/generations` (async)
- **Poll:** `GET https://api.x.ai/v1/videos/{request_id}`
- **Model:** `grok-imagine-video`
- **Output:** MP4 downloaded from temporary hosted URL
- **Processing time:** ~90–135 seconds per clip

### Text-to-Video Request
```python
session.post("https://api.x.ai/v1/videos/generations",
    json={
        "model": "grok-imagine-video",
        "prompt": prompt,
        "duration": 10,        # 1–15 seconds
        "resolution": "720p",  # or 480p
        "aspect_ratio": "16:9"
    }, timeout=300)
# Response: {"request_id": "..."}
```

### Image-to-Video Request (animate an existing image)
```python
import base64
img_b64 = base64.b64encode(img_path.read_bytes()).decode()

session.post("https://api.x.ai/v1/videos/generations",
    json={
        "model": "grok-imagine-video",
        "prompt": "slow cinematic zoom, warships rocking on waves...",
        "image": {"url": f"data:image/jpeg;base64,{img_b64}"},  # <-- object format required
        "duration": 8,
        "resolution": "720p",
        "aspect_ratio": "16:9"
    }, timeout=300)
```

### Polling
```python
result = session.get(f"https://api.x.ai/v1/videos/{request_id}", ...).json()
# result["status"] → "pending" | "done" | "failed"
# result["video"]["url"] → download URL when done
```

### Prompts file format (`videos_from_prompts.py`)
Per-prompt settings appended with `|`. Image path is relative to the prompts file folder:
```
Slow aerial pullback over the Strait of Malacca... | duration: 10 | aspect_ratio: 16:9 | resolution: 720p
---
Slow cinematic zoom into the silhouetted king... | image: image_04.jpg | duration: 8 | aspect_ratio: 16:9 | resolution: 720p
```

**Auto-numbering:** Script finds the highest existing `video_NN.mp4` in the output folder and continues from there — never overwrites. Images and videos are numbered in separate independent sequences (`image_01`, `image_02` … and `video_01`, `video_02` …). At no point should any file be overwritten.

---

## 4. LinkedIn post images — Google Sheets + Grok + Drive

**Script:** `linkedin_images_watcher.py` — **batch mode** (one run, processes all eligible rows, then exits).

**Docs:** [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md) · [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md) · [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md)

### What it does

For each approved row on tab **Image Library** (engine chosen by column **F**):

**Grok styles** (`b2b_clean`, `saas_ui`, etc.):

1. **grok-3** builds an image prompt from post + preset + optional **H**
2. **grok-imagine-image-quality** generates the image
3. Resizes to LinkedIn pixels, uploads to Drive, writes **E** + **G**

**Napkin styles** (`napkin`, `diagram`, `napkin_sketch`, etc.):

1. Sends post + **H** to [Napkin API](https://api.napkin.ai/) for an infographic/diagram (landscape: `height: 627` only; square: `width: 1080`)
2. Letterbox-fits PNG to LinkedIn pixels (edge-matched padding), uploads to Drive, writes **E** + **I** + **G**

**Notebook sketchnote** (`notebook_sketch` in F):

1. Builds full grok-imagine prompt from **H** (long outline) or grok-3 draft from **A** + **H**
2. Grok Imagine draws lined-notebook sketchnote (lime green headers, sections, CTA)
3. Letterbox-fits to LinkedIn size, uploads to Drive, writes **E** + **I** + **G**

Standalone test (no sheet): `python grok_notebook_sketch.py --prompt-file notebook_sketches\your_prompt.txt`

### Google Sheet columns (row 1 = headers)

| Col | Field | You fill? | Description |
|-----|--------|-----------|-------------|
| **A** | `post` | Yes | LinkedIn **caption** — not an image prompt |
| **B** | `format` | Yes | `landscape` or `square` (case-insensitive) |
| **C** | `approved` | Yes | `TRUE` / `YES` / `1` to include in batch |
| **D** | `status` | Auto | `processing`, `done`, or `error: ...` |
| **E** | `drive_file_id` | Auto | Google Drive file ID after upload |
| **I** | `drive_url` | Auto | Drive view link (`https://drive.google.com/file/d/.../view`) |
| **F** | `image_style` | Optional | Style preset (default `b2b_clean` if empty) |
| **G** | `image_prompt` | Auto | Full prompt sent to image model (review/debug) |
| **H** | `image_direction` | Optional | 1–2 sentence visual brief for this row only |

**Row is processed when:** A has text, B is valid, C is approved, E is empty, D is not `done`/`processing`/previous `error`.

**Retry a row:** Clear D, E, G, I; set C = `TRUE`; run batch again.

### How the batch is triggered

**Manual only** — no background polling. Run `python linkedin_images_watcher.py` once; it scans **all rows** from row 2 down and processes every row that passes the checks below, then exits.

**Eligible row:** A has text · B = `landscape` or `square` · C = `TRUE`/`YES`/`1` · **E empty** · D not `done` / `processing` / `error:...`

**Not required to run:** F, H, G, I (filled by script on success).

### Hybrid prompt model

| Column | Role |
|--------|------|
| **A** | What the LinkedIn post says (caption context) |
| **F** | Engine + **look** — Grok preset, `notebook_sketch`, or Napkin |
| **H** | Optional brief **or** full sketchnote outline (see below) |
| **G** | **Output** — exact prompt or Napkin content (written after each run) |
| **I** | **Output** — Drive view URL |

**Grok photo styles (`b2b_clean`, etc.):** grok-3 reads A + F + H → short scene → grok-imagine → **center-crop** resize → upload.

**`notebook_sketch`:** If **H** is long (≥120 chars), used as full page copy + style; else grok-3 drafts from A + H → grok-imagine → **letterbox** resize → upload.

**Napkin:** post + H sent to Napkin API → **letterbox** resize (edge-matched padding) → upload.

**H examples (short — for photo styles):**
```
Enterprise sales team at a monitor showing a CRM workspace, modern office, no readable text on screen.
```

Leave **H** empty for most rows; use **F** only.

### Column F — image style presets

```powershell
python linkedin_images_watcher.py --list-styles
```

| Key | Best for |
|-----|----------|
| `b2b_clean` | **Default** — clean B2B LinkedIn marketing (navy/teal, uncluttered) |
| `executive_photo` | Thought leadership, realistic office/team |
| `gradient_abstract` | Brand-style banner, gradients, minimal shapes |
| `saas_ui` | Product/software — device + blurred UI, no readable text |
| `concept_metaphor` | One symbolic visual (use sparingly) |
| `stats_visual` | Growth/metrics — abstract charts, no labels |
| `notebook_sketch` | Notebook sketchnote — paste full outline in **H** |

**Aliases:** `sketchnote`/`notebook`/`headless_sketch` → `notebook_sketch`; `professional`/`b2b`/`clean` → `b2b_clean`; `corporate`/`photo` → `executive_photo`; `gradient`/`abstract` → `gradient_abstract`; `saas`/`ui`/`dashboard` → `saas_ui`; `metaphor`/`concept` → `concept_metaphor`; `data`/`stats`/`analytics` → `stats_visual`. Unknown values fall back to `b2b_clean`.

**Salesforce / product posts:** `saas_ui` or `b2b_clean` in F; add concrete **H** when needed.

**Napkin (infographics / hub-and-spoke diagrams):**

| Key | Best for |
|-----|----------|
| `napkin` | Default Napkin style — corporate diagram |
| `napkin_elegant` | Elegant outline diagrams |
| `napkin_sketch` | Hand-drawn sketch style |
| `diagram` / `infographic` | Alias for `napkin` |

Requires `NAPKIN_API_TOKEN` in `grokapi.env` (from app.napkin.ai → Account → Developers). Uses Napkin credits.

**Deal Rooms-style diagram:** F = `napkin`, H = `Hub-and-spoke diagram: center Deal Room, nodes for Sales, Engineering, Factory, Integrations with arrows inward.`

**Headless CRM sketchnote:** F = `notebook_sketch`, H = full section outline (title, 6 sections, footer). Put exact footer at end of **H** with `CRITICAL` line to avoid wrong CTA text.

**Layered architecture diagram** (MCP stack, platform layers): use `napkin_elegant` + **H** describing each layer; not `notebook_sketch`.

### LinkedIn output sizes

| B format | API `aspect_ratio` | Output pixels |
|----------|-------------------|---------------|
| `landscape` | `16:9` | 1200 × 627 |
| `square` | `1:1` | 1080 × 1080 |

View image: column **I** (`drive_url`) or `https://drive.google.com/file/d/<FILE_ID>/view`.

### Config (`linkedin_images_watcher.py`)

```python
SHEET_ID = "..."           # from sheet URL /d/<ID>/edit
WORKSHEET_NAME = "Image Library"
DRIVE_FOLDER_ID = "..."    # from folder URL /folders/<ID>
DRIVE_AUTH = "oauth"       # personal Gmail (recommended)
```

### Credentials and setup

**Install:**
```powershell
pip install -r requirements-linkedin.txt
```

**Keys** — file `grokapi.env` (first), `.env`, or `.env.example`:
```
XAI_API_KEY=xai-...
NAPKIN_API_TOKEN=...    # only for column F = napkin / diagram / infographic
```
Load order: `grokapi.env` → `.env` → `.env.example`.

**Google Sheets** — `service_account.json` in project folder; enable **Google Sheets API**; share the spreadsheet with the service account email (**Editor**).

**Google Drive (personal Gmail, no Workspace):**

1. `DRIVE_AUTH = "oauth"` in `linkedin_images_watcher.py`
2. Google Cloud: OAuth consent screen (External) + your Gmail as test user
3. Credentials → OAuth client ID → **Desktop app** → save as `client_secret.json`
4. Run once: `python setup_drive_oauth.py` → creates `drive_token.json`
5. Drive folder must belong to the Google account you signed in with

**Verify:**
```powershell
python check_linkedin_setup.py
```

**Google Workspace alternative:** `DRIVE_AUTH = "service_account"` + folder inside a **Shared Drive** with service account as Content manager (service accounts cannot upload to My Drive).

### Run

```powershell
python linkedin_images_watcher.py
```

Schedule with Windows Task Scheduler if you want periodic batches.

### LinkedIn known issues

| Issue | Fix |
|-------|-----|
| `Service Accounts do not have storage quota` | Use `DRIVE_AUTH = "oauth"` + `setup_drive_oauth.py`, not My Drive via service account |
| `SpreadsheetNotFound` / 404 on sheet | Wrong `SHEET_ID` or sheet not shared with service account |
| No rows processed | Need A + B + C=`TRUE` + empty E; clear D if retrying |
| Image too abstract for LinkedIn | Use `saas_ui` or `b2b_clean` in F; or **napkin** for diagrams |
| Unknown style in F | Falls back to `b2b_clean` (Grok); check `--list-styles` |
| Napkin errors / no token | Add `NAPKIN_API_TOKEN` to `grokapi.env` |
| Notebook wrong footer text | Put exact footer at end of **H**; see [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) |
| Sheet does not read local `.txt` | Copy prompt into column **H** (file is for `grok_notebook_sketch.py` only) |

---

## 5. Grok X search — live Twitter research

**Script:** `grok_x_query.py` — uses `POST https://api.x.ai/v1/responses` with tool `{"type": "x_search"}`. Separate from LinkedIn and YouTube; does not write to Drive or the sheet.

```powershell
python grok_x_query.py "What is the sentiment on X about Salesforce?"
python grok_x_query.py --from 2026-05-01 --to 2026-05-28 "Key influencers on CRM AI"
python grok_x_query.py --handles salesforce,Benioff "Summarize CRM AI buzz"
python grok_x_query.py -i
python grok_x_query.py --out x_query_outputs\my_report.txt "Your question"
```

| Flag | Purpose |
|------|---------|
| `--handles` / `--exclude` | Limit X accounts (max 20) |
| `--from` / `--to` | Date range (YYYY-MM-DD) |
| `--images` / `--videos` | Analyze media in posts |
| `--model` | Default `grok-4-1-fast` or `GROK_X_MODEL` in env |

Each run prints to the terminal and saves **`x_query_outputs/<timestamp>_<slug>.txt`** (gitignored).

**Docs:** [GROK_X_QUERY.md](GROK_X_QUERY.md) · [xAI X Search](https://docs.x.ai/developers/tools/x-search)

---

## 6. Notebook sketchnote — standalone JPG

**Script:** `grok_notebook_sketch.py` — `grok-imagine-image-quality`, same model as LinkedIn images. Default aspect **portrait `9:16`**.

```powershell
python grok_notebook_sketch.py --prompt-file notebook_sketches\headless_crm_signal_prompt.txt --aspect portrait
python grok_notebook_sketch.py --prompt-file notebook_sketches\my_prompt.txt --aspect landscape --out notebook_sketches\out.jpg
```

| Item | Notes |
|------|--------|
| Prompt file | Must include **visual style** (notebook paper, lime `#00FF41`, panels) **and** section copy — see `headless_crm_signal_prompt.txt` |
| Footer | Put exact footer at end + `CRITICAL — footer must be EXACTLY...` or Grok may reuse old CTA text |
| Output JPG | `notebook_sketches/*.jpg` (gitignored) |
| Sheet + Drive | Copy prompt into column **H**, F = `notebook_sketch`, run §4 batch |

**Docs:** [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md)

---

## Folder Structure

```
Grok Voice api/
  generate.py                  # single TTS
  generate_batch.py            # batch TTS
  generate_images.py           # script → images via grok-3 prompt crafting
  images_from_prompts.py       # prompts txt → images
  videos_from_prompts.py       # prompts txt → videos (text or image-to-video)
  watcher.py                   # Google Sheets automation (not yet tested)
  script1.txt                  # Chola dynasty narration (3 sections)
  CLAUDE.md                    # this file
  linkedin_images_watcher.py   # LinkedIn images batch (Sheets + Drive) — see section 4
  setup_drive_oauth.py         # Drive OAuth one-time setup
  check_linkedin_setup.py      # LinkedIn pipeline health check
  requirements-linkedin.txt    # deps for LinkedIn scripts
  LINKEDIN_IMAGES.md           # LinkedIn pipeline quick start
  LINKEDIN_SHEET_COLUMNS.md    # per-column input guide
  NOTEBOOK_SKETCH.md           # notebook sketchnote style
  GROK_X_QUERY.md              # X search CLI
  SCRIPTS.md                   # all run commands in one place
  grok_notebook_sketch.py      # standalone sketchnote JPG
  grok_x_query.py                # X research via x_search

  notebook_sketches/
    headless_crm_signal_prompt.txt  # sketchnote template (in git)
    *.jpg                        # generated JPGs (gitignored)
  x_query_outputs/             # X research txt output (gitignored)
  .env.example                 # key names template (no secrets)

  script naval chola - audio , images and video/
    script-intro.txt / .mp3
    script-1.txt / .mp3
    script-2.txt / .mp3
    script-3.txt / .mp3

  voice and image prompts/
    chola-image-prompts.txt    # 14 image prompts
    chola-video-prompts.txt    # 6 video prompts
    image_01.jpg … image_20.jpg
    video_01.mp4 … video_10.mp4
```

---

## Run Commands

```powershell
# Set API key
$env:XAI_API_KEY = "xai-..."

# Generate audio for multiple scripts
python generate_batch.py "script naval chola - audio , images and video" script-intro.txt script-1.txt script-2.txt script-3.txt

# Generate images from prompts file
python images_from_prompts.py "voice and image prompts\chola-image-prompts.txt" "voice and image prompts"

# Generate videos from prompts file (text-to-video and/or image-to-video)
python videos_from_prompts.py "voice and image prompts\chola-video-prompts.txt" "voice and image prompts"

# LinkedIn images (batch) — see section 4
python check_linkedin_setup.py
python linkedin_images_watcher.py
python linkedin_images_watcher.py --list-styles

# Notebook sketchnote (local) — see section 6
python grok_notebook_sketch.py --prompt-file notebook_sketches\headless_crm_signal_prompt.txt

# X research — see section 5
python grok_x_query.py "CRM sentiment on X this week"
```

---

## Known Issues & Fixes

| Issue | Fix |
|-------|-----|
| 403 error code 1010 | Use `requests.Session()` — never urllib |
| Image-to-video `image` field rejected | Must be `{"url": "data:image/jpeg;base64,..."}` object, not plain string |
| Windows console encoding error | Avoid `→` and em-dash characters in print statements |
| PowerShell temp files have BOM | Read with `encoding="utf-8-sig"` in Python |
| urllib hangs indefinitely | Always set `timeout=` on urlopen calls |

---

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | — |
| 400 | Bad request | Check parameters |
| 401 | Unauthorized | Check `XAI_API_KEY` |
| 403 / 1010 | Cloudflare block | Switch to requests.Session() |
| 422 | Bad request body | Check field formats |
| 429 | Rate limited | Exponential backoff |
| 500+ | Server error | Retry |
