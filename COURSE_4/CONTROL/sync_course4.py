#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Синхронизация COURSE_4 → WEB_ALL (4 курс).

Что делает:
  1. Нормализует папки LAB / LECTION / CONTROL
     (Условие, Примеры, Материалы; PDF → Условие/Материалы)
  2. Копирует материалы в WEB_ALL/materials/course-4/
  3. Пересобирает списки в lab.html / lection.html / okr.html
  4. Создаёт overview для новых лабораторных, если ещё нет

Запуск из корня репозитория:
  py -3 COURSE_4/CONTROL/sync_course4.py
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # CONTROL -> COURSE_4 -> repo
SRC = ROOT / "COURSE_4"
DST_MAT = ROOT / "WEB_ALL" / "materials" / "course-4"
PAGES = ROOT / "WEB_ALL" / "pages" / "course-4"

SKIP_NAMES = {".gitkeep", "thumbs.db", "desktop.ini", ".ds_store"}
# служебные файлы в CONTROL — не материалы ОКР
CONTROL_HELPERS = {"sync_course4.py", "как_подключить.txt"}
SKIP_HTML = {"page.html"}  # служебное окно для window.open
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".mp3", ".mp4", ".wav"}
HTML_EXTS = {".html", ".htm"}
PDF_EXTS = {".pdf"}
DOC_EXTS = {".pdf", ".docx", ".doc"}


def log(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


def is_skipped(path: Path) -> bool:
    name = path.name.lower()
    if name in SKIP_NAMES or path.name.startswith("~$"):
        return True
    if name in CONTROL_HELPERS or name.endswith(".py"):
        return True
    return False


def natural_key(name: str):
    parts = re.split(r"(\d+)", name)
    key = []
    for p in parts:
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p.lower()))
    return key


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def move_file(src: Path, dest_dir: Path) -> Path:
    ensure_dir(dest_dir)
    dest = dest_dir / src.name
    if dest.resolve() == src.resolve():
        return dest
    if dest.exists():
        if dest.stat().st_size == src.stat().st_size:
            src.unlink(missing_ok=True)
            return dest
        dest = dest_dir / f"{src.stem}_copy{src.suffix}"
    shutil.move(str(src), str(dest))
    return dest


def find_named_subdir(parent: Path, *names: str) -> Path | None:
    wanted = {n.lower() for n in names}
    for child in parent.iterdir():
        if child.is_dir() and child.name.lower() in wanted:
            return child
    return None


def normalize_lab(lab_dir: Path) -> None:
    """LAB/NN → Условие + Примеры."""
    uslovie = find_named_subdir(lab_dir, "Условие", "условие") or ensure_dir(lab_dir / "Условие")
    primery = find_named_subdir(lab_dir, "Примеры", "примеры") or ensure_dir(lab_dir / "Примеры")

    for item in list(lab_dir.iterdir()):
        if is_skipped(item) or item in (uslovie, primery):
            continue
        if item.is_file():
            ext = item.suffix.lower()
            if ext in DOC_EXTS:
                move_file(item, uslovie)
            elif ext in HTML_EXTS or ext in ASSET_EXTS or item.suffix.lower() == ".hta":
                move_file(item, primery)
            else:
                move_file(item, primery)
        elif item.is_dir() and item.name.lower() in {"image", "images", "img", "css", "js", "assets"}:
            target = primery / item.name
            if target.exists():
                for f in item.rglob("*"):
                    if f.is_file() and not is_skipped(f):
                        rel = f.relative_to(item)
                        dest = target / rel
                        ensure_dir(dest.parent)
                        shutil.copy2(f, dest)
                shutil.rmtree(item, ignore_errors=True)
            else:
                shutil.move(str(item), str(target))

    # PDF accidentally left in Примеры → Условие
    for f in list(primery.iterdir()):
        if f.is_file() and f.suffix.lower() in DOC_EXTS:
            move_file(f, uslovie)


def normalize_lection(lec_dir: Path) -> None:
    """LECTION/id → Материалы + примеры в корне."""
    materials = find_named_subdir(lec_dir, "Материалы", "материалы") or ensure_dir(lec_dir / "Материалы")

    for item in list(lec_dir.iterdir()):
        if is_skipped(item) or item == materials or (item.is_dir() and item.name.lower() in {"image", "images"}):
            continue
        if item.is_file() and item.suffix.lower() in DOC_EXTS:
            # fake pdf that is actually html → keep as .html demo in root
            head = item.read_bytes()[:20]
            if head.startswith(b"<!DOCTYPE") or head.startswith(b"<html") or head.startswith(b"\xef\xbb\xbf<!DOC"):
                html_name = item.with_suffix(".html").name
                # avoid clobbering existing good demos
                dest = lec_dir / html_name
                if not dest.exists():
                    dest.write_bytes(item.read_bytes())
                    log(f"  HTML-заглушка PDF → {lec_dir.name}/{html_name}")
                item.unlink(missing_ok=True)
            else:
                move_file(item, materials)


def normalize_control_unit(unit: Path) -> None:
    """CONTROL/NN или CONTROL/тема → Условие + Примеры."""
    if not unit.is_dir():
        return
    # Already structured
    if find_named_subdir(unit, "Условие", "Примеры", "Материалы"):
        uslovie = find_named_subdir(unit, "Условие", "условие") or ensure_dir(unit / "Условие")
        primery = find_named_subdir(unit, "Примеры", "примеры") or ensure_dir(unit / "Примеры")
        for f in list(unit.iterdir()):
            if f.is_file() and not is_skipped(f):
                if f.suffix.lower() in DOC_EXTS:
                    move_file(f, uslovie)
                else:
                    move_file(f, primery)
        for f in list(primery.iterdir()) if primery.exists() else []:
            if f.is_file() and f.suffix.lower() in DOC_EXTS:
                move_file(f, uslovie)
        return

    # Flat dump of files → wrap
    files = [f for f in unit.iterdir() if f.is_file() and not is_skipped(f)]
    dirs = [d for d in unit.iterdir() if d.is_dir()]
    if files and not dirs:
        uslovie = ensure_dir(unit / "Условие")
        primery = ensure_dir(unit / "Примеры")
        for f in files:
            if f.suffix.lower() in DOC_EXTS:
                move_file(f, uslovie)
            else:
                move_file(f, primery)


def normalize_control_root(control: Path) -> None:
    ensure_dir(control)
    # Служебные файлы (sync_course4.py и инструкция) не трогаем
    top_files = [f for f in control.iterdir() if f.is_file() and not is_skipped(f)]
    top_dirs = [d for d in control.iterdir() if d.is_dir()]
    if top_files and not top_dirs:
        unit = ensure_dir(control / "01")
        for f in top_files:
            shutil.move(str(f), str(unit / f.name))
        top_dirs = [unit]

    for d in top_dirs:
        normalize_control_unit(d)


def sync_control(src: Path, dst: Path) -> int:
    """Копирует только папки ОКР (01, 02…), не сам sync-скрипт."""
    if not src.exists():
        return 0
    count = 0
    ensure_dir(dst)
    for unit in list_units(src):
        count += sync_tree(unit, dst / unit.name)
    return count


def sync_tree(src: Path, dst: Path) -> int:
    """Copy all files from src to dst (merge). Returns file count."""
    if not src.exists():
        return 0
    count = 0
    ensure_dir(dst)
    for f in src.rglob("*"):
        if not f.is_file() or is_skipped(f):
            continue
        rel = f.relative_to(src)
        dest = dst / rel
        ensure_dir(dest.parent)
        if not dest.exists() or f.stat().st_mtime > dest.stat().st_mtime or f.stat().st_size != dest.stat().st_size:
            shutil.copy2(f, dest)
            count += 1
    return count


def list_units(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        [d for d in folder.iterdir() if d.is_dir() and not is_skipped(d) and any(f.is_file() for f in d.rglob("*") if not is_skipped(f))],
        key=lambda p: natural_key(p.name),
    )


def display_label(folder_name: str, kind: str) -> tuple[str, str]:
    """Return (num_badge, title)."""
    name = folder_name.strip()
    if re.fullmatch(r"\d+", name):
        num = name.zfill(2)
        if kind == "lab":
            return num, f"Лабораторная {num}"
        if kind == "control":
            return num, f"Контроль {num}"
        return num, f"Лекция {num}"

    # 4_5_6 / 7-8-9 / 04-06
    nums = re.findall(r"\d+", name)
    if len(nums) >= 2:
        a, b = nums[0].zfill(2), nums[-1].zfill(2)
        badge = f"{a}–{b}"
        if kind == "lab":
            return badge, f"Лабораторные {a}–{b}"
        if kind == "control":
            return badge, f"Контроль {a}–{b}"
        return badge, f"Лекции {a}–{b}"

    if nums:
        num = nums[0].zfill(2)
        title = name
        if kind == "lab":
            title = f"Лабораторная {num}"
        elif kind == "lection":
            title = f"Лекция {num}"
        elif kind == "control":
            title = f"Контроль {num}"
        return num, title

    return name[:4], name


def rel_web(path: Path) -> str:
    """Path relative to pages/course-4 → ../../materials/..."""
    return "../../" + path.relative_to(ROOT / "WEB_ALL").as_posix()


def html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def is_real_pdf(path: Path) -> bool:
    if path.suffix.lower() != ".pdf":
        return False
    try:
        head = path.read_bytes()[:16]
    except OSError:
        return False
    return head.startswith(b"%PDF")


def collect_files(folder: Path, exts: set[str]) -> list[Path]:
    if not folder or not folder.exists():
        return []
    out = []
    for f in sorted(folder.rglob("*"), key=lambda p: natural_key(p.as_posix())):
        if f.is_file() and not is_skipped(f) and f.suffix.lower() in exts:
            if f.name.lower() in SKIP_HTML:
                continue
            if f.suffix.lower() == ".pdf" and not is_real_pdf(f):
                continue
            out.append(f)
    return out


def build_lab_group(lab_id: str, mat_dir: Path) -> str:
    num, title = display_label(lab_id, "lab")
    uslovie = find_named_subdir(mat_dir, "Условие", "условие")
    primery = find_named_subdir(mat_dir, "Примеры", "примеры")
    pdfs = collect_files(uslovie, PDF_EXTS) if uslovie else []
    htmls = collect_files(primery, HTML_EXTS) if primery else []

    parts = [
        f'<details class="lab-group">',
        f'<summary><span class="lab-group__num">{html_escape(num)}</span><span class="lab-group__name">{html_escape(title)}</span><span class="lab-group__chevron" aria-hidden="true"></span></summary>',
        f'<div class="lab-group__body"><div class="lab-group__tree">',
    ]

    if pdfs:
        parts.append('<section class="lab-section">')
        parts.append('<h4 class="lab-section__title">Условие</h4>')
        parts.append('<ul class="lab-files">')
        for pdf in pdfs:
            href = rel_web(pdf)
            label = pdf.stem
            parts.append(
                f'    <li><a href="{href}" class="lab-files__link lab-files__link--pdf" target="_blank" rel="noopener noreferrer">{html_escape(label)}</a></li>'
            )
        parts.append("</ul></section>")

    overview = PAGES / "overviews" / f"lab-{lab_id.zfill(2) if lab_id.isdigit() else lab_id}.html"
    # overview naming: lab-01.html for digit ids; lab-06.html
    ov_name = f"lab-{lab_id.zfill(2)}.html" if lab_id.isdigit() else f"lab-{lab_id}.html"
    overview = PAGES / "overviews" / ov_name
    parts.append('<section class="lab-section lab-section--desc">')
    parts.append('<h4 class="lab-section__title">Описание</h4>')
    parts.append('<ul class="lab-files">')
    if overview.exists():
        parts.append(
            f'<li><a href="overviews/{overview.name}" class="lab-files__link lab-files__link--overview" data-material-src="overviews/{overview.name}">Описание занятия</a></li>'
        )
    else:
        parts.append('<li><span class="lab-catalog__empty">Пока нет описания</span></li>')
    parts.append("</ul></section>")

    parts.append('<section class="lab-section lab-section--works">')
    parts.append('<h4 class="lab-section__title">Выполненное задание</h4>')
    parts.append('<ul class="lab-files">')
    if htmls:
        for html in htmls:
            href = rel_web(html)
            parts.append(
                f'    <li><a href="{href}" class="lab-files__link lab-files__link--html" data-material-src="{href}">{html_escape(html.name)}</a></li>'
            )
    else:
        parts.append('<li><span class="lab-catalog__empty">Пока нет HTML-работ</span></li>')
    parts.append("</ul></section>")
    parts.append("</div></div></details>")
    return "\n".join(parts)


def build_lection_group(lec_id: str, mat_dir: Path) -> str:
    num, title = display_label(lec_id, "lection")
    materials = find_named_subdir(mat_dir, "Материалы", "материалы")
    pdfs = collect_files(materials, PDF_EXTS) if materials else []
    # demos / works in root (and nested except Материалы/image handled via rglob on root excluding Материалы pdfs already)
    htmls = []
    for f in sorted(mat_dir.rglob("*"), key=lambda p: natural_key(p.as_posix())):
        if not f.is_file() or is_skipped(f):
            continue
        if materials and materials in f.parents:
            # allow html demos mistakenly in Материалы
            if f.suffix.lower() in HTML_EXTS:
                htmls.append(f)
            continue
        if f.suffix.lower() in HTML_EXTS and f.name.lower() not in SKIP_HTML:
            htmls.append(f)
        if f.suffix.lower() == ".hta":
            htmls.append(f)

    parts = [
        f'<details class="lab-group">',
        f'<summary><span class="lab-group__num">{html_escape(num)}</span><span class="lab-group__name">{html_escape(title)}</span><span class="lab-group__chevron" aria-hidden="true"></span></summary>',
        f'<div class="lab-group__body"><div class="lab-group__tree">',
    ]

    parts.append('<section class="lab-section">')
    parts.append('<h4 class="lab-section__title">Материалы лекции</h4>')
    parts.append('<ul class="lab-files">')
    if pdfs:
        for pdf in pdfs:
            href = rel_web(pdf)
            parts.append(
                f'    <li><a href="{href}" class="lab-files__link lab-files__link--pdf" target="_blank" rel="noopener noreferrer">{html_escape(pdf.stem)}</a></li>'
            )
    else:
        # html materials as fallback demos
        mat_html = [h for h in htmls if materials and materials in h.parents]
        if mat_html:
            for h in mat_html:
                href = rel_web(h)
                parts.append(
                    f'    <li><a href="{href}" class="lab-files__link lab-files__link--html" data-material-src="{href}">{html_escape(h.name)}</a></li>'
                )
                htmls = [x for x in htmls if x != h]
        else:
            parts.append('<li><span class="lab-catalog__empty">Пока нет материалов</span></li>')
    parts.append("</ul></section>")

    parts.append('<section class="lab-section lab-section--works">')
    parts.append('<h4 class="lab-section__title">Выполненное задание</h4>')
    parts.append('<ul class="lab-files">')
    work_htmls = [h for h in htmls if not (materials and materials in h.parents)]
    if work_htmls:
        for html in work_htmls:
            href = rel_web(html)
            if html.suffix.lower() == ".hta":
                parts.append(
                    f'    <li><a href="{href}" class="lab-files__link lab-files__link--html" target="_blank" rel="noopener noreferrer">{html_escape(html.name)}</a></li>'
                )
            else:
                parts.append(
                    f'    <li><a href="{href}" class="lab-files__link lab-files__link--html" data-material-src="{href}">{html_escape(html.name)}</a></li>'
                )
    else:
        parts.append('<li><span class="lab-catalog__empty">Пока нет примеров</span></li>')
    parts.append("</ul></section>")
    parts.append("</div></div></details>")
    return "\n".join(parts)


def build_control_group(unit_id: str, mat_dir: Path) -> str:
    num, title = display_label(unit_id, "control")
    uslovie = find_named_subdir(mat_dir, "Условие", "условие")
    primery = find_named_subdir(mat_dir, "Примеры", "примеры")
    materials = find_named_subdir(mat_dir, "Материалы", "материалы")
    pdfs = []
    if uslovie:
        pdfs.extend(collect_files(uslovie, PDF_EXTS))
    if materials:
        pdfs.extend(collect_files(materials, PDF_EXTS))
    htmls = collect_files(primery, HTML_EXTS) if primery else []
    # also root html
    for f in mat_dir.iterdir():
        if f.is_file() and f.suffix.lower() in HTML_EXTS and not is_skipped(f):
            htmls.append(f)

    parts = [
        f'<details class="lab-group">',
        f'<summary><span class="lab-group__num">{html_escape(num)}</span><span class="lab-group__name">{html_escape(title)}</span><span class="lab-group__chevron" aria-hidden="true"></span></summary>',
        f'<div class="lab-group__body"><div class="lab-group__tree">',
    ]

    if pdfs:
        parts.append('<section class="lab-section">')
        parts.append('<h4 class="lab-section__title">Условие</h4>')
        parts.append('<ul class="lab-files">')
        for pdf in pdfs:
            href = rel_web(pdf)
            parts.append(
                f'    <li><a href="{href}" class="lab-files__link lab-files__link--pdf" target="_blank" rel="noopener noreferrer">{html_escape(pdf.stem)}</a></li>'
            )
        parts.append("</ul></section>")

    parts.append('<section class="lab-section lab-section--works">')
    parts.append('<h4 class="lab-section__title">Выполненное задание</h4>')
    parts.append('<ul class="lab-files">')
    if htmls:
        for html in htmls:
            href = rel_web(html)
            parts.append(
                f'    <li><a href="{href}" class="lab-files__link lab-files__link--html" data-material-src="{href}">{html_escape(html.name)}</a></li>'
            )
    else:
        parts.append('<li><span class="lab-catalog__empty">Пока нет работ</span></li>')
    parts.append("</ul></section>")
    parts.append("</div></div></details>")
    return "\n".join(parts)


def replace_marked_block(html_path: Path, start: str, end: str, inner: str) -> None:
    text = html_path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    block = f"{start}\n{inner.rstrip()}\n{end}"
    if not pattern.search(text):
        raise SystemExit(f"Маркеры не найдены в {html_path}: {start} … {end}")
    html_path.write_text(pattern.sub(block, text, count=1), encoding="utf-8")
    log(f"  обновлён {html_path.relative_to(ROOT)}")


OVERVIEW_META = {
    "01": {
        "title": "Лаб 01 — окна и диалоги",
        "topics": ["alert, confirm, prompt", "window.open / focus / blur", "resizeBy", "setInterval / clearInterval"],
        "summary": "Диалоговые окна браузера, открытие нового окна и работа с таймером.",
        "story": "В 3_05.html — alert, confirm и prompt. В 3_06.html открывается отдельное окно с заданными параметрами. В 3_07.html — ввод адреса, focus/blur и изменение размера окна через resizeBy. В 3_08.html — счётчик на setInterval и остановка таймера.",
    },
    "02": {
        "title": "Лаб 02 — объект document",
        "topics": ["свойства document", "запись в документ", "цвета и фон", "работа с формами"],
        "summary": "Свойства объекта document и вывод информации на страницу.",
        "story": "Примеры 3_09–3_11 и 6.html — свойства document, цвета страницы и простая работа с содержимым.",
    },
    "03": {
        "title": "Лаб 03 — доступ к HTML-элементам",
        "topics": ["getElementById / getElementsBy*", "innerHTML / innerText", "коллекции элементов", "самостоятельная работа"],
        "summary": "Поиск элементов в DOM и изменение их содержимого.",
        "story": "elements_control, inner, p319, p322 и independent_work — доступ к узлам и правка содержимого страницы.",
    },
    "04": {
        "title": "Лаб 04 — анимация и drag-and-drop",
        "topics": ["покадровая анимация изображений", "слайдер", "drag and drop", "эффекты при наведении"],
        "summary": "Перемещение картинок по таймеру, слайдер, флаги drag-and-drop и эффекты zoom / пульсация.",
        "story": "В anim.html и ind.html — перемещение картинки по сетке через смену src. В slider.html — переключение изображений. В drag_and_drop_flagi.html — перетаскивание флагов. В task1_* — эффекты при наведении.",
    },
    "06": {
        "title": "Лаб 06 — изменение структуры DOM",
        "topics": ["appendChild / insertBefore", "removeChild / replaceChild", "cloneNode", "самостоятельная работа"],
        "summary": "Создание, вставка, клонирование и удаление узлов в дереве документа.",
        "story": "В appendChild, insertBefore, cloneNode, replaceChild, removeChild и removeallchild — операции над дочерними узлами. В ind.html — самостоятельная работа со списком элементов.",
    },
}


def overview_shell(lab_id: str, meta: dict, work_links: list[tuple[str, str]]) -> str:
    topics = "\n".join(f"        <li>{html_escape(t)}</li>" for t in meta["topics"])
    works = "\n".join(
        f'            <li><a href="{href}">{html_escape(label)}</a></li>' for href, label in work_links
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Обзор — Лаб {html_escape(lab_id)} — Программные средства создания интернет-приложений</title>
    <link rel="stylesheet" href="../../../css/main.css">
</head>
<body class="site-app">
    <div class="site-grid">
        <header class="site-header">
            <a class="site-header__logo site-header__logo--personal" href="../../../course-4.html" title="На главную">
                <img src="../../../assets/images/Logo.png" alt="Логотип — Слепцов П.Л.">
            </a>
            <h1 class="site-header__title">
                <span class="site-header__title-top">4 курс</span>
                <span class="site-header__title-sub">Программные средства создания интернет-приложений</span>
            </h1>
            <span class="site-header__logo site-header__logo--college" title="БТЭУ ПК">
                <img src="../../../assets/images/college-logo.png" alt="Логотип колледжа">
            </span>
        </header>
        <div class="nav-backdrop"></div>
        <button type="button" class="nav-toggle" aria-label="Открыть меню" aria-expanded="false">
            <svg class="nav-toggle__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path class="nav-toggle__path nav-toggle__path--1" d="M4 7h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"></path>
                <path class="nav-toggle__path nav-toggle__path--2" d="M4 12h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"></path>
                <path class="nav-toggle__path nav-toggle__path--3" d="M4 17h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"></path>
            </svg>
        </button>
        <nav class="site-sidebar" aria-label="Меню">
            <h2>Разделы</h2>
            <ul class="site-nav">
                <li><a href="../../../course-4.html">Главная</a></li>
                <li><a href="../lab.html" class="is-active">Лабораторные</a></li>
                <li><a href="../lection.html">Лекции</a></li>
                <li><a href="../okr.html">Контроль</a></li>
                <li><a href="../../../index.html">Курсы</a></li>
            </ul>
        </nav>
        <main class="site-main page page--overview">
            <p class="overview-back"><a href="../lab.html">← К списку лабораторных</a></p>
            <article class="day-overview">
        <header class="day-overview__header">
<h2 class="day-overview__title">{html_escape(meta["title"])}</h2>
</header>
        <ul class="day-overview__topics">
{topics}
        </ul>
        <p class="day-overview__summary">{html_escape(meta["summary"])}</p>
        <section class="site-frame site-frame--story">
            <h3>Что я сделал</h3>
            <p class="day-overview__story">{html_escape(meta["story"])}</p>
        </section>
        <section class="site-frame site-frame--works">
        <h3>Выполненные работы</h3>
        <ul class="day-files">
{works}
        </ul>
    </section>
</article>
        </main>
        <aside class="site-aside" aria-label="Реклама">
            <p class="site-aside__title">Реклама</p>
            <a class="ad-card" href="https://github.com/PavelCRG" target="_blank" rel="noopener noreferrer">
                <div class="ad-card__head">
                    <img class="ad-card__logo" src="../../../assets/images/github.svg" alt="GitHub" width="56" height="56">
                    <strong class="ad-card__brand">PavelCRG</strong>
                </div>
                <p class="ad-card__text">Репозиторий автора: учебные работы по курсу и другие проекты.</p>
                <span class="ad-card__url">github.com/PavelCRG</span>
            </a>
            <a class="ad-card" href="https://voxivaai.vercel.app/" target="_blank" rel="noopener noreferrer">
                <div class="ad-card__head">
                    <img class="ad-card__logo" src="../../../assets/images/voxiva-logo.svg" alt="Voxiva" width="56" height="56">
                    <strong class="ad-card__brand">Voxiva</strong>
                </div>
                <p class="ad-card__text">Личный проект. Voxiva Space — терминалы и агенты. Voxiva Voice — диктовка в любое поле.</p>
                <span class="ad-card__url">voxivaai.vercel.app</span>
            </a>
            <a class="ad-card ad-card--text" href="https://github.com/PavelCRG" target="_blank" rel="noopener noreferrer">
                <div class="ad-card__head">
                    <strong class="ad-card__brand">Павел CRG</strong>
                    <span class="ad-card__sub">Портфолио</span>
                </div>
                <p class="ad-card__text">Работы, проекты и учебные материалы автора.</p>
            </a>
        </aside>
        <footer class="site-footer">
            <p class="site-footer__brand">Программные средства создания интернет-приложений</p>
            <p class="site-footer__college"><a href="https://mtk-bks.by/" target="_blank" rel="noopener">Минский филиал БТЭУ ПК</a></p>
            <p class="site-footer__copy">&copy; Слепцов Павел Леонидович</p>
        </footer>
    </div>
    <script src="../../../js/nav/mobile-nav.js"></script>
</body>
</html>
"""


def ensure_lab_overview(lab_id: str, mat_dir: Path) -> None:
    if not lab_id.isdigit():
        return
    ov_path = PAGES / "overviews" / f"lab-{lab_id.zfill(2)}.html"
    if ov_path.exists():
        return

    meta = OVERVIEW_META.get(lab_id.zfill(2))
    if not meta:
        meta = {
            "title": f"Лаб {lab_id.zfill(2)}",
            "topics": ["материалы занятия"],
            "summary": "Описание появится после заполнения.",
            "story": "Работы из папки Примеры.",
        }
    primery = find_named_subdir(mat_dir, "Примеры", "примеры")
    htmls = collect_files(primery, HTML_EXTS) if primery else []
    links = [("../../../" + h.relative_to(ROOT / "WEB_ALL").as_posix(), f"Примеры / {h.name}") for h in htmls]

    ensure_dir(ov_path.parent)
    ov_path.write_text(overview_shell(lab_id.zfill(2), meta, links), encoding="utf-8")
    log(f"  overview: {ov_path.relative_to(ROOT)}")


def remove_stale_lection_4() -> None:
    """Old materials/lection/4 after rename to 4_5_6."""
    old = DST_MAT / "lection" / "4"
    new = DST_MAT / "lection" / "4_5_6"
    if old.exists() and new.exists():
        shutil.rmtree(old)
        log("  удалена устаревшая materials/lection/4 (есть 4_5_6)")


def main() -> int:
    if not SRC.exists():
        log(f"Нет папки {SRC}")
        return 1

    log("=== 1. Нормализация COURSE_4 ===")
    for lab in list_units(SRC / "LAB") or sorted((SRC / "LAB").iterdir() if (SRC / "LAB").exists() else []):
        if lab.is_dir():
            log(f"LAB/{lab.name}")
            normalize_lab(lab)
    for lec in list_units(SRC / "LECTION") or []:
        log(f"LECTION/{lec.name}")
        normalize_lection(lec)
    if (SRC / "CONTROL").exists():
        log("CONTROL")
        normalize_control_root(SRC / "CONTROL")

    log("\n=== 2. Копирование в WEB_ALL/materials/course-4 ===")
    n_lab = sync_tree(SRC / "LAB", DST_MAT / "lab")
    n_lec = sync_tree(SRC / "LECTION", DST_MAT / "lection")
    n_ctl = sync_control(SRC / "CONTROL", DST_MAT / "control")
    log(f"  lab: {n_lab} файлов обновлено, lection: {n_lec}, control: {n_ctl}")
    remove_stale_lection_4()

    log("\n=== 3. Overview лабораторных ===")
    for lab in list_units(DST_MAT / "lab"):
        ensure_lab_overview(lab.name, lab)

    log("\n=== 4. Каталоги страниц ===")
    lab_page = PAGES / "lab.html"
    lec_page = PAGES / "lection.html"
    okr_page = PAGES / "okr.html"

    def ensure_sync_markers(page: Path, start: str, end: str) -> None:
        text = page.read_text(encoding="utf-8")
        if start in text and end in text:
            return
        head_key = '<div class="lab-catalog__head">'
        viewer_key = '<div class="lab-layout__viewer'
        h = text.find(head_key)
        v = text.find(viewer_key)
        if h < 0 or v <= h:
            raise SystemExit(f"Не найден каталог в {page}")
        head_close = text.find("</div>", h)
        head_end = head_close + len("</div>")
        before = text[:v].rstrip()
        idx = before.rfind("</div>")
        before2 = before[:idx].rstrip()
        idx2 = before2.rfind("</div>")
        new = text[:head_end] + f"\n\n{start}\n{end}\n" + text[idx2:]
        page.write_text(new, encoding="utf-8")
        log(f"  markers: {page.name}")

    ensure_sync_markers(lab_page, "<!-- SYNC:LAB_START -->", "<!-- SYNC:LAB_END -->")
    ensure_sync_markers(lec_page, "<!-- SYNC:LECTION_START -->", "<!-- SYNC:LECTION_END -->")
    ensure_sync_markers(okr_page, "<!-- SYNC:CONTROL_START -->", "<!-- SYNC:CONTROL_END -->")

    lab_groups = "\n\n".join(build_lab_group(u.name, u) for u in list_units(DST_MAT / "lab"))
    lec_groups = "\n\n".join(build_lection_group(u.name, u) for u in list_units(DST_MAT / "lection"))
    ctl_units = list_units(DST_MAT / "control")
    if ctl_units:
        ctl_groups = "\n\n".join(build_control_group(u.name, u) for u in ctl_units)
    else:
        ctl_groups = ""

    replace_marked_block(lab_page, "<!-- SYNC:LAB_START -->", "<!-- SYNC:LAB_END -->", lab_groups)
    replace_marked_block(lec_page, "<!-- SYNC:LECTION_START -->", "<!-- SYNC:LECTION_END -->", lec_groups)
    replace_marked_block(okr_page, "<!-- SYNC:CONTROL_START -->", "<!-- SYNC:CONTROL_END -->", ctl_groups)

    log("")
    log("Готово. Проверь Лабораторные / Лекции / Контроль в WEB_ALL.")
    log("Дальше: файлы в COURSE_4 -> двойной клик COURSE_4\\CONTROL\\sync_course4.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
