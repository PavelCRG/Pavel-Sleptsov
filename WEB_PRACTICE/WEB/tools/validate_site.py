# -*- coding: utf-8 -*-
"""Quick site validation: links, CSS imports, day-7 nav."""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
CSS_MAIN = WEB / "css" / "main.css"


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[int, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if tag == "a" and d.get("href"):
            self.links.append((self.getpos()[0], "href", d["href"]))
        if tag in ("img", "script", "link") and d.get("src"):
            self.links.append((self.getpos()[0], "src", d["src"]))
        if tag == "link" and d.get("href"):
            self.links.append((self.getpos()[0], "href", d["href"]))


def css_imports_exist() -> list[str]:
    errs: list[str] = []
    text = CSS_MAIN.read_text(encoding="utf-8")
    for m in re.finditer(r'@import\s+"([^"]+)"', text):
        p = (CSS_MAIN.parent / m.group(1)).resolve()
        if not p.is_file():
            errs.append(f"Missing CSS: {m.group(1)}")
    return errs


def is_external(url: str) -> bool:
    return url.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:"))


def resolve(html: Path, url: str) -> Path | None:
    if is_external(url):
        return None
    base = html.parent
    target = (base / url).resolve()
    try:
        target.relative_to(WEB.resolve())
    except ValueError:
        return None
    return target


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(css_imports_exist())

    day7_nav_missing: list[str] = []
    for html in WEB.rglob("*.html"):
        rel = html.relative_to(WEB)
        text = html.read_text(encoding="utf-8", errors="replace")
        if "WEB-ПРАКТИКА" in text or "web-практика" in text.lower():
            if "День 7" not in text and rel.parts[0].startswith("den-"):
                day7_nav_missing.append(str(rel))
            if rel.name == "index.html" and len(rel.parts) == 2:
                if "День 7" not in text:
                    day7_nav_missing.append(str(rel))

        parser = LinkExtractor()
        try:
            parser.feed(text)
        except Exception as e:
            errors.append(f"{rel}: HTML parse error: {e}")
            continue

        for line, kind, url in parser.links:
            if is_external(url) or url.startswith("data:"):
                continue
            target = resolve(html, url)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"{rel}:{line} broken {kind} -> {url}")

    for p in sorted(set(day7_nav_missing)):
        if p.startswith("den-") and p.endswith("index.html"):
            parts = Path(p).parts
            if len(parts) == 2:
                warnings.append(f"Missing 'День 7' in nav: {p}")

    print("=== WEB site validation ===")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(" ", w)
    if errors:
        print("\nErrors:")
        for e in errors:
            print(" ", e)
        print(f"\nTotal errors: {len(errors)}")
        return 1
    print("\nNo broken local links or missing CSS.")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
