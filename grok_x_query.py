"""
Query X (Twitter) through the xAI Grok API native x_search integration.

Separate from LinkedIn / YouTube pipelines. Uses XAI_API_KEY from grokapi.env.

Examples:
  python grok_x_query.py "What is the sentiment on X about Salesforce Agentforce?"
  python grok_x_query.py --handles salesforce,Benioff "Who are key influencers discussing CRM AI?"
  python grok_x_query.py --from 2026-05-01 --to 2026-05-26 "Summarize sentiment on Deal Rooms"
  python grok_x_query.py -i
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime

import requests

PROJECT_DIR = pathlib.Path(__file__).parent
OUTPUT_DIR = PROJECT_DIR / "x_query_outputs"
RESPONSES_URL = "https://api.x.ai/v1/responses"
DEFAULT_MODEL = "grok-4-1-fast"
ENV_FILES = ("grokapi.env", ".env", ".env.example")

SYSTEM_PROMPT = """You are a research assistant with live access to X (Twitter) via the x_search tool.

Use x_search to gather current posts, threads, and accounts relevant to the user's question.

When asked about sentiment:
- State overall tone (positive, negative, mixed, neutral) with brief evidence
- List 3-5 recurring themes or narratives
- Mention representative posts or quotes when useful (include @handles)

When asked about influencers or key voices:
- List notable accounts (@handle), role (exec, analyst, creator, etc.), and why they matter
- Note approximate engagement signals if visible (likes, reposts, reply volume)

Be direct, structured, and grounded in what you find on X. Cite handles. If the topic is ambiguous, pick the most likely interpretation and say what you searched for."""

USER_PROMPT_TEMPLATE = """Research this on X using x_search:

{query}

Provide a clear, structured answer. Use bullet sections where helpful."""


def load_env_file() -> None:
    for name in ENV_FILES:
        env_file = PROJECT_DIR / name
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        break


def build_x_search_tool(args: argparse.Namespace) -> dict:
    tool: dict = {"type": "x_search"}
    if args.handles:
        tool["allowed_x_handles"] = [
            h.strip().lstrip("@") for h in args.handles.split(",") if h.strip()
        ][:20]
    if args.exclude:
        tool["excluded_x_handles"] = [
            h.strip().lstrip("@") for h in args.exclude.split(",") if h.strip()
        ][:20]
    if args.from_date:
        tool["from_date"] = args.from_date
    if args.to_date:
        tool["to_date"] = args.to_date
    if args.images:
        tool["enable_image_understanding"] = True
    if args.videos:
        tool["enable_video_understanding"] = True
    return tool


def extract_response_text(data: dict) -> str:
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"].strip()

    parts: list[str] = []
    for item in data.get("output") or []:
        if item.get("type") != "message" or item.get("role") != "assistant":
            continue
        content = item.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content.strip())
            continue
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            text = block.get("text")
            if text and block.get("type") in ("output_text", "text"):
                parts.append(text.strip())
    return "\n\n".join(parts).strip()


def extract_citations(data: dict) -> list:
    citations = data.get("citations")
    if isinstance(citations, list):
        return citations
    return []


def query_x(
    prompt: str,
    api_key: str,
    session: requests.Session,
    *,
    model: str,
    tool: dict,
    timeout: int,
) -> dict:
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(query=prompt)},
        ],
        "tools": [tool],
    }
    resp = session.post(
        RESPONSES_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=timeout,
    )
    if not resp.ok:
        raise RuntimeError(f"API {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def slugify_prompt(prompt: str, max_len: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower()).strip("_")
    return (slug[:max_len] if slug else "query")


def resolve_output_path(prompt: str, out: str | None) -> pathlib.Path:
    if out:
        path = pathlib.Path(out)
        return path if path.is_absolute() else PROJECT_DIR / path
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUT_DIR / f"{stamp}_{slugify_prompt(prompt)}.txt"


def format_citations(citations: list) -> str:
    if not citations:
        return ""
    lines = ["", "--- Citations ---"]
    for i, cite in enumerate(citations, 1):
        if isinstance(cite, str):
            lines.append(f"{i}. {cite}")
        elif isinstance(cite, dict):
            lines.append(f"{i}. {cite.get('url') or cite.get('title') or cite}")
    return "\n".join(lines)


def save_response_file(
    path: pathlib.Path,
    *,
    prompt: str,
    model: str,
    tool: dict,
    text: str,
    citations: list,
    response_id: str | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tool_opts = {k: v for k, v in tool.items() if k != "type"}
    header = [
        f"Query: {prompt}",
        f"Model: {model}",
        f"Tool: x_search",
        f"Saved: {datetime.now().isoformat(timespec='seconds')}",
    ]
    if tool_opts:
        header.append(f"Options: {json.dumps(tool_opts)}")
    if response_id:
        header.append(f"Response ID: {response_id}")
    body = "\n".join(header) + "\n\n---\n\n" + text + format_citations(citations) + "\n"
    path.write_text(body, encoding="utf-8")


def run_query(args: argparse.Namespace) -> int:
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if not api_key:
        print("Error: XAI_API_KEY not set. Add to grokapi.env", file=sys.stderr)
        return 1

    model = os.environ.get("GROK_X_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    tool = build_x_search_tool(args)

    print(f"Model: {model}")
    print(f"Tool: x_search")
    if tool.keys() - {"type"}:
        print(f"Options: {json.dumps({k: v for k, v in tool.items() if k != 'type'})}")
    print(f"Query: {args.prompt}\n")
    print("Searching X...\n")

    with requests.Session() as session:
        data = query_x(
            args.prompt,
            api_key,
            session,
            model=model,
            tool=tool,
            timeout=args.timeout,
        )

    text = extract_response_text(data)
    if not text:
        print("No text in response. Raw JSON saved for debug.", file=sys.stderr)
        if args.raw:
            print(json.dumps(data, indent=2)[:8000])
        return 1

    print(text)

    citations = extract_citations(data)
    if citations:
        print("\n--- Citations ---")
        for i, cite in enumerate(citations, 1):
            if isinstance(cite, str):
                print(f"{i}. {cite}")
            elif isinstance(cite, dict):
                print(f"{i}. {cite.get('url') or cite.get('title') or cite}")

    response_id = data.get("id")
    if args.raw:
        print("\n--- Raw response id ---")
        print(response_id or "(no id)")

    out_path = resolve_output_path(args.prompt, args.out)
    save_response_file(
        out_path,
        prompt=args.prompt,
        model=model,
        tool=tool,
        text=text,
        citations=citations,
        response_id=response_id,
    )
    print(f"\nSaved to: {out_path}")

    return 0


def interactive_loop(args: argparse.Namespace) -> int:
    print("Grok X query (interactive). Empty line or Ctrl+C to exit.\n")
    try:
        while True:
            try:
                line = input("X query> ").strip()
            except EOFError:
                break
            if not line:
                break
            args.prompt = line
            print()
            run_query(args)
            print()
    except KeyboardInterrupt:
        print("\nBye.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query X via xAI Grok native x_search (Responses API)."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help='Question, e.g. "What is the sentiment on X about Salesforce?"',
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive prompt loop",
    )
    parser.add_argument(
        "--handles",
        metavar="H1,H2",
        help="Only posts from these @handles (max 20, comma-separated)",
    )
    parser.add_argument(
        "--exclude",
        metavar="H1,H2",
        help="Exclude these @handles (max 20)",
    )
    parser.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD")
    parser.add_argument("--images", action="store_true", help="Analyze images in posts")
    parser.add_argument("--videos", action="store_true", help="Analyze videos in posts")
    parser.add_argument(
        "--model",
        default=None,
        help=f"Override model (default: {DEFAULT_MODEL} or GROK_X_MODEL env)",
    )
    parser.add_argument("--timeout", type=int, default=600, help="HTTP timeout seconds")
    parser.add_argument("--raw", action="store_true", help="Print response id / debug info")
    parser.add_argument(
        "--out",
        metavar="FILE",
        help="Output .txt path (default: x_query_outputs/<timestamp>_<slug>.txt)",
    )
    args = parser.parse_args(argv)

    if args.handles and args.exclude:
        parser.error("Use --handles or --exclude, not both.")

    if args.model:
        os.environ["GROK_X_MODEL"] = args.model

    if not args.interactive and not args.prompt:
        parser.error("Provide a prompt or use --interactive")

    return args


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    args = parse_args(argv)
    if args.interactive:
        return interactive_loop(args)
    return run_query(args)


if __name__ == "__main__":
    raise SystemExit(main())
