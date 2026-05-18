# -*- coding: utf-8 -*-
"""Сборка сайта WEB-практика из оригиналов День_1 … День_6.

Запуск: py -3 WEB_PRACTICE/WEB/build_site.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent
PRACTICE = ROOT.parent

GROUP_IB = "31ИБ"
GRID_SHELL_FILENAME = "zad3_p211-213.html"

# iframe в исходниках; в WEB заменяется на панели + CSS :target
RE_WORK_FRAME_IFRAME = re.compile(
    r"(?is)<iframe[^>]*\bname=[\"']work-frame[\"'][^>]*>\s*</iframe>|"
    r"<iframe[^>]*\bname=[\"']work-frame[\"'][^>]*/>",
)
RE_INDEX_DEMO_LINK = re.compile(r"(?i)\bhref\s*=\s*[\"']index(\d+)\.html[\"']")
RE_TARGET_WORK_FRAME = re.compile(r"(?i)\s*target\s*=\s*[\"']work-frame[\"']")

# Смещения из макета zad1.3 (боковая колонка) — в контенте не нужны
LAB_OFFSET_PROPS = frozenset({
    "margin-left", "margin-right", "left", "right", "float", "position", "clear",
})

DAY_LABELS = {
    "den-1": "День 1",
    "den-2": "День 2",
    "den-3": "День 3",
    "den-4": "День 4",
    "den-5": "День 5",
    "den-6": "День 6",
}

COPY_MAP = [
    (PRACTICE / "День_1_11.05.2026/Примеры", ROOT / "den-1/primery", "*.html"),
    (PRACTICE / "День_2_12.05.2026/Примеры/zad1/zad1.3", ROOT / "den-2/zad1", "*.html"),
    (PRACTICE / "День_2_12.05.2026/Примеры/zad1", ROOT / "den-2/zad1", "zad1.2_p164-165.html"),
    (PRACTICE / "День_2_12.05.2026/Примеры/zad2/zad2.3", ROOT / "den-2/zad2/zad2.3", "*"),
    (PRACTICE / "День_2_12.05.2026/Примеры/zad2", ROOT / "den-2/zad2", "zad2.2_p176-177.html"),
    (PRACTICE / "День_2_12.05.2026/Примеры/zad2", ROOT / "den-2/zad2", "2_29.css"),
    (PRACTICE / "День_2_12.05.2026/Примеры/zad3", ROOT / "den-2/zad3", "*"),
    (PRACTICE / "День_3_13.05.2026/Примеры", ROOT / "den-3/primery", "*.html"),
    (PRACTICE / "День_3_13.05.2026/Индивидуальное/table", ROOT / "den-3/tablitsa", "**/*"),
    (PRACTICE / "День_4_14.05.2026/Примеры", ROOT / "den-4/primery", "**/*"),
    (PRACTICE / "День_5_15.05.2026/Примеры", ROOT / "den-5/primery", "**/*"),
    (PRACTICE / "День_5_15.05.2026/Примеры из презентации", ROOT / "den-5/prezentaciya", "**/*"),
    (PRACTICE / "День_5_15.05.2026/Индивидуальное/index.html", ROOT / "den-5/individualnoe/index.html", None),
    (PRACTICE / "День_6_16.05.2026/Примеры/Формы_в_таблице", ROOT / "den-6/formy", "**/*"),
    (PRACTICE / "День_6_16.05.2026/Примеры/Анкета_регистрации", ROOT / "den-6/anketa", "**/*"),
]

# (исходник в День_*, относительный путь в WEB)
HTML_SOURCES: list[tuple[Path, str]] = []


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_copy_map() -> Iterator[tuple[Path, Path, str | None]]:
    for item in COPY_MAP:
        yield item[0], item[1], item[2] if len(item) > 2 else None


def register_html(src: Path, web_rel: str) -> None:
    if src.suffix.lower() != ".html":
        return
    if not src.is_file():
        return
    pair = (src, web_rel.replace("\\", "/"))
    if pair not in HTML_SOURCES:
        HTML_SOURCES.append(pair)


def scan_sources() -> None:
    HTML_SOURCES.clear()
    for src_root, dst_root, pattern in iter_copy_map():
        if src_root.is_file():
            register_html(src_root, str(dst_root.relative_to(ROOT)).replace("\\", "/"))
            continue
        if not src_root.exists():
            continue
        if pattern == "**/*":
            for f in sorted(src_root.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(src_root)
                    register_html(f, str((dst_root / rel).relative_to(ROOT)).replace("\\", "/"))
        elif pattern == "*":
            for f in sorted(src_root.iterdir()):
                if f.is_file():
                    register_html(f, str((dst_root / f.name).relative_to(ROOT)).replace("\\", "/"))
        elif pattern and "*" in pattern:
            for f in sorted(src_root.glob(pattern)):
                if f.is_file():
                    register_html(f, str((dst_root / f.name).relative_to(ROOT)).replace("\\", "/"))
        else:
            for f in sorted(src_root.glob("*.html")):
                register_html(f, str((dst_root / f.name).relative_to(ROOT)).replace("\\", "/"))


def copy_assets() -> None:
    """Копирует всё кроме HTML (HTML собирается из оригинала при обёртке)."""
    for src_root, dst_root, pattern in iter_copy_map():
        if src_root.is_file():
            dst_root.parent.mkdir(parents=True, exist_ok=True)
            if src_root.suffix.lower() != ".html":
                shutil.copy2(src_root, dst_root)
            continue
        if not src_root.exists():
            continue
        if pattern == "**/*":
            if dst_root.exists():
                shutil.rmtree(dst_root)
            shutil.copytree(src_root, dst_root)
            for html in dst_root.rglob("*.html"):
                html.unlink()
        elif pattern == "*":
            dst_root.mkdir(parents=True, exist_ok=True)
            for f in src_root.iterdir():
                if f.is_file() and f.suffix.lower() != ".html":
                    shutil.copy2(f, dst_root / f.name)
        elif pattern and "*" in pattern:
            dst_root.mkdir(parents=True, exist_ok=True)
            for f in src_root.glob(pattern):
                if f.is_file() and f.suffix.lower() != ".html":
                    shutil.copy2(f, dst_root / f.name)


def get_menu_structure() -> list:
    """Меню: названия дней и файлов как в папках День_1 … День_6."""
    flex = [(f"index{i}.html", f"den-2/zad2/zad2.3/index{i}.html") for i in range(1, 16)]
    flex.append(("zad3_p211-213.html", "den-2/zad2/zad2.3/zad3_p211-213.html"))
    zad3 = [(f"index{i}.html", f"den-2/zad3/index{i}.html") for i in range(1, 12)]
    zad3.append(("zad3_p211-213.html", "den-2/zad3/zad3_p211-213.html"))
    prez = [(f"{i}/index.html", f"den-5/prezentaciya/{i}/index.html") for i in range(1, 14)]
    tab_moto = [
        ("Tourist.html", "den-3/tablitsa/moto/sub_section/Tourist.html"),
        ("Enduro.html", "den-3/tablitsa/moto/sub_section/Enduro.html"),
        ("Chopper.html", "den-3/tablitsa/moto/sub_section/Chopper.html"),
        ("Sport.html", "den-3/tablitsa/moto/sub_section/Sport.html"),
    ]
    tab_ship = [
        ("Boat.html", "den-3/tablitsa/ship/sub_section/Boat.html"),
        ("Yacht.html", "den-3/tablitsa/ship/sub_section/Yacht.html"),
    ]
    forms = [
        ("1_поиск/index.html", "den-6/formy/1_поиск/index.html"),
        ("2_поиск_обязательная/index.html", "den-6/formy/2_поиск_обязательная/index.html"),
        ("3_авторизация/index.html", "den-6/formy/3_авторизация/index.html"),
        ("4_опрос/index.html", "den-6/formy/4_опрос/index.html"),
        ("5_отзыв/index.html", "den-6/formy/5_отзыв/index.html"),
        ("6_города/index.html", "den-6/formy/6_города/index.html"),
        ("7_загрузка/index.html", "den-6/formy/7_загрузка/index.html"),
        ("8_валидация/index.html", "den-6/formy/8_валидация/index.html"),
    ]
    return [
        ("Главная", "index.html", None),
        (
            DAY_LABELS["den-1"],
            "den-1/index.html",
            [
                ("_sec_", "Примеры", [
                    ("python_part1.html", "den-1/primery/python_part1.html"),
                    ("python_part2.html", "den-1/primery/python_part2.html"),
                    ("python_part3.html", "den-1/primery/python_part3.html"),
                    ("add.html", "den-1/primery/add.html"),
                ]),
            ],
        ),
        (
            DAY_LABELS["den-2"],
            "den-2/index.html",
            [
                ("_sec_", "zad1/zad1.3", [
                    ("zad1.3.html", "den-2/zad1/zad1.3.html"),
                    ("spiski.html", "den-2/zad1/spiski.html"),
                    ("ssilki.html", "den-2/zad1/ssilki.html"),
                    ("tablitsi.html", "den-2/zad1/tablitsi.html"),
                    ("formi.html", "den-2/zad1/formi.html"),
                    ("formatirovanie.html", "den-2/zad1/formatirovanie.html"),
                ]),
                ("_sec_", "zad2/zad2.3", flex),
                ("_sec_", "zad3", zad3),
                ("zad2/zad2.2_p176-177.html", "den-2/zad2/zad2.2_p176-177.html"),
                ("zad1/zad1.2_p164-165.html", "den-2/zad1/zad1.2_p164-165.html"),
            ],
        ),
        (
            DAY_LABELS["den-3"],
            "den-3/index.html",
            [
                ("_sec_", "Примеры", [
                    ("python_part1.html", "den-3/primery/python_part1.html"),
                    ("python_part2.html", "den-3/primery/python_part2.html"),
                    ("python_part3.html", "den-3/primery/python_part3.html"),
                ]),
                ("_sec_", "Индивидуальное/table", [
                    ("main.html", "den-3/tablitsa/main.html"),
                ]),
                ("_sec_", "moto", [("moto.html", "den-3/tablitsa/moto/moto.html")] + tab_moto),
                ("_sec_", "ship", [("ship.html", "den-3/tablitsa/ship/ship.html")] + tab_ship),
            ],
        ),
        (
            DAY_LABELS["den-4"],
            "den-4/index.html",
            [
                ("_sec_", "Примеры", [
                    ("python_01_link_img.html", "den-4/primery/python_01_link_img.html"),
                    ("python_02_link_img.html", "den-4/primery/python_02_link_img.html"),
                    ("python_03_link_img.html", "den-4/primery/python_03_link_img.html"),
                ]),
            ],
        ),
        (
            DAY_LABELS["den-5"],
            "den-5/index.html",
            [
                ("_sec_", "Примеры", [
                    ("python_01_link_img.html", "den-5/primery/python_01_link_img.html"),
                    ("python_02_link_img.html", "den-5/primery/python_02_link_img.html"),
                    ("python_03_link_img.html", "den-5/primery/python_03_link_img.html"),
                ]),
                ("_sec_", "Примеры/import_style", [
                    ("python_01.html", "den-5/primery/import_style/python_01.html"),
                    ("python_02.html", "den-5/primery/import_style/python_02.html"),
                    ("python_03.html", "den-5/primery/import_style/python_03.html"),
                ]),
                ("_sec_", "Примеры/link_style", [
                    ("python_01.html", "den-5/primery/link_style/python_01.html"),
                    ("python_02.html", "den-5/primery/link_style/python_02.html"),
                    ("python_03.html", "den-5/primery/link_style/python_03.html"),
                ]),
                ("_sec_", "Примеры/style_media", [
                    ("python_01.html", "den-5/primery/style_media/python_01.html"),
                    ("python_02.html", "den-5/primery/style_media/python_02.html"),
                    ("python_03.html", "den-5/primery/style_media/python_03.html"),
                ]),
                ("_sec_", "Примеры/master_import", [
                    ("python_01.html", "den-5/primery/master_import/python_01.html"),
                    ("python_02.html", "den-5/primery/master_import/python_02.html"),
                    ("python_03.html", "den-5/primery/master_import/python_03.html"),
                ]),
                ("_sec_", "Примеры из презентации", prez),
                ("Индивидуальное/index.html", "den-5/individualnoe/index.html"),
            ],
        ),
        (
            DAY_LABELS["den-6"],
            "den-6/index.html",
            [
                ("_sec_", "Формы_в_таблице", forms),
                ("Анкета_регистрации/index.html", "den-6/anketa/index.html"),
            ],
        ),
    ]


def all_hrefs_in_menu(menu: list) -> set[str]:
    found: set[str] = set()

    def walk(items):
        if not items:
            return
        for it in items:
            if isinstance(it, tuple) and len(it) == 3 and it[0] == "_sec_":
                walk(it[2])
            elif isinstance(it, tuple) and len(it) == 2:
                found.add(it[1])

    for entry in menu:
        if entry[2] is None:
            found.add(entry[1])
        else:
            found.add(entry[1])
            walk(entry[2])
    return found


def menu_day_open(day_href: str, sections, active: str) -> bool:
    if active == day_href or active.startswith(day_href.rsplit("/", 1)[0] + "/"):
        return True
    return active in all_hrefs_in_menu([("x", day_href, sections)])


def menu_section_open(links, active: str) -> bool:
    return any(href == active for _, href in links)


def iter_menu_file_links(sections) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for item in sections:
        if isinstance(item, tuple) and len(item) == 3 and item[0] == "_sec_":
            links.extend(iter_menu_file_links(item[2]))
        elif isinstance(item, tuple) and len(item) == 2:
            links.append(item)
    return links


def href_from_day_index(full_href: str, day_key: str) -> str:
    prefix = f"{day_key}/"
    if full_href.startswith(prefix):
        return full_href[len(prefix) :]
    return full_href


DAY_OVERVIEW_DESC: dict[str, str] = {
    "den-1": "Основы HTML: страницы Python (части 1–3), теги и списки.",
    "den-2": "CSS: блочный мини-сайт zad1.3, flex, таблицы стилей, отдельные страницы в папках zad1–zad3.",
    "den-3": "Таблицы HTML и индивидуальное задание (moto, ship).",
    "den-4": "Ссылки и изображения в страницах Python.",
    "den-5": "Подключение CSS: style, link, @import, media, презентация.",
    "den-6": "Формы в таблице и анкета регистрации.",
}


def render_day_overview_body(day_key: str) -> str:
    day_href = f"{day_key}/index.html"
    label = DAY_LABELS[day_key]
    links: list[tuple[str, str]] = []
    for entry in get_menu_structure():
        if len(entry) != 3 or entry[1] != day_href:
            continue
        links = iter_menu_file_links(entry[2])
        break
    lis = "\n".join(
        f'<li><a href="{href_from_day_index(href, day_key)}">{lbl}</a></li>'
        for lbl, href in links
    )
    desc = DAY_OVERVIEW_DESC.get(day_key, "Материалы практики за этот день.")
    return f"""<div class="day-overview">
<h2>{label}</h2>
<p class="day-desc">{desc}</p>
<h3>Файлы</h3>
<ul class="day-files">{lis}</ul>
<p class="day-hint">Откройте файл из списка выше или перейдите в меню слева: раскройте «{label}» и выберите нужную работу.</p>
</div>"""


def rel_prefix(web_path: str) -> str:
    parts = Path(web_path).parts
    if len(parts) <= 1:
        return ""
    return "../" * (len(parts) - 1)


LAB_LAYOUT_IDS = {
    "header": "l-hdr",
    "sidebar": "l-side",
    "content": "l-main",
    "footer": "l-ftr",
}


def lab_content_region_empty(body: str) -> bool:
    m = re.search(r'(?is)<div\s+id=["\']content["\'][^>]*>(.*?)</div>', body)
    if not m:
        return True
    text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return len(text) == 0


def rename_lab_layout_ids(html: str) -> str:
    for old, new in LAB_LAYOUT_IDS.items():
        html = re.sub(
            rf'id=(["\']){re.escape(old)}\1',
            rf"id=\1{new}\1",
            html,
            flags=re.I,
        )
    return html


def scope_block_layout_css(css_inner: str) -> str:
    """Стили блочной лабы целиком — как в оригинале, только id не конфликтуют с сайтом."""
    css_inner = re.sub(r"(?im)([^\w-]|^)body\s*\{", r"\1.lab-content.lab-layout {", css_inner)
    css_inner = re.sub(r"#container\b", ".lab-content.lab-layout", css_inner)
    for old, new in (
        ("#header", "#l-hdr"),
        ("#sidebar", "#l-side"),
        ("#content", "#l-main"),
        ("#footer", "#l-ftr"),
    ):
        css_inner = re.sub(rf"{re.escape(old)}\b", new, css_inner)
    return css_inner


def filter_lab_declarations(declarations: str) -> str:
    kept: list[str] = []
    for part in declarations.split(";"):
        part = part.strip()
        if not part:
            continue
        prop = part.split(":", 1)[0].strip().lower()
        if prop in LAB_OFFSET_PROPS:
            continue
        kept.append(part)
    return "; ".join(kept)


def scope_content_region_css(css_inner: str) -> str:
    """Стили только для области #content оригинала → .lab-content."""
    rules: list[str] = []
    shell_only = ("#container", "#sidebar", "#header", "#footer")
    for rule in re.finditer(r"(?is)([^{]+)\{([^}]*)\}", css_inner):
        selector = rule.group(1).strip()
        decl = filter_lab_declarations(rule.group(2).strip())
        if not selector or selector == "body":
            if selector == "body" and decl:
                rules.append(f".lab-content {{{decl}}}")
            continue
        if not decl:
            continue
        if any(s in selector for s in shell_only) and not re.search(r"#content\b", selector):
            continue
        selector = re.sub(r"\bbody\b", ".lab-content", selector)
        selector = re.sub(r"^#content\b", ".lab-content", selector)
        selector = re.sub(r"#content\b", ".lab-content", selector)
        rules.append(f"{selector} {{{decl}}}")
    return "\n".join(rules)


def extract_full_layout_html(body: str) -> str:
    parts: list[str] = []
    for tag in LAB_LAYOUT_IDS:
        m = re.search(
            rf'(?is)<div\s+id=["\']{tag}["\'][^>]*>.*?</div>',
            body,
        )
        if m:
            parts.append(m.group(0))
    return rename_lab_layout_ids("\n".join(parts))


def scope_standalone_css(css_inner: str) -> str:
    css_inner = re.sub(r"(?im)([^\w-]|^)body\s*\{", r"\1.lab-content {", css_inner)
    return re.sub(r"#content\b", ".lab-content", css_inner)


def scope_external_css(css_text: str) -> str:
    """Внешний CSS лабы — только внутри .lab-content (не трогать html/body сайта)."""
    rules: list[str] = []
    for rule in re.finditer(r"(?is)([^{]+)\{([^}]*)\}", css_text):
        selector = rule.group(1).strip()
        decl = rule.group(2).strip()
        if not selector:
            continue
        if selector.startswith("@"):
            rules.append(f"{selector} {{{decl}}}")
            continue
        low = selector.lower()
        if low == "html" or low == "body":
            rules.append(f".lab-content {{{decl}}}")
            continue
        scoped: list[str] = []
        for part in selector.split(","):
            part = part.strip()
            if not part:
                continue
            if part.startswith(".lab-content"):
                scoped.append(part)
            else:
                scoped.append(f".lab-content {part}")
        rules.append(f"{', '.join(scoped)} {{{decl}}}")
    return "\n".join(rules)


def is_semantic_lab_html(html: str) -> bool:
    return bool(re.search(r"<(header|main|footer|nav)\b", html, re.I))


def inline_linked_stylesheets(html: str, src_path: Path) -> str:
    chunks: list[str] = []
    for m in re.finditer(
        r'(?is)<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\'][^>]*>',
        html,
    ):
        href = m.group(1).strip()
        if href.startswith(("http://", "https://", "//")):
            chunks.append(m.group(0))
            continue
        css_file = (src_path.parent / href).resolve()
        if css_file.is_file():
            css_text = css_file.read_text(encoding="utf-8", errors="replace")
            chunks.append("<style>\n" + scope_external_css(css_text) + "\n</style>")
        else:
            chunks.append(m.group(0))
    return "\n".join(chunks)


LAB_GRID_IDS = {
    "header": "lab-header",
    "nav": "lab-nav",
    "content": "lab-inner",
    "sidebar": "lab-sidebar",
    "footer": "lab-footer",
}


def is_grid_lab_html(html: str) -> bool:
    return bool(re.search(r'id=["\']nav["\']', html)) and not re.search(
        r'id=["\']container["\']', html
    )


def is_block_layout_lab(html: str) -> bool:
    return bool(re.search(r'id=["\']container["\']', html)) and not is_grid_lab_html(html)


def rename_lab_grid_ids(html: str) -> str:
    for old, new in LAB_GRID_IDS.items():
        html = re.sub(
            rf'id=(["\']){re.escape(old)}\1',
            rf"id=\1{new}\1",
            html,
            flags=re.I,
        )
    return html


def scope_grid_lab_css(css_inner: str) -> str:
    css_inner = re.sub(r"(?im)([^\w-]|^)body\s*\{", r"\1.lab-content.lab-grid {", css_inner)
    css_inner = re.sub(r"(?im)^(\s*)div\s*\{", r"\1.lab-content.lab-grid div {", css_inner)
    for old, new in (
        ("#header", "#lab-header"),
        ("#nav", "#lab-nav"),
        ("#content", "#lab-inner"),
        ("#sidebar", "#lab-sidebar"),
        ("#footer", "#lab-footer"),
    ):
        css_inner = re.sub(rf"{re.escape(old)}\b", new, css_inner)
    return css_inner


def extra_head(
    html: str,
    src_path: Path,
    *,
    layout_mode: bool = False,
    content_region: bool = False,
) -> str:
    """Стили из оригинала — без «улучшений», только вписать в .lab-content."""
    chunks: list[str] = []

    if is_grid_lab_html(html):
        for m in re.finditer(r"(?is)<style[^>]*>(.*?)</style>", html):
            chunks.append("<style>\n" + scope_grid_lab_css(m.group(1)) + "\n</style>")
        chunks.append(inline_linked_stylesheets(html, src_path))
        return "\n".join(chunks)

    for m in re.finditer(r"(?is)<style[^>]*>(.*?)</style>", html):
        inner = m.group(1)
        block = m.group(0)
        if layout_mode:
            chunks.append("<style>\n" + scope_block_layout_css(inner) + "\n</style>")
        elif content_region or "#container" in block or "#sidebar" in block:
            scoped = scope_content_region_css(inner)
            if scoped.strip():
                chunks.append("<style>\n" + scoped + "\n</style>")
        else:
            chunks.append("<style>\n" + scope_standalone_css(inner) + "\n</style>")

    chunks.append(inline_linked_stylesheets(html, src_path))
    return "\n".join(chunks)


def strip_prepended_nav(body: str) -> str:
    return re.sub(
        r'(?is)^\s*<table border="1" cellpadding="10"[^>]*>.*?</table>\s*<br>\s*',
        "",
        body,
    )


def clean_extracted_inner(inner: str) -> str:
    inner = re.sub(r'(?is)^\s*<div\s+id=["\']content["\'][^>]*>\s*', "", inner)
    return inner.strip()


def strip_zad_shell(body: str) -> str:
    """Убрать оболочку zad1.3, если попала в body целиком."""
    body = re.sub(r'(?is)<div\s+id=["\']container["\'][^>]*>\s*', "", body, count=1)
    body = re.sub(r'(?is)<div\s+id=["\']header["\'][^>]*>.*?</div>\s*', "", body, count=1)
    body = re.sub(r'(?is)<div\s+id=["\']sidebar["\'][^>]*>.*?</div>\s*', "", body, count=1)
    body = re.sub(r'(?is)<div\s+id=["\']footer["\'][^>]*>.*?</div>\s*', "", body)
    body = re.sub(r"(?is)</div>\s*</div>\s*$", "", body)
    return body.strip()


def extract_inner_from_body(body: str) -> str | None:
    m = re.search(r'(?is)<div\s+id=["\']content["\'][^>]*>', body)
    if not m:
        return None
    start = m.end()
    fm = re.search(r'(?is)<div\s+id=["\']footer["\']', body[start:])
    chunk = body[start : start + fm.start()] if fm else body[start:]
    return clean_extracted_inner(chunk)


def wrap_lab_content(
    inner: str,
    *,
    grid: bool = False,
    layout: bool = False,
    semantic: bool = False,
    center: bool = False,
) -> str:
    inner = clean_extracted_inner(inner)
    if not inner:
        return inner
    if re.search(r'class=["\']lab-content["\']', inner):
        return inner
    if grid:
        cls = "lab-content lab-grid"
    elif layout:
        cls = "lab-content lab-layout"
    else:
        cls = "lab-content lab-page"
    if semantic:
        cls += " lab-semantic"
    if center:
        cls += " lab-page--center"
    return '<div class="' + cls + '">\n' + inner + '\n</div>'


def extract_simple_body(html: str) -> str:
    m = re.search(r"(?is)<body[^>]*>(.*)</body>", html)
    if not m:
        return ""
    return clean_extracted_inner(m.group(1).strip())


def has_grid_lab_iframe(body: str) -> bool:
    return bool(RE_WORK_FRAME_IFRAME.search(body))


def remove_work_frame_iframe(body: str) -> str:
    return RE_WORK_FRAME_IFRAME.sub("", body)


def collect_demo_indices(body: str) -> list[int]:
    nums: list[int] = []
    for m in RE_INDEX_DEMO_LINK.finditer(body):
        n = int(m.group(1))
        if n not in nums:
            nums.append(n)
    return nums


def build_demo_panels(demo_dir: Path, indices: list[int]) -> list[str]:
    panels: list[str] = []
    for num in indices:
        idx_path = demo_dir / f"index{num}.html"
        if not idx_path.is_file():
            continue
        demo_html = extract_simple_body(read_text(idx_path))
        if demo_html:
            panels.append(
                f'<div id="lab-demo-{num}" class="lab-demo">\n{demo_html}\n</div>'
            )
    return panels


def inline_grid_lab_demos(body: str, shell_src: Path) -> str:
    """Вместо iframe — панели с демо; переключение якорями (#lab-demo-N) и CSS :target."""
    panels = build_demo_panels(shell_src.parent, collect_demo_indices(body))
    if not panels:
        return remove_work_frame_iframe(body)

    panels_block = '<div class="lab-panels">\n' + "\n".join(panels) + "\n</div>"
    body, _ = RE_WORK_FRAME_IFRAME.subn(panels_block, body, count=1)
    body = RE_INDEX_DEMO_LINK.sub(r'href="#lab-demo-\1"', body)
    return RE_TARGET_WORK_FRAME.sub("", body)


def extract_grid_lab_body(body: str, src_path: Path | None = None) -> str:
    body = re.sub(r'(?is)<p\s+class=["\']site-topbar["\'][^>]*>.*?</p>\s*', "", body)
    body = body.strip()
    if (
        src_path
        and src_path.name == GRID_SHELL_FILENAME
        and has_grid_lab_iframe(body)
    ):
        body = inline_grid_lab_demos(body, src_path)
    elif has_grid_lab_iframe(body):
        body = remove_work_frame_iframe(body)
    return rename_lab_grid_ids(body)


def extract_content(html: str, src_path: Path, web_rel: str = "") -> tuple[str, str]:
    grid = is_grid_lab_html(html)
    semantic = is_semantic_lab_html(html)
    m = re.search(r"(?is)<body[^>]*>(.*)</body>", html)
    if not m:
        return (
            wrap_lab_content(html, grid=grid, semantic=semantic),
            extra_head(html, src_path),
        )
    body = strip_prepended_nav(m.group(1).strip())
    layout_mode = is_block_layout_lab(html) and lab_content_region_empty(body)
    if grid:
        extra = extra_head(html, src_path)
        inner = extract_grid_lab_body(body, src_path)
        return wrap_lab_content(inner, grid=True), extra
    inner = extract_inner_from_body(body)
    content_region = inner is not None and not layout_mode
    extra = extra_head(
        html, src_path, layout_mode=layout_mode, content_region=content_region
    )
    if layout_mode:
        inner = extract_full_layout_html(body)
        return wrap_lab_content(inner, layout=True), extra
    wp = web_rel.replace("\\", "/")
    center = content_region or wp.endswith("zad1/zad1.3.html")
    if inner is not None:
        return wrap_lab_content(inner, semantic=semantic, center=center), extra
    inner = strip_zad_shell(body) if re.search(r'id=["\']container["\']', body) else body
    return wrap_lab_content(inner, semantic=semantic, center=center), extra


def fix_content_paths(content: str, web_path: str) -> str:
    """Пути из оригиналов → структура WEB (без изменения текста)."""
    content = content.replace("../Индивидуальное/table/", "../tablitsa/")
    content = content.replace("../индивидуальное/table/", "../tablitsa/")
    # В лабе: @import "файл.css", а не @import url("...")
    content = re.sub(
        r'@import\s+url\(\s*(["\'])([^"\']+)\1\s*\)',
        r'@import "\2"',
        content,
        flags=re.I,
    )
    wp = web_path.replace("\\", "/")
    if "prezentaciya/12/" in wp:
        content = content.replace('href="styles1.css"', 'href="style1.css"')
        content = content.replace('href="styles2.css"', 'href="style2.css"')
    elif "prezentaciya/13/" in wp:
        content = content.replace('href="styles1.css"', 'href="style.css"')
    return content


def render_sidebar(active: str, prefix: str, menu: list) -> str:
    lines = ["<h3>Меню</h3>"]
    active = active.replace("\\", "/")

    for entry in menu:
        if entry[2] is None:
            label, href, _ = entry
            cls = ' class="active"' if href == active else ""
            lines.append(f'<p class="nav-top"><a href="{prefix}{href}"{cls}>{label}</a></p>')
            continue

        if entry[2] == "top-extra":
            continue

        day_label, day_href, sections = entry
        open_day = " open" if menu_day_open(day_href, sections, active) else ""
        lines.append(f'<details class="nav-day"{open_day}>')
        lines.append(f"<summary>{day_label}</summary>")
        lines.append('<div class="nav-day-body">')
        ocls = ' class="active"' if day_href == active else ""
        lines.append(f'<p class="nav-overview"><a href="{prefix}{day_href}"{ocls}>Обзор дня</a></p>')

        flat: list[tuple[str, str]] = []

        def flush_flat() -> None:
            if not flat:
                return
            lines.append('<ul class="nav-flat">')
            for lbl, href in flat:
                cls = ' class="active"' if href == active else ""
                lines.append(f'<li><a href="{prefix}{href}"{cls}>{lbl}</a></li>')
            lines.append("</ul>")
            flat.clear()

        for item in sections:
            if isinstance(item, tuple) and len(item) == 3 and item[0] == "_sec_":
                flush_flat()
                _, sec_name, links = item
                open_sec = " open" if menu_section_open(links, active) else ""
                lines.append(f'<details class="nav-section"{open_sec}>')
                lines.append(f"<summary>{sec_name}</summary><ul>")
                for lbl, href in links:
                    cls = ' class="active"' if href == active else ""
                    lines.append(f'<li><a href="{prefix}{href}"{cls}>{lbl}</a></li>')
                lines.append("</ul></details>")
            else:
                flat.append(item)

        flush_flat()
        lines.append("</div></details>")
    return "\n".join(lines)


def render_page_clean(
    title: str,
    content: str,
    web_path: str,
    nav: list | None = None,
    active: str | None = None,
    extra_styles: str = "",
) -> str:
    active = active or web_path.replace("\\", "/")
    if nav is None:
        nav = get_menu_structure()
    prefix = rel_prefix(web_path)
    extra_block = f"    {extra_styles}\n" if extra_styles else ""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — WEB-практика</title>
    <link rel="stylesheet" href="{prefix}css/main.css">
{extra_block}</head>
<body>
    <div id="container">
        <div id="header">
            <h1>WEB-ПРАКТИКА</h1>
        </div>
        <div id="main-row">
            <div id="sidebar">
{render_sidebar(active, prefix, nav)}
            </div>
            <div id="content">
{content}
            </div>
        </div>
        <div id="footer">
            <div class="footer-inner">
                <p class="footer-brand">WEB-ПРАКТИКА</p>
                <p class="footer-group">Группа <span class="footer-group-code">{GROUP_IB}</span></p>
                <p class="footer-copy"><span class="copy-sign">&copy;</span> Слепцов Павел Леонидович</p>
            </div>
        </div>
    </div>
</body>
</html>
"""


def verify_site() -> list[str]:
    """Проверка: файлы меню и ресурсы в собранных страницах."""
    problems: list[str] = []
    for href in all_hrefs_in_menu(get_menu_structure()):
        clean = href.split("#")[0]
        if clean == "index.html":
            continue
        if not (ROOT / clean).is_file():
            problems.append(f"меню: нет файла {clean}")

    skip_prefixes = ("http://", "https://", "#", "mailto:", "data:", "javascript:")

    def check_ref(html_file: Path, ref: str) -> None:
        if ref.startswith(skip_prefixes) or "://" in ref:
            return
        if ref.startswith("css/main.css"):
            return
        target = (html_file.parent / ref).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            return
        if Path(ref).suffix and not target.is_file():
            problems.append(f"{html_file.relative_to(ROOT)}: нет {ref}")

    for html_file in sorted(ROOT.rglob("*.html")):
        if "css" in html_file.parts and html_file.suffix == ".css":
            continue
        text = read_text(html_file)
        for m in re.finditer(r'(?i)(?:src|href)=["\']([^"\']+)["\']', text):
            check_ref(html_file, m.group(1).strip())
        for m in re.finditer(
            r'@import\s+(?:url\(\s*)?["\']?([^"\')\s;]+)["\']?',
            text,
            re.I,
        ):
            check_ref(html_file, m.group(1).strip())

    for css_file in sorted((ROOT / "den-5" / "primery").glob("*.css")):
        text = read_text(css_file)
        for m in re.finditer(r'@import\s+url\(', text, re.I):
            problems.append(f"{css_file.relative_to(ROOT)}: используется @import url(), нужен @import \"файл\"")
    return problems


def remove_stale_embed_pages() -> None:
    for embed in ROOT.rglob("*.embed.html"):
        embed.unlink()


def build_all_pages() -> None:
    for src_path, web_rel in HTML_SOURCES:
        raw = read_text(src_path)
        out = ROOT / web_rel
        out.parent.mkdir(parents=True, exist_ok=True)

        content, extra = extract_content(raw, src_path, web_rel)
        content = fix_content_paths(content, web_rel)
        extra = fix_content_paths(extra, web_rel)
        title_m = re.search(r"<title>([^<]*)</title>", raw, re.I)
        title = title_m.group(1).strip() if title_m else out.stem
        extra_block = f"    {extra}\n" if extra else ""
        out.write_text(
            render_page_clean(title, content, web_rel, active=web_rel, extra_styles=extra_block),
            encoding="utf-8",
        )


def write_index_and_day_pages() -> None:
    index_body = """<div class="welcome">
    <h2>Добро пожаловать!</h2>
    <p class="welcome-lead">Сайт с материалами проделанной WEB-практики.</p>
    <table class="welcome-table welcome-table--days" border="1" cellpadding="8" cellspacing="0">
        <tr><th>Дни</th></tr>
        <tr><td><a href="den-1/index.html">День 1</a></td></tr>
        <tr><td><a href="den-2/index.html">День 2</a></td></tr>
        <tr><td><a href="den-3/index.html">День 3</a></td></tr>
        <tr><td><a href="den-4/index.html">День 4</a></td></tr>
        <tr><td><a href="den-5/index.html">День 5</a></td></tr>
        <tr><td><a href="den-6/index.html">День 6</a></td></tr>
    </table>
    <section class="about-dev">
        <h2>О разработчике</h2>
        <p class="dev-name">Слепцов Павел Леонидович</p>
        <p class="dev-group">Единая группа <span>{GROUP_IB}</span></p>
    </section>
</div>"""
    (ROOT / "index.html").write_text(
        render_page_clean("Главная", index_body, "index.html", active="index.html"),
        encoding="utf-8",
    )
    for day in DAY_LABELS:
        p = f"{day}/index.html"
        body = render_day_overview_body(day)
        (ROOT / p).write_text(
            render_page_clean(f"Обзор — {DAY_LABELS[day]}", body, p, active=p),
            encoding="utf-8",
        )


def main() -> None:
    scan_sources()
    copy_assets()
    build_all_pages()
    remove_stale_embed_pages()
    write_index_and_day_pages()

    img_dir = ROOT / "img"
    if img_dir.exists():
        shutil.rmtree(img_dir)

    problems = verify_site()
    print(f"Собрано страниц: {len(HTML_SOURCES) + 7}, каталог: {ROOT}")
    if problems:
        print("Проверка — найдены проблемы:")
        for msg in problems:
            print(f"  - {msg}")
    else:
        print("Проверка: все ссылки меню и файлы на месте.")


if __name__ == "__main__":
    main()
