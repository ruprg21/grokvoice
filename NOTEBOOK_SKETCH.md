# Notebook sketchnote images (Grok Imagine)

Hand-drawn **notebook page** infographics (lime green headers, sections, bullets, CTA). Separate from Napkin diagrams and from photo-style Grok presets.

## Two ways to run

### 1. Standalone (local JPG)

```powershell
python grok_notebook_sketch.py --prompt-file notebook_sketches\headless_crm_signal_prompt.txt --aspect portrait
```

| Output | Location |
|--------|----------|
| Default | `notebook_sketches/<timestamp>_<slug>.jpg` |
| Custom | `--out path\to\file.jpg` |

Does **not** upload to Drive. Edit prompts in any `.txt` file.

### 2. Google Sheet → Drive (batch)

| Col | Value |
|-----|--------|
| **F** | `notebook_sketch` (aliases: `sketchnote`, `notebook`) |
| **H** | Full outline — paste content from your `.txt` prompt file |
| **A** | Short topic / caption |
| **B** | `landscape` or `square` |
| **C** | `TRUE`, **E** empty |

```powershell
python linkedin_images_watcher.py
```

Writes **E** (file ID), **I** (view URL), **G** (full prompt). Image goes to your Drive folder.

## Prompt tips

- Put **all section text** in **H** (or the `.txt` file for standalone).
- Repeat exact **footer** copy at the **end** of the prompt with a `CRITICAL` line so Grok does not revert to old CTAs.
- Dense text may have small typos — fix footer in Canva if needed.

## Visual spec (default)

- Lined paper, red margin, spiral binding
- Lime green `#00FF41` headers/boxes, black body text
- Alternating panels, curved arrows, robot/gear doodles
- Portrait `9:16` for standalone; sheet uses **B** format (letterbox fit, no crop)

## Not for

- Layered **architecture stack** diagrams (use **napkin** or design tools) — see [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md)

## See also

- [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md) — full LinkedIn pipeline
- [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md) — column **H** examples
