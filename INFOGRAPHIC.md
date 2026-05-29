# B2B SaaS technical infographic (local JPG)

Dense flat corporate one-pager (navy header, pillar icons, before/after columns, workflow strip, tech table). Separate from **notebook sketchnote** ([NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md)) and from Napkin-only diagrams in the sheet batch.

**Example prompt in git:** `infographic/info_script.txt` (Salesforce Data Cloud).

---

## Standalone scripts (no Google Sheet)

| Script | Engine | Best for |
|--------|--------|----------|
| **`grok_infographic.py`** | Grok Imagine (`grok-imagine-image-quality`) | **Dense labeled one-pager** — usually closest to cheat-sheet layout |
| `napkin_infographic.py` | Napkin API | Simpler diagrams / hub-and-spoke; may render as Gantt or bridge if prompt is long |

Both read a `.txt` file, use **`grokapi.env`**, and save JPG under `infographic/` (gitignored).

### Grok (recommended for dense layout)

```powershell
python grok_infographic.py --prompt-file infographic\info_script.txt --aspect landscape
```

| Flag | Default | Notes |
|------|---------|--------|
| `--prompt-file` | `infographic/info_script.txt` | Style prefix + full script sent to Imagine |
| `--aspect` | `landscape` | `16:9` — use `square` for 1:1 |
| `--out` | auto timestamp | e.g. `infographic\info_script_grok_20260529_121553.jpg` |

Needs: **`XAI_API_KEY`** only.

### Napkin

```powershell
python napkin_infographic.py --prompt-file infographic\info_script.txt --style napkin --format landscape
```

| Flag | Default | Notes |
|------|---------|--------|
| `--style` | `napkin_elegant` | Try `napkin` for corporate before/after |
| `--format` | `landscape` | Letterboxed to 1200×627 |
| `--raw-png` | off | Save Napkin PNG without LinkedIn resize |

Needs: **`NAPKIN_API_TOKEN`** in `grokapi.env`.

---

## Google Sheet batch (Drive upload)

Same content as the `.txt` file, but the watcher **does not read files from disk** — paste into column **H**.

| Col | Dense one-pager |
|-----|-----------------|
| **F** | `napkin_elegant` or `napkin` (Napkin); or `saas_ui` + long **H** (Grok, less reliable text) |
| **H** | Structured section list — see [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md#b2b-saas-technical-infographic-dense-one-pager) |
| **B** | `landscape` |

```powershell
python linkedin_images_watcher.py
```

For local iteration, prefer **`grok_infographic.py`** then copy winning prompt into **H** for batch.

---

## Prompt tips

- Include **layout** (header, pillars, comparison, flow, footer) **and** **copy** (bullets, labels).
- Avoid prose-only files — Napkin may pick Gantt/timeline; Grok handles dense layout better in tests.
- Spot-check typos on footer and table; fix in Canva if needed.

---

## Output

| Path | In git? |
|------|---------|
| `infographic/info_script.txt` | Yes (example) |
| `infographic/*_grok_*.jpg` | No (gitignored) |
| `infographic/*.jpg` | No (gitignored) |

---

## See also

- [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md) — sheet pipeline + style picker
- [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) — `grok_notebook_sketch.py` (notebook style)
- [SCRIPTS.md](SCRIPTS.md) — all commands
- [CLAUDE.md](CLAUDE.md) §§6–7
