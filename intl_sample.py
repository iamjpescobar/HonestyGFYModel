"""
International source sampler v2 — KBO structure recon.

NPB is solved (npb.jp monthly page fully parsed — see npb_precompute.py).
This pass digs into MyKBOStats' /schedule page, which answers 200 but
uses div-based markup (no <table> rows), so v1's probe missed it.
Dumps game-row structure and game links so the KBO fetcher gets written
against reality. Reconnaissance only; nothing is saved.
"""

import re
import requests

UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}


def fetch(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        return r.status_code, (r.content.decode("utf-8", errors="replace") if r.content else "")
    except Exception as exc:
        return "ERR", str(exc)


def section(title):
    print("\n" + "=" * 70 + "\n" + title + "\n" + "=" * 70)


def dump_body(html, limit=6000):
    """Prints the page's main content area with tags intact, whitespace
    collapsed — enough structure to write a parser from."""
    body = html
    for anchor in ('<main', '<div id="content"', '<div class="content"', "<body"):
        i = html.find(anchor)
        if i != -1:
            body = html[i:]
            break
    print(re.sub(r"\s+", " ", body)[:limit])


def show_game_links(html, limit=30):
    print("--- links containing /games/ or /game ---")
    hits = re.findall(r'href="([^"]*game[^"]*)"', html, re.I)
    for h in list(dict.fromkeys(hits))[:limit]:
        print(" ", h)
    if not hits:
        print("  (none)")


def main():
    for label, url in [
        ("KBO / MyKBOStats /schedule", "https://mykbostats.com/schedule"),
        ("KBO / MyKBOStats homepage (today's games block?)", "https://mykbostats.com/"),
    ]:
        section(label)
        code, html = fetch(url)
        print(f"status {code}, {len(html):,} bytes")
        if isinstance(code, int) and code == 200:
            show_game_links(html)
            dump_body(html)

    print("\n=== sample v2 done ===")


if __name__ == "__main__":
    main()