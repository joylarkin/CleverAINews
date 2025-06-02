#!/usr/bin/env python3
"""
generate_post.py  –  Paste a URL, pick a summary, get a ready-to-publish
_markdown_ post in _posts/YYYY-MM-DD-slug.md.

Usage:
    ./generate_post.py https://some.news/article
"""

import sys, re, datetime, json, textwrap, uuid, pathlib, subprocess
import requests, readability, frontmatter, openai

# 1️⃣ grab & clean the web page
URL = sys.argv[1]
html = requests.get(URL, timeout=20).text
article_html = readability.Document(html).summary()        # extract main body  [oai_citation:0‡PyPI](https://pypi.org/project/readability-lxml/?utm_source=chatgpt.com)
plain_text = re.sub(r"<[^>]+>", "", article_html)[:8000]   # trim to keep prompt small

# 2️⃣ ask the LLM for up to three headline/summary options
SYSTEM_MSG = (
    "You are an editor for an AI-news link-blog. "
    "Return JSON: [{title: str, summary: str}] (max 3 items). "
    "Title ≤ 80 chars, summary ≤ 40 words."
)

response = openai.ChatCompletion.create(                    # vanilla 0.x call  [oai_citation:1‡Gist](https://gist.github.com/pszemraj/c643cfe422d3769fd13b97729cf517c5?utm_source=chatgpt.com)
    model="gpt-4o",                                         # swap for any available model ID
    messages=[
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "user", "content": plain_text},
    ],
    temperature=0.3,
)
candidates = json.loads(response.choices[0].message.content)

# 3️⃣ let you pick the best version
for i, c in enumerate(candidates, 1):
    print(f"\n[{i}] {c['title']}\n   {textwrap.fill(c['summary'], 80)}")
choice = int(input(f"\nPick 1-{len(candidates)} (0 = abort): "))
if choice < 1:
    sys.exit(0)
chosen = candidates[choice - 1]

# 4️⃣ write the Jekyll post file with YAML front-matter
today = datetime.date.today()
slug = re.sub(r"[^a-z0-9]+", "-", chosen["title"].lower()).strip("-")[:50]
fname = f"_posts/{today:%Y-%m-%d}-{slug}.md"

post = frontmatter.Post(                                    # dump YAML + empty body  [oai_citation:2‡python-frontmatter.readthedocs.io](https://python-frontmatter.readthedocs.io/en/latest/handlers.html?utm_source=chatgpt.com)
    "",
    title=chosen["title"],
    date=today.isoformat(),
    link=URL,
    summary=chosen["summary"],
    id=str(uuid.uuid4()),
)
pathlib.Path(fname).write_text(frontmatter.dumps(post), encoding="utf-8")

# 5️⃣ stage the new file so it’s ready to commit
subprocess.run(["git", "add", fname])
print("\nCreated", fname, "and staged it for commit.")