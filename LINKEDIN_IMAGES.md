# LinkedIn post images

Batch pipeline: Google Sheet **Image Library** → Grok or Napkin image → resize for LinkedIn → upload to Google Drive → write **E** (file ID) and **I** (view URL) back to the sheet.

**Script:** `linkedin_images_watcher.py` — **manual batch** (one run, all eligible rows, then exits; no background polling).

**GitHub:** Developed on branch `linkedin-grok` ([ruprg21/grokvoice](https://github.com/ruprg21/grokvoice)). YouTube/Chola scripts remain on `main`.

**Master doc:** [CLAUDE.md](CLAUDE.md) section 4 · **Columns:** [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md) · **Sketchnote:** [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) · **Infographic:** [INFOGRAPHIC.md](INFOGRAPHIC.md) · **All commands:** [SCRIPTS.md](SCRIPTS.md)

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
| H | `image_direction` | Optional — short brief, or **full sketchnote outline** for `notebook_sketch` |

**Row runs when:** A has text, B is valid, C approved, **E empty**, D not `done` / `processing` / prior `error`.

**Does not read** local `.txt` files — copy `notebook_sketches\headless_crm_signal_prompt.txt` into **H** for sketchnotes.

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
| **Dense B2B SaaS one-pager** (see below) | `napkin_elegant` or `napkin` | Full section list in **H** |

---

## B2B SaaS technical infographic (dense one-pager)

**What people call it:** B2B SaaS technical infographic, product marketing one-pager, solution overview graphic, DX (developer experience) marketing visual, or LinkedIn “save-worthy” explainer.

**What it looks like:** Vertical, information-dense layout — dark navy header band, flat two-tone icons, color-coded pillar cards, feature grid, **before vs after** comparison (red X vs green checkmarks), horizontal **workflow arrow** strip, key takeaways, optional tech-stack table, quote/CTA footer. Corporate flat design — **not** hand-drawn notebook (`notebook_sketch`) and **not** a single photo.

**Example use case:** Salesforce Headless 360 + MCP + Agentforce cheat sheet (header, four systems, innovations grid, old/new workflow, time-savings metric, “how it works together” flow, stack table).

### Sheet settings

| Col | Recommendation |
|-----|----------------|
| **F** | `napkin_elegant` (first choice) or `napkin` |
| **H** | Structured brief — list every block Napkin should draw (see template below) |
| **B** | `landscape` (1200 x 627) |
| **A** | Normal LinkedIn caption (not the layout spec) |

**Avoid for this layout:** `notebook_sketch` (lined paper / lime green), `concept_metaphor` (one symbol only), empty **F** with only vague **H** (falls back to generic `b2b_clean` photo art).

**Local test (no sheet):** Prefer **`grok_infographic.py`** for dense labeled layouts; **`napkin_infographic.py`** for simpler diagrams. See [INFOGRAPHIC.md](INFOGRAPHIC.md).

**Sheet batch:** `saas_ui` + long **H** uses grok-3 prompt builder (less control than `grok_infographic.py`). Napkin via F = `napkin` / `napkin_elegant` + structured **H**.

### H brief template (paste into column H)

```
B2B SaaS technical infographic, portrait-friendly vertical layout, flat corporate icons, navy header.

HEADER: [title] + [subtitle]. Logo area: [brand].

ROW 1 — Four pillars (color-coded circles): [System 1 name + one line], [System 2], [System 3], [System 4].

SECTION — Key innovations: 4 cards with icons — [card 1], [card 2], [card 3], [card 4 including MCP/tools if relevant].

COMPARISON — Left column red header "The Old Way": bullet list with X icons. Right column green header "The New Way": bullet list with checkmarks. Side metric: [e.g. 3-4 hours down to under 10 minutes].

FLOW — Horizontal arrows: [step1] -> [step2] -> [step3] -> ... -> [final step].

FOOTER — Key takeaways (3-5 bullets). Optional tech stack table: columns Tool, Version, Status. Bottom quote: "[exact CTA line]".

Style: clean sans-serif, high contrast, no photorealistic people, readable labels on all boxes.
```

Shorten or expand blocks to match your post; Napkin works best when **H** names sections and labels explicitly.

### vs other styles

| Style | Genre |
|-------|--------|
| **SaaS technical infographic** (this section) | Flat corporate infographic, dense text + diagrams |
| `notebook_sketch` | Hand-drawn notebook page — [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) |
| `saas_ui` (Grok) | Product photo / blurred UI mock — not a labeled cheat sheet |
| `b2b_clean` | Single marketing scene — not multi-section layout |

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

## Resize behavior

| Engine | Resize |
|--------|--------|
| Grok photos (`b2b_clean`, `saas_ui`, …) | Center-crop to LinkedIn size |
| `notebook_sketch` | Letterbox fit (no crop) |
| Napkin | Letterbox fit; edge color sampled from diagram borders |

## Napkin API sizing

- **Landscape:** Napkin gets `height: 627` only (not `width: 1200` — that produced tall images that were cropped).
- **Square:** Napkin gets `width: 1080`.

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
| `grok_notebook_sketch.py` | Local notebook sketchnote JPG — [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) |
| `grok_infographic.py` | Local B2B SaaS one-pager (Grok Imagine) — [INFOGRAPHIC.md](INFOGRAPHIC.md) |
| `napkin_infographic.py` | Local infographic / diagram (Napkin API) — [INFOGRAPHIC.md](INFOGRAPHIC.md) |
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
| `grok_notebook_sketch.py` | Standalone sketchnote generator |
| `grok_infographic.py` | Standalone B2B infographic (Grok) |
| `napkin_infographic.py` | Standalone B2B infographic (Napkin) |
| `notebook_sketches/headless_crm_signal_prompt.txt` | Sketchnote prompt template (in git) |
| `notebook_sketches/*.jpg` | Sketchnote JPG output (gitignored) |
| `infographic/info_script.txt` | SaaS one-pager example prompt (in git) |
| `infographic/*.jpg` | Infographic JPG output (gitignored) |
