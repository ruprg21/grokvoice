# xAI Voice, Image & Video — Chronicles of Indus YouTube Pipeline

## Project Goal
Build a full YouTube content pipeline using xAI APIs: TTS voiceover, AI image generation, and AI video generation.
User: Rupesh (ruprg21@gmail.com) — GitHub: https://github.com/ruprg21/grokvoice

## Platform
- **Python 3.14** — all scripts use Python (Node.js not installed)
- **Auth:** Bearer token via env var `XAI_API_KEY`
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

**Auto-numbering:** Script finds the highest existing `video_NN.mp4` in the output folder and continues from there — never overwrites.

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
