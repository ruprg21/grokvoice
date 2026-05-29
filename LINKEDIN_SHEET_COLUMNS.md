# LinkedIn Image Library — Sheet column guide

Tab: **Image Library** (see [CLAUDE.md](CLAUDE.md) section 4 for full setup).

Row 1 = headers. Data starts row 2.

**Related:** [LINKEDIN_IMAGES.md](LINKEDIN_IMAGES.md) · [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md) · [SCRIPTS.md](SCRIPTS.md) · Prompt template: `notebook_sketches/headless_crm_signal_prompt.txt`

---

## Quick reference

| Col | Header | You type? | Required for run? |
|-----|--------|-----------|-------------------|
| A | post | Yes | Yes |
| B | format | Yes | Yes |
| C | approved | Yes | Yes (`TRUE`) |
| D | status | No (auto) | — |
| E | drive_file_id | No (auto) | Must be **empty** to run |
| F | image_style | Optional | No (default `b2b_clean`; `napkin` / `notebook_sketch` for diagrams / sketchnotes) |
| G | image_prompt | No (auto) | — |
| H | image_direction | Optional | No (full outline for `notebook_sketch`; recommended for `napkin`) |
| I | drive_url | No (auto) | — (add header `drive_url` in row 1) |

### How a row gets picked up

The watcher runs **only when you execute** `python linkedin_images_watcher.py`. It does not watch the sheet continuously.

| Must be true | Column |
|--------------|--------|
| Post text present | A |
| `landscape` or `square` | B |
| Approved | C = `TRUE` / `YES` / `1` |
| No file yet | E empty |
| Not blocked | D not `done`, `processing`, or `error:...` |

---

## Column A — `post`

**What it is:** Your LinkedIn **caption** (the text you publish with the post).

**What it is NOT:** An image prompt. Do not paste grok/midjourney-style instructions here.

### Good input

- 2–8 sentences of real post copy
- Clear topic (product, announcement, thought leadership)
- Normal line breaks OK

### Example

```
Deal Rooms in Salesforce connect sales, engineering, and factory teams on one record.
Read how teams ship faster: https://example.com/article
#Salesforce #SalesCloud
```

### Weak input

- One vague word (`Salesforce`)
- Only a URL with no context
- Instructions like `generate a blue image of a dashboard`

**Tip:** Stronger post copy → grok-3 infers a more relevant scene. Pair with **F** and **H** for best results.

---

## Column B — `format`

**What it is:** Output shape for LinkedIn.

### Allowed values (case-insensitive)

| Value | Output size | Use when |
|-------|-------------|----------|
| `landscape` | 1200 × 627 | Standard feed link preview (most posts) |
| `square` | 1080 × 1080 | Square feed creative, some carousels |

### Good input

```
landscape
```

or

```
square
```

### Invalid (row skipped)

- `portrait`, `16:9`, `1200x627`, blank

---

## Column C — `approved`

**What it is:** Trigger for the batch script.

### Good input

| Value | Works? |
|-------|--------|
| `TRUE` | Yes |
| `YES` | Yes |
| `1` | Yes |
| `FALSE` / empty / `0` | Row ignored |

### Workflow

1. Fill A, B, (optional F, H)
2. Set C = `TRUE`
3. Run `python linkedin_images_watcher.py`
4. After success, leave C as-is or set `FALSE` to avoid accidental re-runs

---

## Column D — `status`

**What it is:** Script progress (do not type before run).

### Values you will see

| Value | Meaning |
|-------|---------|
| *(empty)* | Not started yet |
| `processing` | Run in progress |
| `done` | Image generated and uploaded |
| `error: ...` | Failed — read message, fix, clear and retry |

### To retry after error

1. Clear **D** (delete cell content)
2. Clear **E**, **G**, and **I**
3. Set **C** = `TRUE`
4. Run batch again

---

## Column E — `drive_file_id`

**What it is:** Google Drive file ID after upload (do not type before run).

### Good state before run

- **Empty** — row will be picked up if C = `TRUE`

### After success

- ID like `1sawBsX9AIT33X56c6TDky-S8RTzd5afp`
- Open: column **I** (`drive_url`) or `https://drive.google.com/file/d/<ID>/view`

### Re-run same row

Clear **E** (and D, G, I), set C = `TRUE` again.

---

## Column I — `drive_url`

**What it is:** Auto-filled clickable Google Drive link after upload.

**Format:** `https://drive.google.com/file/d/<file_id>/view`

### You type?

**No.** Add header `drive_url` in cell **I1** on the Image Library tab (row 1). Script fills **I** on each successful run.

### Re-run same row

Clear **I** with **E**, **D**, and **G** before setting C = `TRUE` again.

---

## Column F — `image_style`

**What it is:** Standard **look** for the image (preset). Default if empty: `b2b_clean`.

**What it is NOT:** The full image prompt (that is built automatically and stored in G).

### Presets — what to pick

| Value in F | Best for | Good response when post is about… |
|------------|----------|----------------------------------|
| `b2b_clean` | Default B2B marketing | General business, announcements, safe professional feed image |
| `executive_photo` | People / leadership | Thought leadership, culture, teamwork |
| `gradient_abstract` | Brand banner | Event promo, brand mood, minimal “designed” graphic |
| `saas_ui` | Software / product | Salesforce, CRM, dashboards, platform features |
| `concept_metaphor` | One symbol | Abstract idea (use rarely — can feel off-brand) |
| `stats_visual` | Metrics / growth | ROI, scale, analytics, performance |
| `notebook_sketch` | Notebook sketchnote | Dense visual summary: paste section outline in **H** (title, 4–6 sections, bullets, CTA) |

### Aliases (also work)

`sketchnote` / `notebook` / `visual_journal` / `headless_sketch` → `notebook_sketch`

`professional`, `b2b`, `clean` → `b2b_clean`  
`corporate`, `photo`, `workplace` → `executive_photo`  
`gradient`, `abstract` → `gradient_abstract`  
`saas`, `ui`, `dashboard` → `saas_ui`  
`data`, `stats`, `analytics` → `stats_visual`

List in terminal:

```powershell
python linkedin_images_watcher.py --list-styles
```

### Good input examples

| Post type | F |
|-----------|---|
| Ecosystem / process diagram | `napkin` |
| Headless CRM / newsletter sketchnote | `notebook_sketch` + full outline in **H** |
| Salesforce product post | `saas_ui` |
| CEO / culture post | `executive_photo` |
| Webinar announcement | `gradient_abstract` or `b2b_clean` |
| Q4 growth results | `stats_visual` |
| Unsure | *(leave empty)* → `b2b_clean` |

### Weak input

- Random words → falls back to `b2b_clean`
- `concept_metaphor` for every post → often too abstract for LinkedIn

### Notebook sketchnote (`notebook_sketch`)

Uses **Grok Imagine** (not Napkin). Best when **H** contains the full page outline:

- Title + subtitle
- Numbered sections with headings and bullets
- Footer CTA (repeat exact lines at the **end** of **H** with a `CRITICAL` footer block)

**Does not read** `notebook_sketches\*.txt` from disk — paste that file into **H**.

After run: JPEG on Drive, **I** = view link, **G** = `[notebook_sketch]` + full prompt.

See [NOTEBOOK_SKETCH.md](NOTEBOOK_SKETCH.md).

### Napkin styles (infographics — uses Napkin API, not Grok)

Requires `NAPKIN_API_TOKEN` in `grokapi.env` (get token at app.napkin.ai → Developers).

| Value in F | Best for |
|------------|----------|
| `napkin` | Hub-and-spoke / business diagrams (default Napkin look) |
| `napkin_elegant` | Cleaner outline diagrams |
| `napkin_sketch` | Hand-drawn sketch diagrams |
| `diagram` or `infographic` | Same as `napkin` |

**Pair with H for Deal Rooms-style graphics:**

```
Hub-and-spoke diagram: central Deal Room, nodes for Sales Team, Engineering Team, Factory Team, Integrations, arrows pointing inward, professional labels.
```

Column **G** will show `[Napkin napkin]` plus the text sent to Napkin.

---

## Column G — `image_prompt`

**What it is:** **Output only** — full prompt (Grok) or Napkin input text (Napkin styles).

### You type?

**No.** Leave empty before run. Script fills after generation.

### How to use it

- Review what the model actually received
- Copy phrasing you like into **H** for the next similar post
- Debug if the image missed the mark

---

## Column H — `image_direction`

**What it is:** Optional **per-post** visual brief. For most Grok photo styles: 1–2 sentences. For **`notebook_sketch`** or **`napkin`**: can be a **full outline** (sections, bullets, footer).

**What it is NOT:**

- Column A again (not the LinkedIn caption)
- A full AI prompt (no “4k, octane, masterpiece”)
- Hashtags or links

### When to leave empty

- Default look from **F** is enough
- Bulk rows with same campaign style

### When to fill H

- Default image was too abstract or generic
- You need a specific scene (product shot, office, industry)

### Good input examples

```
Enterprise sales team reviewing a CRM dashboard on a large monitor, modern office, warm lighting, no readable text on screen.
```

```
Clean Salesforce-themed abstract background, deep blue and white, subtle cloud motif, plenty of empty space on the left, no text.
```

```
Diverse engineers and sales reps in a meeting room with a wall display showing workflow diagrams, professional, photorealistic.
```

### Weak input

```
Make it look cool
```

```
Same as column A pasted again
```

```
Generate LinkedIn image for Salesforce Deal Rooms with text overlay saying Download Now
```

*(Script avoids text in images; asking for text hurts results.)*

### Hybrid recipe (best quality)

| Col | Example |
|-----|---------|
| A | Full LinkedIn post copy |
| F | `saas_ui` |
| H | One concrete scene sentence (above) |
| C | `TRUE` |

---

## Example row (good)

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| *(your post text)* | landscape | TRUE | | | saas_ui | | Enterprise team at CRM on monitor, no readable UI text |

After run: D = `done`, E = file ID, G = full prompt.

---

## Example row (minimal)

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| *(your post text)* | landscape | TRUE | | | | | |

Uses `b2b_clean` automatically; fine for quick tests.

---

## Checklist before you run

- [ ] A has real post copy (not a prompt)
- [ ] B is `landscape` or `square`
- [ ] C is `TRUE`
- [ ] E is empty
- [ ] D is empty or not `processing`
- [ ] F set if you want a specific look (else default)
- [ ] H filled only when you need a specific scene
- [ ] `python check_linkedin_setup.py` passes

```powershell
python linkedin_images_watcher.py
```
