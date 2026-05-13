# xAI Voice — YouTube Channel Voiceover Project

## Project Goal
Build and test an xAI Text-to-Speech pipeline for YouTube channel voiceovers before scaling up.
User: Rupesh (ruprg21@gmail.com)

---

## API Configuration

- **Endpoint:** `POST https://api.x.ai/v1/tts`
- **Auth:** Bearer token via env var `XAI_API_KEY`
- **Platform:** Node.js (fetch, built-in since Node 18 — no SDK required)
- **Use case:** File output (saved to disk, embedded in video)

### Default Voice Settings
```json
{
  "voice_id": "leo",
  "language": "en",
  "output_format": {
    "codec": "mp3",
    "sample_rate": 44100,
    "bit_rate": 128000
  }
}
```

---

## Baseline Script

```js
// tts.mjs  — run with: XAI_API_KEY=xai-... node tts.mjs
import fs from 'fs';

const res = await fetch('https://api.x.ai/v1/tts', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${process.env.XAI_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'Hello! This is a text-to-speech demo.',
    voice_id: 'leo',
    output_format: { codec: 'mp3', sample_rate: 44100, bit_rate: 128000 },
    language: 'en',
  }),
});

if (!res.ok) throw new Error(`TTS error ${res.status}: ${await res.text()}`);

const buf = Buffer.from(await res.arrayBuffer());
fs.writeFileSync('output.mp3', buf);
console.log('Saved to output.mp3');
```

---

## Voices Available

| Voice | Personality |
|-------|-------------|
| `leo` | Authoritative & strong — current default |
| `eve` | Energetic & upbeat |
| `ara` | Warm & friendly |
| `rex` | Confident & clear |
| `sal` | Smooth & balanced |

---

## Speech Tags Reference

**Inline** (insert at a point):
`[pause]` `[long-pause]` `[laugh]` `[chuckle]` `[breath]` `[inhale]` `[exhale]` `[sigh]` `[hum-tune]` `[giggle]` `[cry]` `[tsk]` `[tongue-click]` `[lip-smack]`

**Wrapping** (wrap text to change delivery):
`<soft>` `<whisper>` `<loud>` `<build-intensity>` `<decrease-intensity>`
`<higher-pitch>` `<lower-pitch>` `<slow>` `<fast>`
`<sing-song>` `<singing>` `<laugh-speak>` `<emphasis>`

Example:
```
"Welcome back. [pause] Today we're covering something big. <build-intensity>This changes everything.</build-intensity>"
```

---

## Output Formats

| codec | sample_rate | bit_rate | Notes |
|-------|------------|---------|-------|
| mp3 | 44100 | 128000 | Current default — YouTube-safe |
| mp3 | 44100 | 192000 | Higher quality option |
| wav | 44100 | — | Lossless, larger files |
| mp3 | 24000 | 128000 | API default (smaller files) |

---

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Audio bytes in body |
| 400 | Bad request | Check text length, voice name, format |
| 401 | Unauthorized | Check `XAI_API_KEY` |
| 429 | Rate limited | Exponential backoff |
| 500+ | Server error | Retry with backoff |

---

## Scaling Notes (for later)
- Requests are independent — parallelize with `Promise.all`
- Implement exponential backoff on 429
- Never expose API key client-side — proxy through backend
- Batch processing: split long scripts into paragraphs, generate in parallel

---

## Next Steps (Testing Phase)
1. Run baseline script with a real YouTube script excerpt
2. Test multiple voices (`leo`, `rex`, `sal`) and compare
3. Add speech tags for natural pauses and emphasis
4. Compare 128 kbps vs 192 kbps quality for video use
5. Build a batch script that takes a `.txt` file and outputs `.mp3`
