#!/usr/bin/env python3
"""Generate index.html listing every GitHub Pages site owned by USER.

Discovers repos with Pages enabled, verifies each site is live, pulls the
page <title> and the repo description, and renders them as cards.
"""

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("PAGES_USER", "fmiguelt")
TOKEN = os.environ.get("GITHUB_TOKEN")
# Repos never listed: the site itself, the profile README repo.
SKIP = {f"{USER}.github.io", USER}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")


def get(url, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": f"{USER}-index-builder",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def repos():
    out, page = [], 1
    while True:
        batch = json.loads(get(
            f"https://api.github.com/users/{USER}/repos"
            f"?per_page=100&page={page}&sort=pushed"))
        if not batch:
            break
        out += batch
        if len(batch) < 100:
            break
        page += 1
    return out


def page_title(url):
    """Return the <title> of a live page, or None if it isn't reachable."""
    try:
        body = get(url, accept="text/html")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  ! unreachable ({e})", file=sys.stderr)
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
    if not m:
        return ""
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()


def collect():
    sites = []
    for r in repos():
        name = r["name"]
        if name in SKIP or r.get("archived") or not r.get("has_pages"):
            continue
        url = f"https://{USER}.github.io/{name}/"
        print(f"- {name}", file=sys.stderr)
        title = page_title(url)
        if title is None:          # Pages flag set but nothing served yet.
            continue
        sites.append({
            "name": name,
            "url": url,
            "repo": r["html_url"],
            "title": title or name,
            "desc": (r.get("description") or "").strip(),
            "pushed": r["pushed_at"],
        })
    sites.sort(key=lambda s: s["pushed"], reverse=True)
    return sites


def card(s):
    e = html.escape
    when = datetime.strptime(s["pushed"], "%Y-%m-%dT%H:%M:%SZ")
    desc = f'<p class="desc">{e(s["desc"])}</p>' if s["desc"] else ""
    return f"""      <li class="card">
        <a class="card-link" href="{e(s['url'])}">
          <h2>{e(s['title'])}</h2>
          {desc}
        </a>
        <div class="meta">
          <time datetime="{e(s['pushed'])}">Updated {when:%d %b %Y}</time>
          <a class="src" href="{e(s['repo'])}">Source</a>
        </div>
      </li>"""


def render(sites):
    built = datetime.now(timezone.utc)
    cards = "\n".join(card(s) for s in sites) or \
        '      <li class="empty">No published pages yet.</li>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Francisco Tavares</title>
<meta name="description" content="Index of pages published at {USER}.github.io">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>&#x1F3C3;</text></svg>">
<style>
:root {{
  color-scheme: light dark;
  --bg: #fbfbfa;
  --surface: #ffffff;
  --border: #e4e4e1;
  --text: #1a1a18;
  --muted: #6b6b66;
  --accent: #b8502a;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #161614;
    --surface: #1f1e1c;
    --border: #33312e;
    --text: #efedea;
    --muted: #9a968f;
    --accent: #e08a5f;
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  padding: 0 16px;
  background: var(--bg);
  color: var(--text);
  font: 16px/1.55 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}}
.wrap {{ max-width: 720px; margin: 0 auto; padding-block: 72px 56px; }}
header {{ margin-bottom: 40px; }}
h1 {{ margin: 0 0 6px; font-size: 1.75rem; letter-spacing: -0.02em; }}
header p {{ margin: 0; color: var(--muted); }}
ul {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; }}
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  transition: border-color .15s ease, transform .15s ease;
}}
.card:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
.card-link {{ display: block; padding: 20px 20px 4px; text-decoration: none; color: inherit; }}
.card h2 {{ margin: 0 0 6px; font-size: 1.05rem; letter-spacing: -0.01em; }}
.card:hover h2 {{ color: var(--accent); }}
.desc {{ margin: 0; color: var(--muted); font-size: .9rem; }}
.meta {{
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  padding: 12px 20px 16px; font-size: .8rem; color: var(--muted);
}}
.src {{ color: var(--muted); text-decoration: none; border-bottom: 1px solid var(--border); }}
.src:hover {{ color: var(--accent); border-color: var(--accent); }}
.empty {{ color: var(--muted); padding: 24px 0; }}
footer {{ margin-top: 48px; font-size: .78rem; color: var(--muted); }}
footer a {{ color: inherit; }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Francisco Tavares</h1>
      <p>Pages published at {USER}.github.io</p>
    </header>
    <ul>
{cards}
    </ul>
    <footer>
      Rebuilt automatically from
      <a href="https://github.com/{USER}?tab=repositories">my repositories</a>
      &middot; {built:%d %b %Y, %H:%M} UTC
    </footer>
  </div>
</body>
</html>
"""


if __name__ == "__main__":
    found = collect()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(found))
    print(f"Wrote {OUT} with {len(found)} site(s).", file=sys.stderr)
