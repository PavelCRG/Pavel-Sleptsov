#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Подключает ОКР из COURSE_4/CONTROL к сайту.

Запуск из корня репозитория:
  py -3 COURSE_4/CONTROL/sync_okr.py
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "COURSE_4" / "CONTROL"
DST = ROOT / "WEB_ALL" / "materials" / "course-4" / "control"
PAGE = ROOT / "WEB_ALL" / "pages" / "course-4" / "okr.html"

SKIP = {".gitkeep", "thumbs.db", "desktop.ini", ".ds_store"}
HELPERS = {"sync_okr.py", "sync_course4.py", "как_подключить.txt"}
PDF = {".pdf"}
HTML = {".html", ".htm"}
MARK_A = "<!-- ok -->"
MARK_B = "<!-- /ok -->"


def skip(p: Path) -> bool:
    n = p.name.lower()
    return n in SKIP or n in HELPERS or n.endswith(".py") or p.name.startswith("~$")


def natural_key(name: str):
    return [(0, int(x)) if x.isdigit() else (1, x.lower()) for x in re.split(r"(\d+)", name)]


def find_sub(parent: Path, *names: str) -> Path | None:
    want = {n.lower() for n in names}
    for c in parent.iterdir():
        if c.is_dir() and c.name.lower() in want:
            return c
    return None


def ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def move_into(src: Path, dest_dir: Path) -> None:
    ensure(dest_dir)
    dest = dest_dir / src.name
    if dest.resolve() == src.resolve():
        return
    if dest.exists():
        if dest.stat().st_size == src.stat().st_size:
            src.unlink(missing_ok=True)
            return
        dest = dest_dir / f"{src.stem}_copy{src.suffix}"
    shutil.move(str(src), str(dest))


def normalize_unit(unit: Path) -> None:
    usl = find_sub(unit, "Условие", "условие") or ensure(unit / "Условие")
    prim = find_sub(unit, "Примеры", "примеры") or ensure(unit / "Примеры")
    for item in list(unit.iterdir()):
        if item in (usl, prim) or skip(item):
            continue
        if item.is_file():
            if item.suffix.lower() in PDF | {".doc", ".docx"}:
                move_into(item, usl)
            else:
                move_into(item, prim)
    for f in list(prim.iterdir()) if prim.exists() else []:
        if f.is_file() and f.suffix.lower() in PDF:
            move_into(f, usl)


def normalize_root() -> None:
    ensure(SRC)
    files = [f for f in SRC.iterdir() if f.is_file() and not skip(f)]
    dirs = [d for d in SRC.iterdir() if d.is_dir()]
    if files and not dirs:
        unit = ensure(SRC / "01")
        for f in files:
            shutil.move(str(f), str(unit / f.name))
        dirs = [unit]
    for d in dirs:
        normalize_unit(d)


def units() -> list[Path]:
    out = []
    for d in SRC.iterdir():
        if not d.is_dir() or skip(d):
            continue
        if any(f.is_file() and not skip(f) for f in d.rglob("*")):
            out.append(d)
    return sorted(out, key=lambda p: natural_key(p.name))


def sync_unit(unit: Path) -> int:
    dest = ensure(DST / unit.name)
    n = 0
    for f in unit.rglob("*"):
        if not f.is_file() or skip(f):
            continue
        rel = f.relative_to(unit)
        target = dest / rel
        ensure(target.parent)
        if not target.exists() or f.stat().st_mtime > target.stat().st_mtime or f.stat().st_size != target.stat().st_size:
            shutil.copy2(f, target)
            n += 1
    return n


def collect(folder: Path | None, exts: set[str]) -> list[Path]:
    if not folder or not folder.exists():
        return []
    files = []
    for f in sorted(folder.rglob("*"), key=lambda p: natural_key(p.as_posix())):
        if f.is_file() and not skip(f) and f.suffix.lower() in exts:
            if f.suffix.lower() == ".pdf":
                try:
                    if not f.read_bytes()[:4].startswith(b"%PDF"):
                        continue
                except OSError:
                    continue
            files.append(f)
    return files


def label(name: str) -> tuple[str, str]:
    nums = re.findall(r"\d+", name)
    if re.fullmatch(r"\d+", name):
        num = name.zfill(2)
        return num, f"Контроль {num}"
    if len(nums) >= 2:
        a, b = nums[0].zfill(2), nums[-1].zfill(2)
        return f"{a}–{b}", f"Контроль {a}–{b}"
    if nums:
        num = nums[0].zfill(2)
        return num, f"Контроль {num}"
    return name[:4], name


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def rel_web(path: Path) -> str:
    return "../../" + path.relative_to(ROOT / "WEB_ALL").as_posix()


def build_group(unit: Path) -> str:
    num, title = label(unit.name)
    mat = DST / unit.name
    usl = find_sub(mat, "Условие", "условие")
    prim = find_sub(mat, "Примеры", "примеры")
    pdfs = collect(usl, PDF)
    htmls = collect(prim, HTML)
    for f in mat.iterdir():
        if f.is_file() and f.suffix.lower() in HTML and not skip(f):
            htmls.append(f)

    parts = [
        '<details class="lab-group">',
        f'<summary><span class="lab-group__num">{esc(num)}</span><span class="lab-group__name">{esc(title)}</span><span class="lab-group__chevron" aria-hidden="true"></span></summary>',
        '<div class="lab-group__body"><div class="lab-group__tree">',
    ]
    if pdfs:
        parts.append('<section class="lab-section">')
        parts.append('<h4 class="lab-section__title">Условие</h4>')
        parts.append('<ul class="lab-files">')
        for pdf in pdfs:
            href = rel_web(pdf)
            parts.append(
                f'    <li><a href="{href}" class="lab-files__link lab-files__link--pdf" target="_blank" rel="noopener noreferrer">{esc(pdf.stem)}</a></li>'
            )
        parts.append("</ul></section>")

    parts.append('<section class="lab-section lab-section--works">')
    parts.append('<h4 class="lab-section__title">Выполненное задание</h4>')
    parts.append('<ul class="lab-files">')
    if htmls:
        for html in htmls:
            href = rel_web(html)
            parts.append(
                f'    <li><a href="{href}" class="lab-files__link lab-files__link--html" data-material-src="{href}">{esc(html.name)}</a></li>'
            )
    else:
        parts.append('<li><span class="lab-catalog__empty">Пока нет работ</span></li>')
    parts.append("</ul></section>")
    parts.append("</div></div></details>")
    return "\n".join(parts)


def ensure_marks(text: str) -> str:
    if MARK_A in text and MARK_B in text:
        return text
    # migrate old markers
    text = text.replace("<!-- SYNC:CONTROL_START -->", MARK_A).replace("<!-- SYNC:CONTROL_END -->", MARK_B)
    if MARK_A in text and MARK_B in text:
        return text
    head = '<div class="lab-catalog__head">'
    viewer = '<div class="lab-layout__viewer'
    h = text.find(head)
    v = text.find(viewer)
    if h < 0 or v <= h:
        raise SystemExit("Не найден каталог в okr.html")
    head_end = text.find("</div>", h) + len("</div>")
    before = text[:v].rstrip()
    idx = before.rfind("</div>")
    before2 = before[:idx].rstrip()
    idx2 = before2.rfind("</div>")
    return text[:head_end] + f"\n\n{MARK_A}\n{MARK_B}\n" + text[idx2:]


def write_catalog(inner: str) -> None:
    text = ensure_marks(PAGE.read_text(encoding="utf-8"))
    block = f"{MARK_A}\n{inner.rstrip()}\n{MARK_B}" if inner.strip() else f"{MARK_A}\n{MARK_B}"
    pattern = re.compile(re.escape(MARK_A) + r".*?" + re.escape(MARK_B), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit("Маркеры не найдены в okr.html")
    PAGE.write_text(pattern.sub(block, text, count=1), encoding="utf-8")


def main() -> int:
    if not SRC.exists():
        print("Нет папки COURSE_4/CONTROL")
        return 1
    normalize_root()
    total = 0
    for u in units():
        total += sync_unit(u)
    groups = "\n\n".join(build_group(u) for u in units())
    write_catalog(groups)
    print(f"OKR: обновлено файлов {total}, групп {len(units())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
