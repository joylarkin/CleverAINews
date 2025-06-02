#!/usr/bin/env python3
"""
Generate a Jekyll-ready Markdown post from a URL.

Flow:
  1. Fetch URL, strip boiler-plate HTML, keep first 2 000 chars of text.
  2. Ask OpenAI for up to three {title, summary} JSON objects.
  3. Let the user pick one; abort cleanly if nothing returned.
  4. Write _posts/YYYY-MM-DD-slug.md with YAML front-matter.
  5. Stage the file via `git add` so it’s ready to commit.

Requirements (install inside *your* venv):
  python3 -m pip install requests readability-lxml python-frontmatter "openai>=1.0"

The script assumes $OPENAI_API_KEY is set in your environment.
"""
import sys, re, datetime, json, textwrap, uuid, pathlib, subprocess, warnings
from typing import List, Dict

import requests, readability, frontmatter
from openai import OpenAI
from openai._exceptions import OpenAIError

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def slugify(text: str, max_len: int = 50) -> str:
    """Convert a title to a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "post"


def ask_llm(plain_text: str, model: str = "gpt-4o", temperature: float = 0.3) -> List[Dict[str, str]]:
    """Return up to three candidate dicts with keys title / summary."""
    system_msg = (
        "You are an editor for an AI-news link-blog. "
        "Return JSON: [{title: str, summary: str}] (max 3 items). "
        "Title \u2264 80 chars, summary \u2264 40 words."
    )
    client = OpenAI()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": plain_text},
            ],
            temperature=temperature,
        )
    except OpenAIError as e:
        sys.exit(f"❌  OpenAI API call failed: {e}")

    raw = resp.choices[0].message.content.strip()
    try:
        options = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit("❌  Model did not return valid JSON:\n" + raw)

    if not options:
        sys.exit("❌  Model returned zero options. Try a different URL or shorter text.")

    return options

# ---------------------------------------------------------------------------
# Main script
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2 or sys.argv[1].startswith("-h"):
        print("Usage: ./generate_post.py <url>")
        sys.exit(1)

    url = sys.argv[1]

    # 1️⃣ fetch & clean the article
    try:
        html = requests.get(url, timeout=20).text
    except Exception as e:
        sys.exit(f"❌  Could not fetch URL: {e}")

    article_html = readability.Document(html).summary()
    plain_text = re.sub(r"<[^>]+>", "", article_html)
    plain_text = plain_text[:2000]  # keep prompt small

    # 2️⃣ ask the LLM
    options = ask_llm(plain_text)

    # 3️⃣ present options & picker
    for i, opt in enumerate(options, 1):
        print(f"\n[{i}] {opt['title']}\n   {textwrap.fill(opt['summary'], 80)}")

    try:
        choice = int(input(f"\nPick 1-{len(options)} (0 = abort): "))
    except ValueError:
        sys.exit("Aborted (non-numeric input)")

    if choice < 1 or choice > len(options):
        sys.exit("Aborted.")

    chosen = options[choice - 1]

    # 4️⃣ write the Markdown post
    today = datetime.date.today()
    slug = slugify(chosen["title"])
    fname = f"_posts/{today:%Y-%m-%d}-{slug}.md"

    post = frontmatter.Post(
        "",  # empty body; you can edit later if desired
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
    # Silence urllib3 LibreSSL warnings if any remain
    warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
    main()
    