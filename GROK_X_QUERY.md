# Grok X search queries

Standalone CLI: ask Grok to research **live X (Twitter)** using xAI’s native **`x_search`** tool (`POST https://api.x.ai/v1/responses`). Not connected to LinkedIn images or the YouTube pipeline.

**Also documented in:** [CLAUDE.md](CLAUDE.md) section 5 · [SCRIPTS.md](SCRIPTS.md)

## Setup

Uses the same key as other scripts:

```
grokapi.env
XAI_API_KEY=xai-...
```

Optional:

```
GROK_X_MODEL=grok-4-1-fast
```

Requires `requests` (already in `requirements-linkedin.txt` or install with `pip install requests`).

## Run

```powershell
cd "...\Grok Voice api"

# Sentiment / themes
python grok_x_query.py "What is the sentiment on X about Salesforce Deal Rooms?"

# Key influencers
python grok_x_query.py "Who are the key influencers discussing Agentforce on X?"

# Limit accounts or dates
python grok_x_query.py --handles salesforce,Benioff "Summarize CRM AI buzz this week"
python grok_x_query.py --from 2026-05-01 --to 2026-05-26 "Sentiment on Winter 26 release"

# Interactive
python grok_x_query.py -i
```

## Flags

| Flag | Purpose |
|------|---------|
| `--handles h1,h2` | Only these accounts (max 20) |
| `--exclude h1,h2` | Exclude accounts (cannot combine with `--handles`) |
| `--from YYYY-MM-DD` | Start of X search window |
| `--to YYYY-MM-DD` | End of window |
| `--images` | Analyze images in posts |
| `--videos` | Analyze videos in posts |
| `--model NAME` | e.g. `grok-4.3` (default `grok-4-1-fast`) |
| `-i` | Interactive mode |

## How it works

1. Sends your prompt to `POST https://api.x.ai/v1/responses`
2. Enables tool `{"type": "x_search"}`
3. Grok searches X and writes a structured answer (sentiment, influencers, themes, etc.)
4. Prints citations when the API returns them
5. **Saves every run** to a `.txt` file (see below)

## Where responses are saved

Default folder:

```
x_query_outputs/
  20260527_163500_what_is_the_sentiment_on_x_about_salesforce.txt
```

Each file includes the query, model, timestamp, answer, and citations.

Custom path:

```powershell
python grok_x_query.py --out my_report.txt "Sentiment on Agentforce"
```

## Cost note

Each run invokes **x_search** (tool pricing on top of tokens). See [xAI pricing](https://x.ai/api).

## Related docs

- [SCRIPTS.md](SCRIPTS.md) — all project scripts
- [CLAUDE.md](CLAUDE.md) section 5 — summary in master doc
- [xAI X Search tool](https://docs.x.ai/developers/tools/x-search)

Not used by LinkedIn image batch, `grok_notebook_sketch.py`, `grok_infographic.py`, or `napkin_infographic.py`.
