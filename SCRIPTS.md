# Script reference — how to run everything

Project root: `Grok Voice api`. API keys in **`grokapi.env`** (not committed).

```powershell
cd "c:\Users\rupesh\OneDrive\Idea AI Perplx , Cursor\Chronincles of indus\Grok Voice api"
```

---

## Chronicles of Indus — YouTube (xAI TTS / images / video)

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
| `grok_notebook_sketch.py` | `python grok_notebook_sketch.py --prompt-file notebook_sketches\my_prompt.txt --aspect portrait` |

Details: [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md)

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

## Output folders (gitignored)

| Folder | Contents |
|--------|----------|
| `notebook_sketches/` | Sketchnote JPGs from `grok_notebook_sketch.py` |
| `x_query_outputs/` | X research `.txt` reports |
| Drive folder in script | LinkedIn JPEGs from sheet batch |

---

## Master doc

[CLAUDE.md](CLAUDE.md) — API details, credentials, error handling.
