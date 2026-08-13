#!/usr/bin/env python3
"""Sanity-check the generated page. Exits non-zero if anything looks broken."""

import re
import sys
from pathlib import Path

TAGS = ("section", "div", "details", "table", "ul", "ol", "li", "pre", "script",
        "style", "header", "footer", "main", "nav", "dl", "tr", "a", "h1", "h2",
        "h3", "h4", "p", "span", "article", "button")

PATTERNS = ((r'href=""', "empty href"),
            (r"\{\{", "unreplaced placeholder"),
            (r">None<", "None leaked into output"),
            (r"\{[a-z_]+\}", "unrendered {field}"))


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/index.html")
    if not path.exists():
        print(f"  ! {path} does not exist — run make first")
        return 1

    html = path.read_text(encoding="utf-8")
    problems = []

    for tag in TAGS:
        opened = len(re.findall(r"<%s[\s>]" % tag, html))
        closed = len(re.findall(r"</%s>" % tag, html))
        if opened != closed:
            problems.append(f"unbalanced <{tag}>: {opened} open, {closed} close")

    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S)
    for pattern, label in PATTERNS:
        if re.search(pattern, body):
            problems.append(label)

    if "<title>" not in html:
        problems.append("missing <title>")
    if 'name="description"' not in html:
        problems.append("missing meta description")

    ids = re.findall(r'id="([^"]+)"', html)
    for anchor in set(re.findall(r'href="#([^"]+)"', html)):
        if anchor and anchor not in ids:
            problems.append(f"link to #{anchor} but no element has that id")

    for problem in problems:
        print("  !", problem)

    if problems:
        print("check failed")
        return 1

    print(f"check passed — {len(html) // 1024} KB, {html.count('<section')} sections, "
          f"{len(ids)} ids, {html.count('<details')} faq entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
