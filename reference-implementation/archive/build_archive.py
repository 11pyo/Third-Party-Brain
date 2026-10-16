#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_archive.py — Compile articles/*/*.md into archive.html and archive-structure.md

Reads markdown SSOT articles, validates schemas and tags, and compiles:
  - archive.html (Read-only mirror)
  - archive-structure.md (Read-only mirror)
"""
import io
import os
import re
import sys
import yaml

# UTF-8 stdout configuration
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(ROOT, "articles")
TEMPLATES_DIR = os.path.join(ROOT, "templates")
HTML_OUT = os.path.join(ROOT, "archive.html")
STRUCT_OUT = os.path.join(ROOT, "archive-structure.md")

CATS = ["기초용어", "프로세스", "기술설정", "트러블슈팅", "운영참조매뉴얼"]
CAT_DIRS = {
    "기초용어": "01_terms",
    "프로세스": "02_process",
    "기술설정": "03_tech",
    "트러블슈팅": "04_troubleshoot",
    "운영참조매뉴얼": "05_manual",
    "운영 참조 매뉴얼": "05_manual",
}
CAT_ICONS = {
    "기초용어": "📘 기초용어",
    "프로세스": "🔄 프로세스",
    "기술설정": "⚙️ 기술설정",
    "트러블슈팅": "🔧 트러블슈팅",
    "운영참조매뉴얼": "📋 운영참조매뉴얼",
    "운영 참조 매뉴얼": "📋 운영 참조 매뉴얼",
}

TAGS_TO_CHECK = ['strong', 'b', 'em', 'a', 'code', 'span', 'small', 'div']


def parse_markdown_article(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().lstrip("\ufeff").replace("\r\n", "\n")

    # Split frontmatter and body
    m = re.match(r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$', text)
    if not m:
        raise ValueError(f"Invalid frontmatter format in {file_path}")

    fm_raw = m.group(1)
    body = m.group(2)

    try:
        fm = yaml.safe_load(fm_raw) or {}
    except Exception as e:
        raise ValueError(f"YAML parse error in {file_path}: {e}")

    return fm, body


def validate_article(fm, body, file_path, seen_ids):
    aid = fm.get("id")
    if not aid:
        print(f"❌ Error in {file_path}: Missing 'id' in frontmatter")
        return False

    if aid in seen_ids:
        print(f"❌ Error: Duplicate article id '{aid}' in {file_path} (already in {seen_ids[aid]})")
        return False
    seen_ids[aid] = file_path

    # Check for nested <article>
    if "<article" in body.lower():
        print(f"❌ Error in {file_path}: Nested <article> found in body")
        return False

    # Check balanced tags
    for tag in TAGS_TO_CHECK:
        open_count = len(re.findall(rf'<{tag}(\s+[^>]*)?>', body, re.IGNORECASE))
        close_count = len(re.findall(rf'</{tag}\s*>', body, re.IGNORECASE))
        if open_count != close_count:
            print(f"❌ Error in {file_path}: Unbalanced <{tag}> tag (open={open_count}, close={close_count})")
            return False

    return True


def main():
    print("=" * 60)
    print("Building archive mirrors from markdown SSOT...")
    print("=" * 60)

    # 1. Load templates
    shell_path = os.path.join(TEMPLATES_DIR, "archive_shell.html")
    update_path = os.path.join(TEMPLATES_DIR, "latest_update.txt")
    footer_path = os.path.join(TEMPLATES_DIR, "structure_footer.md")

    if not os.path.exists(shell_path) or not os.path.exists(update_path) or not os.path.exists(footer_path):
        print(f"❌ Error: Templates missing in {TEMPLATES_DIR}. Run decompile_archive.py first.")
        sys.exit(1)

    with open(shell_path, "r", encoding="utf-8") as f:
        shell_html = f.read()
    with open(update_path, "r", encoding="utf-8") as f:
        latest_update = f.read().strip()
    with open(footer_path, "r", encoding="utf-8") as f:
        structure_footer = f.read()

    # 2. Collect and validate articles
    seen_ids = {}
    articles_by_cat = {c: [] for c in CATS}

    if not os.path.exists(ARTICLES_DIR):
        print(f"❌ Error: {ARTICLES_DIR} does not exist.")
        sys.exit(1)

    for cat_name in CATS:
        cat_dir_name = CAT_DIRS[cat_name]
        cat_path = os.path.join(ARTICLES_DIR, cat_dir_name)
        if not os.path.exists(cat_path):
            continue

        for fname in os.listdir(cat_path):
            if fname.endswith(".md"):
                fpath = os.path.join(cat_path, fname)
                try:
                    fm, body = parse_markdown_article(fpath)
                except Exception as e:
                    print(f"❌ Error: {e}")
                    sys.exit(1)

                if not validate_article(fm, body, fpath, seen_ids):
                    sys.exit(1)

                # Ensure category is set
                fm_cat = fm.get("category", cat_name)
                articles_by_cat[fm_cat].append((fm, body, fpath))

    # 3. Sort articles within each category
    total_articles = sum(len(articles_by_cat[c]) for c in CATS)
    print(f"Loaded and validated {total_articles} articles across {len(CATS)} categories.")

    for c in CATS:
        # Sort by (order, id)
        articles_by_cat[c].sort(key=lambda item: (item[0].get("order", 9999), item[0].get("id", "")))

    # 4. Generate Sidebar Navigation HTML
    sidebar_lines = []
    sidebar_links_count = 0
    for c in CATS:
        sidebar_lines.append(f'  <div class="nav-cat-title">{CAT_ICONS[c]}</div>')
        for fm, _, _ in articles_by_cat[c]:
            # Rule: Render in sidebar only if collapsed is false
            if not fm.get("collapsed", False):
                aid = fm["id"]
                nav_title = fm.get("nav_title") or fm.get("title", "")
                nav_desc = fm.get("nav_desc", "")
                if nav_desc:
                    sidebar_lines.append(f'  <a class="nav-link" href="#{aid}">{nav_title}<span class="nd">{nav_desc}</span></a>')
                else:
                    sidebar_lines.append(f'  <a class="nav-link" href="#{aid}">{nav_title}</a>')
                sidebar_links_count += 1

    sidebar_nav_html = "\n" + "\n".join(sidebar_lines) + "\n"

    # 5. Generate Articles Content HTML
    content_blocks = []
    for c in CATS:
        cnt = len(articles_by_cat[c])
        content_blocks.append(f'<!-- ═══════════════════════════════════ {c} ═══ -->')
        content_blocks.append(f'<div class="cat-header"><h2>{CAT_ICONS[c]}</h2><span class="cnt">{cnt}</span></div>')
        content_blocks.append('')

        for fm, body, _ in articles_by_cat[c]:
            aid = fm["id"]
            title = fm.get("title", "")
            badge_class = fm.get("badge_class", "b-기초")
            badge_text = fm.get("badge_text", c)
            date = fm.get("date", "")
            collapsed = fm.get("collapsed", False)
            old = fm.get("old", False)

            # Class string
            cls_parts = ["article"]
            if collapsed:
                cls_parts.append("collapsed")
            if old:
                cls_parts.append("old")
            cls_str = " ".join(cls_parts)

            # Data attributes
            data_attrs = []
            if fm.get("data_cat"):
                data_attrs.append(f'data-cat="{fm["data_cat"]}"')
            if fm.get("data_related"):
                data_attrs.append(f'data-related="{fm["data_related"]}"')
            if fm.get("data_tags"):
                data_attrs.append(f'data-tags="{fm["data_tags"]}"')

            data_attrs_str = (" " + " ".join(data_attrs)) if data_attrs else ""

            # Tag chips
            tag_chips = fm.get("tag_chips") or []
            chips_html = "".join(f'<span class="tag">{chip}</span>' for chip in tag_chips)

            # Assemble article
            art_lines = [
                f'<article class="{cls_str}" id="{aid}"{data_attrs_str}>',
                '  <div class="ah">',
                f'    <div class="at">{title}</div>',
                f'    <span class="badge {badge_class}">{badge_text}</span>',
                f'    <span class="db">{date}</span>',
                '  </div>',
                '  <div class="tags">',
                f'    {chips_html}',
                '  </div>',
                body.strip(),
                '</article>'
            ]
            content_blocks.append("\n".join(art_lines))
            content_blocks.append('')

    articles_content_html = "\n".join(content_blocks)

    # 6. Build archive.html
    final_html = shell_html.replace('<!-- {{SIDEBAR_NAV}} -->', sidebar_nav_html.strip('\n'))
    final_html = final_html.replace('<!-- {{ARTICLES_CONTENT}} -->', articles_content_html)

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"Generated {HTML_OUT} ({len(final_html)} bytes, {sidebar_links_count} sidebar links)")

    # 7. Build archive-structure.md
    struct_lines = [
        "# archive.html 구조 인덱스",
        "> **목적**: 매 세션마다 archive.html 전체를 읽지 않도록 구조를 미리 파악하기 위한 경량 인덱스.  ",
        "> **업데이트 규칙**: archive.html에 아티클 추가·삭제·이동 시 이 파일도 반드시 동기화할 것.  ",
        f"{latest_update}",
        "",
        "---",
        "",
        "## 파일 위치",
        "```",
        "archive.html",
        "```",
        "",
        "---",
        "",
        "## 전체 아티클 수",
        "| 카테고리 | 아티클 수 | HTML 변수 (cnt) |",
        "|----------|-----------|----------------|",
    ]

    for c in CATS:
        cnt = len(articles_by_cat[c])
        struct_lines.append(f'| {CAT_ICONS[c]} | {cnt} | `<span class="cnt">{cnt}</span>` |')
    struct_lines.append(f'| **합계** | **{total_articles}** | |')
    struct_lines.append('')
    struct_lines.append('> **🔗 메타·링크 레이어 (2026-06-24, Obsidian 패턴 융합)**: 일부 핵심 아티클에 `data-related`(관련글 id 공백구분)·`data-cat` 속성이 추가됨(본문 무손상·검색 영향 0·아티클 수 불변). 페이지 하단 인라인 JS가 이를 읽어 글 하단에 「🔗 관련 / ↩ 여기를 참조」 backlink 칩 + `#태그` 클릭검색을 자동 렌더(`data-noexport`=💾저장 제외, 정본=`data-related` 속성뿐). 통제 태그어휘·메타 규칙=`META_TAG_SCHEMA.md`. 현재 부여 15아티클(여신/세금/반품/취소 허브). 알고리즘 상세=블루프린트 `03-algorithms-scaling`.')
    struct_lines.append('')
    struct_lines.append('---')
    struct_lines.append('')

    # Category tables
    for c in CATS:
        cnt = len(articles_by_cat[c])
        struct_lines.append(f'## {CAT_ICONS[c]} ({cnt}개)')
        struct_lines.append('')
        struct_lines.append('| # | id | 제목 | 핵심 키워드 |')
        struct_lines.append('|---|----|----|------------|')

        for idx, (fm, _, _) in enumerate(articles_by_cat[c], start=1):
            aid = fm["id"]
            stitle = fm.get("struct_title") or fm.get("title", "")
            keywords = fm.get("struct_keywords")
            if not keywords:
                # Combine tag chips and data_tags
                tag_chips = fm.get("tag_chips") or []
                keywords = ", ".join(tag_chips) if tag_chips else fm.get("data_tags", "")
            # Escape pipes if any
            stitle = stitle.replace("|", "&#124;")
            keywords = keywords.replace("|", "&#124;")
            struct_lines.append(f'| {idx} | `{aid}` | {stitle} | {keywords} |')

        struct_lines.append('')
        struct_lines.append('---')
        struct_lines.append('')

    # Append footer
    struct_lines.append(structure_footer.strip())
    struct_lines.append('')

    final_struct = "\n".join(struct_lines)
    with open(STRUCT_OUT, "w", encoding="utf-8") as f:
        f.write(final_struct)
    print(f"Generated {STRUCT_OUT} ({len(final_struct)} bytes, {total_articles} rows)")

    print("\n✅ Build complete: archive.html and archive-structure.md successfully compiled.")


if __name__ == "__main__":
    main()
