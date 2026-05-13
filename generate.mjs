// Usage: node generate.mjs script1.txt
// Requires: XAI_API_KEY env var set
import fs from 'fs';
import path from 'path';

const inputFile = process.argv[2];
if (!inputFile) {
  console.error('Usage: node generate.mjs <script.txt>');
  process.exit(1);
}

if (!process.env.XAI_API_KEY) {
  console.error('Error: XAI_API_KEY environment variable is not set.');
  process.exit(1);
}

const raw = fs.readFileSync(inputFile, 'utf8');

// Remove --- section dividers and collapse excess blank lines
const text = raw
  .replace(/^---+\s*$/gm, '')
  .replace(/\n{3,}/g, '\n\n')
  .trim();

console.log(`Sending ${text.length} characters to xAI TTS (voice: leo)...`);

const res = await fetch('https://api.x.ai/v1/tts', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${process.env.XAI_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text,
    voice_id: 'leo',
    output_format: { codec: 'mp3', sample_rate: 44100, bit_rate: 128000 },
    language: 'en',
  }),
});

if (!res.ok) {
  const errText = await res.text();
  console.error(`TTS error ${res.status}: ${errText}`);
  process.exit(1);
}

const outputFile = path.basename(inputFile, path.extname(inputFile)) + '.mp3';
const buf = Buffer.from(await res.arrayBuffer());
fs.writeFileSync(outputFile, buf);
console.log(`Saved to ${outputFile} (${(buf.length / 1024).toFixed(1)} KB)`);
