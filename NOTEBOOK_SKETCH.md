# Notebook sketchnote images (Grok Imagine)

Hand-drawn **notebook page** infographics (lime green `#00FF41` headers, lined paper, red margin, spiral binding, alternating panels, CTA footer). Separate from Napkin diagrams and from photo-style Grok presets.

**Reference prompt in git:** `notebook_sketches/headless_crm_signal_prompt.txt` (style block + Headless CRM section copy).

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

## Prompt structure (required for sketchnote look)

A **content-only** outline (sections + bullets) without visual instructions often produces a **plain illustration**, not the notebook layout.

Include both:

1. **Visual style** — notebook paper, lime green, panels, icons, portrait layout (copy top of `headless_crm_signal_prompt.txt`).
2. **Page content** — title, sections, footer.

## Prompt tips

- Put **all section text** in **H** (or the `.txt` file for standalone).
- Repeat exact **footer** copy at the **end** with `CRITICAL — footer must be EXACTLY...` so Grok does not revert to old CTAs.
- Dense text may have small typos — fix footer in Canva if needed.

## Visual spec (default)

- Lined paper, red margin, spiral binding
- Lime green `#00FF41` headers/boxes, black body text
- Alternating panels, curved arrows, robot/gear doodles
- Portrait `9:16` for standalone; sheet uses **B** format (letterbox fit, no crop)

## Not for

- **B2B SaaS technical infographic** — dense flat one-pager (navy header, before/after table, workflow strip, stack table). Use **F** = `napkin_elegant` + structured **H** — see [LINKEDIN_IMAGES.md — B2B SaaS technical infographic](LINKEDIN_IMAGES.md#b2b-saas-technical-infographic-dense-one-pager)
- Layered **architecture stack** diagrams (same Napkin path, simpler **H**)

## Standalone script

| Script | Output folder |
|--------|----------------|
| `grok_notebook_sketch.py` | `notebook_sketches/` |

Other local image tools (different style):

| Script | Style | Doc |
|--------|--------|-----|
| `grok_infographic.py` | B2B SaaS dense one-pager | [INFOGRAPHIC.md](INFOGRAPHIC.md) |
| `napkin_infographic.py` | Napkin diagrams | [INFOGRAPHIC.md](INFOGRAPHIC.md) |

## See also

- [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md) — full LinkedIn pipeline + SaaS one-pager section
- [INFOGRAPHIC.md](INFOGRAPHIC.md) — `grok_infographic.py` / `napkin_infographic.py`
- [LINKEDIN_SHEET_COLUMNS.md](LINKEDIN_SHEET_COLUMNS.md) — column **H** examples
- [SCRIPTS.md](SCRIPTS.md) · [CLAUDE.md](CLAUDE.md) §6
