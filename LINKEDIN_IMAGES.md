# LinkedIn post images

Batch pipeline: Google Sheet **Image Library** → Grok or Napkin image → resize for LinkedIn → upload to Google Drive → write file ID back to the sheet.

**Script:** `linkedin_images_watcher.py` (one run, all eligible rows, then exits)

**Deeper docs:** [CLAUDE.md](CLAUDE.md) section 4 · [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md) · [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) · [SCRIPTS.md](SCRIPTS.md)

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
| `notebook_sketch` | Notebook sketchnote (green highlighter, sections — put outline in **H**) |

**Notebook sketchnote (`notebook_sketch`):**

- Paste your full outline in **H** (same content as `notebook_sketches\*.txt` prompt files).
- The sheet does **not** read `.txt` files automatically — copy into **H**.
- Letterbox fit (no crop). **E** + **I** on Drive after batch run.
- Standalone (no Drive): [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) · `python grok_notebook_sketch.py --prompt-file ...`
- Put exact **footer** text at the **end** of **H** with a `CRITICAL — footer must be EXACTLY...` line (Grok may otherwise reuse old CTAs).

Aliases: `saas`/`ui` → `saas_ui`; `sketchnote`/`notebook`/`headless_sketch` → `notebook_sketch`; see `--list-styles`.

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

### Which style for which visual?

| You want | F | H |
|----------|---|---|
| Photo / UI / abstract | `b2b_clean`, `saas_ui`, etc. | Short art direction |
| Hub-and-spoke / business diagram | `napkin` | Layer + node labels |
| Notebook story page (sections + CTA) | `notebook_sketch` | Full outline (see `headless_crm_signal_prompt.txt`) |
| MCP / platform **layer stack** diagram | `napkin_elegant` | Describe each horizontal layer and boxes |

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
| Notebook footer wrong | Exact footer at end of **H** + CRITICAL line; re-run row |
| Prompt in `.txt` not used | Copy into column **H** for sheet batch |

---

## Related scripts (not sheet batch)

| Script | Role |
|--------|------|
| `grok_notebook_sketch.py` | Local sketchnote JPG only |
| `grok_x_query.py` | X research → `x_query_outputs/` ([GROK_X_QUERY.md](GROK_X_QUERY.md)) |

---

## Files in this feature

| File | Role |
|------|------|
| `linkedin_images_watcher.py` | Main batch script |
| `check_linkedin_setup.py` | Validate setup |
| `check_linkedin_credentials.py` | API key + SA check only |
| `setup_drive_oauth.py` | One-time Drive OAuth |
| `requirements-linkedin.txt` | Python deps |
| `grokapi.env` | Your API keys (local only) |
| `notebook_sketches/` | Example prompts + local JPG output |
