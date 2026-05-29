# Script reference — how to run everything

Project root: `Grok Voice api`. API keys in **`grokapi.env`** (not committed).

Repo: https://github.com/ruprg21/grokvoice — LinkedIn / notebook / X tools on branch **`linkedin-grok`**; YouTube/Chola on **`main`**.

```powershell
cd "c:\Users\rupesh\OneDrive\Idea AI Perplx , Cursor\Chronincles of indus\Grok Voice api"
```

| Need | Read |
|------|------|
| Full API reference | [CLAUDE.md](CLAUDE.md) |
| LinkedIn sheet columns | [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md) |
| Sketchnote prompts | [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) |

---

## Chronicles of Indus — YouTube (xAI TTS / images / video)

**Typical branch:** `main`. Does not use Napkin or LinkedIn sheet.

| Script | Command |
|--------|---------|
| `generate.py` | `python generate.py script1.txt` |
| `generate_batch.py` | `python generate_batch.py <folder> file1.txt file2.txt` |
| `generate_images.py` | `python generate_images.py script1.txt` |
| `images_from_prompts.py` | `python images_from_prompts.py prompts.txt output_folder` |
| `videos_from_prompts.py` | `python videos_from_prompts.py prompts.txt output_folder` |
| `watcher.py` | `python watcher.py` (sheet TTS polling; set `SHEET_ID` in script) |

Legacy (needs Node): `node generate.mjs script1.txt`

Details: [CLAUDE.md](CLAUDE.md) sections 1–3.

---

## LinkedIn images — Sheet → Grok / Napkin → Drive

**Typical branch:** `linkedin-grok`. **Trigger:** run script manually when rows have C=`TRUE` and E empty.

| Script | Command |
|--------|---------|
| `setup_drive_oauth.py` | `python setup_drive_oauth.py` (once) |
| `check_linkedin_setup.py` | `python check_linkedin_setup.py` |
| `check_linkedin_credentials.py` | `python check_linkedin_credentials.py` |
| `linkedin_images_watcher.py` | `python linkedin_images_watcher.py` |
| | `python linkedin_images_watcher.py --list-styles` |

**Install:** `pip install -r requirements-linkedin.txt`

**Column F styles (summary):**

| F | Engine |
|---|--------|
| `b2b_clean`, `saas_ui`, … | Grok Imagine (photo / UI / abstract) |
| `notebook_sketch` | Grok Imagine (notebook sketchnote; outline in **H**) |
| `napkin`, `napkin_elegant`, … | Napkin API (diagrams) |

Details: [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md) · [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md)

---

## Notebook sketchnote (local JPG, no sheet)

| Script | Command |
|--------|---------|
| `grok_notebook_sketch.py` | `python grok_notebook_sketch.py --prompt-file notebook_sketches\headless_crm_signal_prompt.txt --aspect portrait` |

Template in git: `notebook_sketches/headless_crm_signal_prompt.txt`. Details: [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md)

---

## X (Twitter) research — Grok `x_search`

| Script | Command |
|--------|---------|
| `grok_x_query.py` | `python grok_x_query.py "Sentiment on X about Salesforce?"` |
| | `python grok_x_query.py -i` |
| | `python grok_x_query.py --from 2026-05-01 --to 2026-05-28 "..."` |

**Output:** `x_query_outputs/*.txt` (auto-saved each run)

Details: [GROK_X_QUERY.md](GROK_X_QUERY.md)

---

## Output folders

| Path | In git? | Contents |
|------|---------|----------|
| `notebook_sketches/*.jpg` | No (gitignored) | Sketchnote JPGs |
| `notebook_sketches/*_prompt.txt` | Yes | Prompt templates |
| `x_query_outputs/` | No (gitignored) | X research `.txt` reports |
| Drive folder in script | — | LinkedIn JPEGs from sheet batch |

---

## Master doc

[CLAUDE.md](CLAUDE.md) — API details, credentials, error handling.
