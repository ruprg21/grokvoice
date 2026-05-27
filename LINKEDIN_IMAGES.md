# LinkedIn post images

Batch pipeline: Google Sheet **Image Library** → Grok or Napkin image → resize for LinkedIn → upload to Google Drive → write file ID back to the sheet.

**Script:** `linkedin_images_watcher.py` (one run, all eligible rows, then exits)

**Deeper docs:** [CLAUDE.md](CLAUDE.md) section 4 · [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md) (per-column input guide)

---

## Quick start

```powershell
cd "...\Grok Voice api"
pip install -r requirements-linkedin.txt
python setup_drive_oauth.py          # once, for Drive upload
python check_linkedin_setup.py       # verify keys + sheet + folder
python linkedin_images_watcher.py    # batch run
python linkedin_images_watcher.py --list-styles
```

---

## API keys — `grokapi.env`

Put both keys in **`grokapi.env`** in the project root (same folder as `linkedin_images_watcher.py`). Do not commit this file.

```
XAI_API_KEY=xai-...
NAPKIN_API_TOKEN=...
```

| Key | Required when | Where to get it |
|-----|----------------|-----------------|
| `XAI_API_KEY` | All Grok styles (`b2b_clean`, `saas_ui`, …) | xAI console |
| `NAPKIN_API_TOKEN` | Column **F** = `napkin`, `diagram`, `infographic`, etc. | [app.napkin.ai](https://app.napkin.ai) → Account → **Developers** |

**Load order:** `grokapi.env` → `.env` → `.env.example` (first file found wins; does not override vars already in the environment).

Template only (no secrets): `.env.example`

---

## Google credentials

| File | Purpose |
|------|---------|
| `service_account.json` | Read/write Google Sheet (share sheet with SA email) |
| `client_secret.json` + `drive_token.json` | Upload to personal Drive (`DRIVE_AUTH = "oauth"`) |

One-time Drive OAuth:

```powershell
python setup_drive_oauth.py
```

---

## Sheet columns (Image Library)

| Col | Field | You fill? |
|-----|--------|-----------|
| A | `post` | Yes — LinkedIn caption (not an image prompt) |
| B | `format` | Yes — `landscape` or `square` |
| C | `approved` | Yes — `TRUE` to include in batch |
| D | `status` | Auto — `processing`, `done`, `error: ...` |
| E | `drive_file_id` | Auto — Drive file ID after upload |
| F | `image_style` | Optional — picks **Grok** or **Napkin** engine |
| I | `drive_url` | Auto — clickable Drive view link (add header in row 1) |
| G | `image_prompt` | Auto — prompt or Napkin content used |
| H | `image_direction` | Optional — 1–2 sentence visual brief |

**Row runs when:** A has text, B is valid, C approved, **E empty**, D not `done` / `processing` / prior `error`.

**Retry:** Clear D, E, G, I → set C = `TRUE` → run batch again.

**View image:** Column **I** (`drive_url`) or `https://drive.google.com/file/d/<FILE_ID>/view` (FILE_ID from column E)

---

## Column F — two engines

Column **F** chooses the generator. Empty **F** → Grok `b2b_clean`.

### Grok (xAI) — photos, UI, marketing art

| F value | Best for |
|---------|----------|
| `b2b_clean` | Default B2B LinkedIn look |
| `executive_photo` | People / leadership / office |
| `gradient_abstract` | Brand banner, gradients |
| `saas_ui` | Product / CRM / dashboard (no readable text) |
| `concept_metaphor` | One symbolic visual (use sparingly) |
| `stats_visual` | Growth / metrics (no labels) |

Aliases: `saas`/`ui` → `saas_ui`; `professional`/`b2b` → `b2b_clean`; see `--list-styles`.

Needs: `XAI_API_KEY` only.

### Napkin — infographics and diagrams

| F value | Best for |
|---------|----------|
| `napkin` | Corporate hub-and-spoke / business diagrams |
| `napkin_elegant` | Cleaner outline diagrams |
| `napkin_sketch` | Hand-drawn sketch style |
| `diagram` / `infographic` | Same as `napkin` |

Needs: `NAPKIN_API_TOKEN` in `grokapi.env` (uses Napkin credits).

**Example row (Deal Rooms-style):**

| Col | Value |
|-----|--------|
| F | `napkin` |
| H | `Hub-and-spoke: center Deal Room, nodes Sales, Engineering, Factory, Integrations, arrows inward, clear labels.` |
| B | `landscape` |
| C | `TRUE` |

Column **G** after run shows `[Napkin napkin]` plus the text sent to Napkin.

---

## Output sizes

| B format | Pixels |
|----------|--------|
| `landscape` | 1200 × 627 |
| `square` | 1080 × 1080 |

---

## Config (in `linkedin_images_watcher.py`)

```python
SHEET_ID = "..."           # from sheet URL /d/<ID>/edit
WORKSHEET_NAME = "Image Library"
DRIVE_FOLDER_ID = "..."    # from folder URL /folders/<ID>
DRIVE_AUTH = "oauth"       # personal Gmail (recommended)
```

---

## Napkin sizing

- **Landscape:** Napkin gets `height: 627` only (not `width: 1200` — that produced tall images that were cropped).
- **Square:** Napkin gets `width: 1080`.
- Output uses **letterbox fit** (full diagram visible; side padding uses Napkin edge color, not hard white). Grok photos still use center-crop.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Napkin diagram cut off | Re-run after fix; use `landscape` + `napkin`; script letterboxes instead of cropping |
| No rows processed | C = `TRUE`, E empty, valid B, D not blocking |
| `NAPKIN_API_TOKEN not set` | Add token to `grokapi.env`, run `check_linkedin_setup.py` |
| Drive 403 / quota | Use `DRIVE_AUTH = "oauth"` + `setup_drive_oauth.py` |
| xAI 403 | Use `requests.Session()` (already in script); check `XAI_API_KEY` |
| Wrong image style | Run `--list-styles`; unknown Grok F → `b2b_clean` |

---

## Files in this feature

| File | Role |
|------|------|
| `linkedin_images_watcher.py` | Main batch script |
| `check_linkedin_setup.py` | Validate setup |
| `setup_drive_oauth.py` | One-time Drive OAuth |
| `requirements-linkedin.txt` | Python deps |
| `grokapi.env` | Your API keys (local only) |
