#!/usr/bin/env python3
"""
Generate a Jekyll-ready Markdown post from a URL.

Flow:
1. Fetch the URL, strip boiler-plate HTML, keep the first 1 500 characters of visible text.
2. Ask OpenAI for up to three `{title, summary}` JSON objects.
3. Let the user pick one; exit gracefully if the model returns no usable choices.
4. Write `_posts/YYYY-MM-DD-slug.md` with YAML front-matter.
5. Stage the file with `git add` so it’s ready to commit.

Install these once inside *your* active virtual-environment:
    python3 -m pip install requests "urllib3<2" readability-lxml python-frontmatter "openai>=1.0"

The script expects an environment variable `OPENAI_API_KEY`.
"""
from __future__ import annotations

import json, sys, re, datetime, textwrap, uuid, pathlib, subprocess, warnings
from typing import List, Dict

import requests, readability, frontmatter   # third-party
from openai import OpenAI                   # SDK ≥ 1.0
from openai._exceptions import OpenAIError

# ──────────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────────

def slugify(text: str, max_len: int = 50) -> str:
    """Convert a title to a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "post"


def ask_llm(content: str, model: str = "gpt-4o", temperature: float = 0.3) -> List[Dict[str, str]]:
    """Return a list of candidate headline/summary dicts."""
    system_msg = (
        "You are an editor for an AI-news link-blog. "
        "Return JSON: [{title: str, summary: str}] (max 3 items). "
        "Title ≤ 80 chars, summary ≤ 40 words."
    )
    client = OpenAI()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": content},
            ],
            temperature=temperature,
        )
    except OpenAIError as e:
        sys.exit(f"❌  OpenAI API call failed: {e}")

    raw = resp.choices[0].message.content.strip()
    try:
        options: List[Dict[str, str]] = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit("❌  Model reply wasn’t valid JSON:\n" + raw)

    if not options:
        sys.exit("❌  Model returned zero options. Try a different URL or shorter text.")
    return options

# ──────────────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1].startswith("-h"):
        print("Usage: ./generate_post.py <url>")
        sys.exit(1)

    url = sys.argv[1]

    # 1️⃣ fetch & clean
    try:
        html = requests.get(url, timeout=20).text
    except Exception as e:
        sys.exit(f"❌  Could not fetch URL: {e}")

    article_html = readability.Document(html).summary()
    plain_text = re.sub(r"<[^>]+>", "", article_html)

    if len(plain_text) < 100:
        sys.exit("❌  Extracted text looks empty; the page may require login. Try a different URL.")

    plain_text = plain_text[:1500]  # keep prompt small enough for the model

    # 2️⃣ ask OpenAI
    options = ask_llm(plain_text)

    # 3️⃣ display choices
    for i, opt in enumerate(options, 1):
        print(f"\n[{i}] {opt['title']}\n   {textwrap.fill(opt['summary'], 80)}")

    try:
        choice = int(input(f"\nPick 1-{len(options)} (0 = abort): "))
    except ValueError:
        sys.exit("Aborted – non-numeric input.")

    if choice < 1 or choice > len(options):
        sys.exit("Aborted.")

    chosen = options[choice - 1]

    # 4️⃣ write Markdown post
    today = datetime.date.today()
    slug = slugify(chosen["title"])
    fname = f"_posts/{today:%Y-%m-%d}-{slug}.md"

    post = frontmatter.Post(
        "",  # body is empty; edit later if desired
        title=chosen["title"],
        date=today.isoformat(),
        link=url,
        summary=chosen["summary"],
        id=str(uuid.uuid4()),
    )
    pathlib.Path(fname).write_text(frontmatter.dumps(post), encoding="utf-8")

    # 5️⃣ stage with git
    subprocess.run(["git", "add", fname], check=False)
    print(f"\n✅  Created {fname} and staged it for commit.")


if __name__ == "__main__":
    # silence urllib3 LibreSSL warnings (useful on macOS system Python)
    warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
    main() 
