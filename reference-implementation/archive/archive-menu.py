#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive-menu.py
Indexable Knowledge Archive — hierarchical terminal menu (TUI)

Run:      python archive-menu.py
Navigate: type a number → Enter  /  b = back  /  q = quit

A keyboard-only browser for the archive: search (keyword / category / T-Code /
person), intake check, status (list / stats / conflict scan), and quick lookups.
Useful on a server or over SSH where the HTML UI isn't handy.
"""

import re, sys, io, os
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding="utf-8", errors="replace")

# ── paths ─────────────────────────────────────────────────────────────
BASE    = Path(__file__).parent
ARCHIVE = BASE / "archive.html"

# ── synonym expansion (shared with intake) ───────────────────────────
#   Sample codes (ZSD*/ZTSD*) are fictional; SU01/VL09/FD32/VKM4 are standard SAP.
ALIASES = {
    "매출취소": ["취소요청", "빌링취소", "ZSD030", "ZSD034"],
    "출고취소": ["VL09", "납품취소", "ZTSD075"],
    "권한":     ["SU01", "역할", "ZSD110"],
    "결산":     ["월말", "마감", "D+1", "D+2", "ZSD143"],
    "여신":     ["Credit", "BLOCK", "FD32", "VKM4", "ZTSD071"],
}

CONFLICT_PAIRS = [
    (r"ZTSD070.{0,40}ZMM213", r"ZMM213.{0,40}ZTSD070"),
    (r"삭제.{0,20}후.{0,20}취소",  r"취소.{0,20}후.{0,20}삭제"),
    (r"먼저.{0,30}다음",            r"다음.{0,30}먼저"),
    (r"VL09.{0,40}ZTSD",            r"ZTSD.{0,40}VL09"),
]

CATEGORY_SIGNALS = {
    "기초용어":       ["유형", "코드", "정의", "T-Code", "테이블"],
    "프로세스":       ["흐름", "절차", "단계", "순서", "오더"],
    "기술설정":       ["설정", "아키텍처", "결산", "CTS", "환경"],
    "트러블슈팅":     ["오류", "Error", "Dump", "문제", "해결", "Block"],
    "운영참조매뉴얼": ["매뉴얼", "참조", "가이드", "임시"],
}

W = 64  # output width
DIVIDER   = "=" * W
SUBDIV    = "-" * W
breadcrumb = []  # track current path

# ── common utils ──────────────────────────────────────────────────────
def strip_tags(s):    return re.sub(r"<[^>]+>", "", s)
def norm(s):          return re.sub(r"\s+", " ", s).strip()
def clr():            os.system("cls" if os.name == "nt" else "clear")

def header(title):
    path = " > ".join(breadcrumb + [title]) if breadcrumb else title
    print(f"\n{DIVIDER}")
    print(f"  Knowledge Archive  |  {path}")
    print(DIVIDER)

def prompt(msg="select"):
    try:
        return input(f"\n  {msg} > ").strip()
    except (EOFError, KeyboardInterrupt):
        return "q"

def pause():
    try:
        input("\n  [Enter] continue...")
    except (EOFError, KeyboardInterrupt):
        pass

def nav_hint():
    print(f"\n  {'b'} = back   {'q'} = quit")

# ── archive parsing ───────────────────────────────────────────────────
_html_cache = None

def get_html():
    global _html_cache
    if _html_cache is None:
        _html_cache = ARCHIVE.read_text(encoding="utf-8")
    return _html_cache

def load_articles():
    html = get_html()
    arts = []
    for m in re.finditer(r'<article[^>]+id="([^"]+)"', html):
        seg = html[m.start(): m.start() + 600]
        title_m = re.search(r'class="at">([^<]+)', seg)
        badge_m = re.search(r'class="badge[^"]*">([^<]+)', seg)
        tags_m  = re.search(r'data-tags="([^"]*)"', html[m.start(): m.start() + 300])
        date_m  = re.search(r'class="db">([^<]+)', seg)
        arts.append({
            "id":    m.group(1),
            "title": norm(title_m.group(1)) if title_m else "?",
            "cat":   norm(badge_m.group(1)) if badge_m else "?",
            "tags":  tags_m.group(1) if tags_m else "",
            "date":  norm(date_m.group(1)) if date_m else "",
            "pos":   m.start(),
        })
    return arts

def article_at(arts, pos):
    best = arts[0] if arts else {"id":"?","title":"?","cat":"?"}
    for a in arts:
        if a["pos"] <= pos:
            best = a
        else:
            break
    return best

def search_html(keywords):
    html = get_html()
    arts = load_articles()
    results = defaultdict(list)
    for kw in keywords:
        for m in re.compile(re.escape(kw), re.I).finditer(html):
            a   = article_at(arts, m.start())
            s   = max(0, m.start() - 180)
            e   = min(len(html), m.end() + 180)
            ctx = norm(strip_tags(html[s:e]))
            results[a["id"]].append({"kw": kw, "ctx": ctx, "title": a["title"], "cat": a["cat"]})
    return results

def expand_kw(kws):
    ex = list(kws)
    for kw in kws:
        for base, aliases in ALIASES.items():
            if kw.upper() in [a.upper() for a in aliases] or kw == base:
                ex.extend(aliases)
    return list(dict.fromkeys(ex))

def suggest_cat(text):
    scores = {c: sum(1 for s in sigs if re.search(s, text, re.I))
              for c, sigs in CATEGORY_SIGNALS.items()}
    return sorted(scores.items(), key=lambda x: -x[1])

def detect_conflict(a, b):
    for pa, pb in CONFLICT_PAIRS:
        if (re.search(pa, a, re.I|re.S) and re.search(pb, b, re.I|re.S)) or \
           (re.search(pa, b, re.I|re.S) and re.search(pb, a, re.I|re.S)):
            return True
    return False

def excerpt(ctx, kw, w=50):
    idx = ctx.lower().find(kw.lower())
    if idx == -1: return ctx[:100]
    s = max(0, idx - w)
    e = min(len(ctx), idx + len(kw) + w)
    return ("..." if s else "") + ctx[s:e] + ("..." if e < len(ctx) else "")

# ═════════════════════════════════════════════════════════════════════
# ── 1. search ────────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════

def search_keyword():
    breadcrumb.append("search")
    while True:
        clr(); header("keyword search")
        print()
        kw_raw = prompt("keywords (space-separated, b=back)")
        if kw_raw in ("b", "q", ""): break
        kws = expand_kw(kw_raw.split())
        res = search_html(kws)
        clr(); header("results")
        if not res:
            print(f"\n  no results -- '{kw_raw}'")
        else:
            print(f"\n  {sum(len(v) for v in res.values())} hits  /  {len(res)} articles\n")
            for art_id, hits in res.items():
                title = hits[0]["title"]
                cat   = hits[0]["cat"]
                kws_hit = list(dict.fromkeys(h["kw"] for h in hits))
                print(f"  [{cat}]  #{art_id}")
                print(f"           {title}")
                print(f"           keywords: {kws_hit[:4]}")
                ex = excerpt(hits[0]["ctx"], hits[0]["kw"])
                print(f"           \"{ex}\"")
                print()
        nav_hint(); pause()
    breadcrumb.pop()

def search_by_category():
    breadcrumb.append("category")
    arts = load_articles()
    cats = {}
    for a in arts:
        cats.setdefault(a["cat"], []).append(a)
    cat_list = sorted(cats.keys())

    while True:
        clr(); header("browse by category")
        print()
        for i, c in enumerate(cat_list, 1):
            print(f"  [{i}] {c}  ({len(cats[c])})")
        nav_hint()
        sel = prompt("select category")
        if sel in ("b", "q", ""): break
        if not sel.isdigit() or not (1 <= int(sel) <= len(cat_list)):
            continue

        chosen = cat_list[int(sel) - 1]
        breadcrumb.append(chosen)
        art_list = cats[chosen]

        while True:
            clr(); header(chosen)
            print()
            for i, a in enumerate(art_list, 1):
                print(f"  [{i:2}]  #{a['id']}")
                print(f"         {a['title']}  ({a['date']})")
            nav_hint()
            sel2 = prompt("select article (number)")
            if sel2 in ("b", "q", ""): break
            if not sel2.isdigit() or not (1 <= int(sel2) <= len(art_list)):
                continue
            a = art_list[int(sel2) - 1]
            clr(); header(a["title"])
            print(f"\n  ID       : #{a['id']}")
            print(f"  category : {a['cat']}")
            print(f"  date     : {a['date']}")
            print(f"  tags     : {a['tags'][:120]}")
            nav_hint(); pause()

        breadcrumb.pop()
    breadcrumb.pop()

def search_tcode():
    breadcrumb.append("T-Code search")
    while True:
        clr(); header("T-Code search")
        print("  Enter a T-Code to find related articles and the screen name.")
        print()
        tc = prompt("T-Code (e.g. ZSD030, VF11, FD32, b=back)")
        if tc in ("b", "q", ""): break

        html = get_html()
        arts = load_articles()
        res  = defaultdict(list)
        pat  = re.compile(re.escape(tc), re.I)
        for m in pat.finditer(html):
            a = article_at(arts, m.start())
            s = max(0, m.start() - 200)
            e = min(len(html), m.end() + 200)
            ctx = norm(strip_tags(html[s:e]))
            res[a["id"]].append({"ctx": ctx, "title": a["title"], "cat": a["cat"]})

        # try to pull the screen name (em dash pattern right after the T-Code)
        screen_m = re.search(
            re.escape(tc) + r"[^<]{0,5}(?:—|--)([^<\n]{3,50})", html, re.I
        )
        screen_name = norm(strip_tags(screen_m.group(1))) if screen_m else "(screen name not found)"

        clr(); header(f"T-Code: {tc.upper()}")
        print(f"\n  screen name : {screen_name}")
        print(f"  hit articles : {len(res)}\n")
        if not res:
            print(f"  '{tc}' not in the archive")
        else:
            for art_id, hits in res.items():
                print(f"  [{hits[0]['cat']}]  #{art_id}  —  {hits[0]['title']}")
                ex = excerpt(hits[0]["ctx"], tc)
                print(f"           \"{ex}\"")
                print()
        nav_hint(); pause()
    breadcrumb.pop()

def search_person():
    breadcrumb.append("person search")
    while True:
        clr(); header("person search")
        print()
        name = prompt("name or task keyword (b=back)")
        if name in ("b", "q", ""): break
        res = search_html([name])
        clr(); header(f"person search: {name}")
        if not res:
            print(f"\n  '{name}' not found")
        else:
            for art_id, hits in res.items():
                print(f"  [{hits[0]['cat']}]  #{art_id}  —  {hits[0]['title']}")
                ex = excerpt(hits[0]["ctx"], name)
                print(f"           \"{ex}\"")
                print()
        nav_hint(); pause()
    breadcrumb.pop()

def menu_search():
    breadcrumb.append("search")
    items = [
        ("keyword search",      search_keyword),
        ("browse by category",  search_by_category),
        ("T-Code search",       search_tcode),
        ("person search",       search_person),
    ]
    while True:
        clr(); header("search")
        print()
        for i, (label, _) in enumerate(items, 1):
            print(f"  [{i}] {label}")
        nav_hint()
        sel = prompt()
        if sel in ("b", "q", ""): break
        if sel.isdigit() and 1 <= int(sel) <= len(items):
            items[int(sel)-1][1]()
    breadcrumb.pop()

# ═════════════════════════════════════════════════════════════════════
# ── 2. new intake ─────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════

def _run_intake(raw_kws, new_text=""):
    """Run the intake logic and print the result."""
    keywords = expand_kw(raw_kws)
    extras   = [k for k in keywords if k not in raw_kws]
    html     = get_html()
    arts     = load_articles()

    print(f"\n  input keywords  : {raw_kws}")
    if extras:
        print(f"  expanded        : +{extras}")

    hits = defaultdict(list)
    for kw in keywords:
        for m in re.compile(re.escape(kw), re.I).finditer(html):
            a = article_at(arts, m.start())
            s = max(0, m.start() - 250); e = min(len(html), m.end() + 250)
            ctx = norm(strip_tags(html[s:e]))
            hits[a["id"]].append({"kw": kw, "ctx": ctx, "title": a["title"], "cat": a["cat"]})

    if not hits:
        print(f"\n  [OK]  no duplicate -- new content not in the archive")
        cats = suggest_cat(new_text or " ".join(raw_kws))
        print(f"  [CAT] suggested category : {cats[0][0]}")
        print(f"\n  [>>]  recommended action:")
        print(f"        -> write a new article  (category: {cats[0][0]})")
        print(f"        -> add a sidebar nav link")
        print(f"        -> bump the category count +1")
        print(f"        -> sync archive-structure.md")
        return

    total = sum(len(v) for v in hits.values())
    print(f"\n  [HIT] {total} hits  /  {len(hits)} articles\n")
    art_ctx = {}
    for art_id, items in hits.items():
        kws_u = list(dict.fromkeys(i["kw"] for i in items))
        print(f"  [ART] #{art_id}  [{items[0]['cat']}]  {items[0]['title']}")
        print(f"        keywords : {kws_u[:5]}")
        ex = excerpt(items[0]["ctx"], items[0]["kw"])
        print(f"        excerpt  : \"{ex}\"")
        print()
        art_ctx[art_id] = " ".join(i["ctx"] for i in items)

    # conflict detection
    art_ids   = list(hits.keys())
    conflicts = []
    for i in range(len(art_ids)):
        for j in range(i+1, len(art_ids)):
            if detect_conflict(art_ctx[art_ids[i]], art_ctx[art_ids[j]]):
                conflicts.append((art_ids[i], art_ids[j]))
    if new_text:
        for aid, ctx in art_ctx.items():
            if detect_conflict(new_text, ctx):
                conflicts.append(("NEW", aid))

    if conflicts:
        print(f"  [!!]  conflicts detected ({len(conflicts)}):")
        for a, b in conflicts:
            la = "new" if a == "NEW" else f"#{a}"
            print(f"        {la}  <->  #{b}  -- compare procedure order")
        print()

    # duplicate ratio
    if new_text:
        nw = set(re.findall(r"\w{2,}", new_text))
        for aid, ctx in art_ctx.items():
            ow  = set(re.findall(r"\w{2,}", ctx))
            ov  = len(nw & ow) / max(len(nw), 1)
            if ov > 0.70:
                print(f"  [DUP] {ov:.0%} similar to #{aid} -- update existing instead")

    # recommended action
    print(f"  [>>]  recommended action:")
    if conflicts:
        for a, b in conflicts:
            la = "new" if a == "NEW" else f"#{a}"
            print(f"        {la} vs #{b} -- verify in practice, merge into one")
    elif len(hits) == 1:
        aid   = art_ids[0]
        title = hits[aid][0]["title"]
        print(f"        -> #{aid} ({title})")
        print(f"           update the existing article")
    elif len(hits) == 2:
        print(f"        -> update whichever of {art_ids} is more relevant")
        print(f"           or cross-link the two articles")
    else:
        cats = suggest_cat(new_text or " ".join(raw_kws))
        print(f"        -> many related articles -- a new article is recommended")
        print(f"           suggested category: {cats[0][0]}")

def intake_keyword():
    breadcrumb.append("keyword intake")
    while True:
        clr(); header("intake by keyword")
        print("  Enter the key terms of the content you want to add.")
        print()
        kw = prompt("keywords (space-separated, b=back)")
        if kw in ("b", "q", ""): break
        clr(); header("intake analysis")
        _run_intake(kw.split())
        nav_hint(); pause()
    breadcrumb.pop()

def intake_text():
    breadcrumb.append("text intake")
    while True:
        clr(); header("intake by full text")
        print("  Paste the content, then press Enter twice on a blank line.")
        print()
        lines, blank = [], 0
        try:
            while blank < 2:
                line = input()
                if line == "":
                    blank += 1
                else:
                    blank = 0
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass

        text = "\n".join(lines).strip()
        if not text or text in ("b", "q"):
            break

        # auto keyword extraction from the text
        tcode_m   = re.findall(r"[ZV][A-Z0-9]{3,10}", text)
        table_m   = re.findall(r"[ZV]T[A-Z0-9]{4,8}", text)
        kw_auto   = list(dict.fromkeys(tcode_m + table_m)) or text.split()[:4]

        clr(); header("text intake analysis")
        print(f"\n  auto-extracted keywords: {kw_auto}")
        _run_intake(kw_auto, text)
        nav_hint(); pause()
        break
    breadcrumb.pop()

def intake_memo():
    """Parse a memo/notice — auto-extract recipient, request, T-Codes, dates."""
    breadcrumb.append("memo parse")
    while True:
        clr(); header("memo / work-note parse")
        print("  Paste the memo, then press Enter twice on a blank line.")
        print("  Auto-extracts recipients, T-Codes, people, and dates.")
        print()
        lines, blank = [], 0
        try:
            while blank < 2:
                line = input()
                if line == "":
                    blank += 1
                else:
                    blank = 0
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass

        text = "\n".join(lines).strip()
        if not text or text in ("b", "q"):
            break

        clr(); header("memo parse result")

        # auto extraction
        tcodes    = list(dict.fromkeys(re.findall(r"[A-Z][A-Z0-9]{2,9}\d{3,}", text)))
        names     = re.findall(r"([가-힣]{2,4})\s*(매니저|부장|사원|팀장|과장|대리|차장)", text)
        dates     = re.findall(r"\d{1,2}월\s*\d{1,2}일|\d{4}[-./]\d{1,2}[-./]\d{1,2}", text)
        depts     = re.findall(r"[가-힣]{2,6}(?:팀|파트|부|실)", text)
        biz_areas = re.findall(r"업무분야\s*[:\s]*(.+)", text)

        print(f"\n  -- extraction {'--'*20}")
        print(f"  T-Code     : {tcodes or '(none)'}")
        print(f"  people     : {[n+t for n,t in names[:5]] or '(none)'}")
        print(f"  dates      : {dates or '(none)'}")
        print(f"  teams      : {list(dict.fromkeys(depts))[:6] or '(none)'}")
        print(f"  area       : {biz_areas or '(none)'}")

        if tcodes or names:
            print(f"\n  -- archive relevance {'--'*18}")
            kw_auto = tcodes[:4] + [n for n,t in names[:2]]
            _run_intake(kw_auto, text)

        nav_hint(); pause()
        break
    breadcrumb.pop()

def menu_intake():
    breadcrumb.append("new intake")
    items = [
        ("by keyword  (T-Code · terms)",  intake_keyword),
        ("by full text (memo / notes)",   intake_text),
        ("paste a memo / notice",         intake_memo),
    ]
    while True:
        clr(); header("new intake")
        print("\n  Auto-checks duplicates/conflicts/placement before you add to the archive.\n")
        for i, (label, _) in enumerate(items, 1):
            print(f"  [{i}] {label}")
        nav_hint()
        sel = prompt()
        if sel in ("b", "q", ""): break
        if sel.isdigit() and 1 <= int(sel) <= len(items):
            items[int(sel)-1][1]()
    breadcrumb.pop()

# ═════════════════════════════════════════════════════════════════════
# ── 3. archive status ─────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════

def status_list():
    breadcrumb.append("full list")
    arts = load_articles()
    cats = defaultdict(list)
    for a in arts:
        cats[a["cat"]].append(a)

    clr(); header("all articles")
    print()
    for cat, items in sorted(cats.items()):
        print(f"  [ {cat} ({len(items)}) ]")
        for a in items:
            print(f"    #{a['id']:<30}  {a['title'][:36]}")
        print()
    print(f"  total: {len(arts)}")
    nav_hint(); pause()
    breadcrumb.pop()

def status_stats():
    breadcrumb.append("stats")
    arts = load_articles()
    cats = defaultdict(list)
    for a in arts:
        cats[a["cat"]].append(a)

    clr(); header("stats by category")
    print()
    total = len(arts)
    for cat, items in sorted(cats.items(), key=lambda x: -len(x[1])):
        bar = "#" * len(items)
        print(f"  {cat:<16} {len(items):3}  {bar}")
    print(SUBDIV)
    print(f"  {'total':<16} {total:3}")

    # recent updates
    dated = sorted([a for a in arts if a["date"]], key=lambda x: x["date"], reverse=True)
    print(f"\n  -- recent updates (5) {'--'*18}")
    for a in dated[:5]:
        print(f"  {a['date']}  [{a['cat']}]  #{a['id']}  {a['title'][:30]}")
    nav_hint(); pause()
    breadcrumb.pop()

def status_conflict_scan():
    breadcrumb.append("conflict scan")
    clr(); header("full conflict scan")
    print("\n  Scanning the whole archive for all conflict patterns...\n")

    html  = get_html()
    arts  = load_articles()
    found = []

    for pat_a, pat_b in CONFLICT_PAIRS:
        arts_a = set()
        arts_b = set()
        for m in re.finditer(pat_a, html, re.I|re.S):
            arts_a.add(article_at(arts, m.start())["id"])
        for m in re.finditer(pat_b, html, re.I|re.S):
            arts_b.add(article_at(arts, m.start())["id"])
        cross = [(a, b) for a in arts_a for b in arts_b if a != b]
        for pair in cross:
            entry = (pat_a[:30], pair[0], pair[1])
            if entry not in found:
                found.append(entry)

    if not found:
        print("  [OK]  no conflicts")
    else:
        print(f"  [!!]  conflict candidates ({len(found)}):\n")
        for pat, a, b in found:
            print(f"  pattern  : ...{pat}...")
            print(f"  articles : #{a}  <->  #{b}")
            print()

    nav_hint(); pause()
    breadcrumb.pop()

def menu_status():
    breadcrumb.append("archive status")
    items = [
        ("all articles",    status_list),
        ("stats",           status_stats),
        ("conflict scan",   status_conflict_scan),
    ]
    while True:
        clr(); header("archive status")
        print()
        for i, (label, _) in enumerate(items, 1):
            print(f"  [{i}] {label}")
        nav_hint()
        sel = prompt()
        if sel in ("b", "q", ""): break
        if sel.isdigit() and 1 <= int(sel) <= len(items):
            items[int(sel)-1][1]()
    breadcrumb.pop()

# ═════════════════════════════════════════════════════════════════════
# ── 4. quick reference ────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════

def quick_tcode_dict():
    breadcrumb.append("T-Code dict")
    while True:
        clr(); header("T-Code quick dictionary")
        print("  Enter a T-Code to find its screen name and purpose in the archive.")
        print()
        tc = prompt("T-Code (b=back)")
        if tc in ("b", "q", ""): break

        html = get_html()
        # pattern 1: T-Code — screen name
        m1 = re.search(re.escape(tc) + r"\s*(?:—|--)?\s*([^<\n]{4,60})", html, re.I)
        # pattern 2: purpose from a table cell
        m2 = re.search(
            r'<td[^>]*>[^<]*' + re.escape(tc) + r'[^<]*</td>\s*<td[^>]*>([^<]{4,80})',
            html, re.I
        )
        clr(); header(f"T-Code: {tc.upper()}")
        print()
        if m1: print(f"  screen/desc : {norm(strip_tags(m1.group(1)))[:80]}")
        if m2: print(f"  table desc  : {norm(strip_tags(m2.group(1)))[:80]}")
        if not m1 and not m2:
            print(f"  '{tc}' not found in the archive.")

        # related articles
        res = search_html([tc])
        if res:
            print(f"\n  related articles:")
            for art_id, hits in list(res.items())[:4]:
                print(f"    #{art_id}  [{hits[0]['cat']}]  {hits[0]['title']}")
        nav_hint(); pause()
    breadcrumb.pop()

def quick_contacts():
    """Optional: if the archive has a 'contacts' table, list it. Otherwise falls back."""
    breadcrumb.append("contacts")
    clr(); header("key contacts")
    html   = get_html()
    m = re.search(r"주요 담당자 연락처(.+?)(?:</div>\s*</div>)", html, re.I | re.S)
    if m:
        rows = re.findall(r"<tr>(.*?)</tr>", m.group(1), re.S)
        print()
        for row in rows:
            cells = [norm(strip_tags(c)) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            if cells:
                print(f"  {' | '.join(c[:30] for c in cells)}")
    else:
        print("\n  (no contacts table in this archive)")
    nav_hint(); pause()
    breadcrumb.pop()

def quick_io_types():
    breadcrumb.append("IO types")
    clr(); header("IO type quick reference")
    # pull the IO-type table from archive-structure.md, if present
    md_path = BASE / "archive-structure.md"
    if md_path.exists():
        md = md_path.read_text(encoding="utf-8")
        m  = re.search(r"IO type quick reference(.+?)(?=\n##|\Z)", md, re.S)
        if m:
            print(m.group(1)[:800])
        else:
            print("\n  (no IO-type section found in archive-structure.md)")
    else:
        print("\n  (archive-structure.md not found)")
    nav_hint(); pause()
    breadcrumb.pop()

def menu_quick():
    breadcrumb.append("quick reference")
    items = [
        ("T-Code dictionary", quick_tcode_dict),
        ("contacts",          quick_contacts),
        ("IO types",          quick_io_types),
    ]
    while True:
        clr(); header("quick reference")
        print()
        for i, (label, _) in enumerate(items, 1):
            print(f"  [{i}] {label}")
        nav_hint()
        sel = prompt()
        if sel in ("b", "q", ""): break
        if sel.isdigit() and 1 <= int(sel) <= len(items):
            items[int(sel)-1][1]()
    breadcrumb.pop()

# ═════════════════════════════════════════════════════════════════════
# ── main menu ─────────────────────────────────────────────────────────
# ═════════════════════════════════════════════════════════════════════

MAIN_ITEMS = [
    ("[1]  search          keyword / category / T-Code / person", menu_search),
    ("[2]  new intake      duplicate · conflict check + placement", menu_intake),
    ("[3]  archive status  list · stats · conflict scan",          menu_status),
    ("[4]  quick reference T-Code dict · contacts · IO types",     menu_quick),
]

def main():
    while True:
        clr()
        print(f"\n{'='*W}")
        print(f"  Indexable Knowledge Archive  |  ops helper")
        print(f"{'='*W}\n")
        for label, _ in MAIN_ITEMS:
            print(f"  {label}")
        print(f"\n  [0]  quit")
        print(f"\n{'='*W}")

        sel = prompt("select")
        if sel in ("0", "q", ""):
            print("\n  bye.\n")
            break
        if sel.isdigit() and 1 <= int(sel) <= len(MAIN_ITEMS):
            MAIN_ITEMS[int(sel)-1][1]()

if __name__ == "__main__":
    main()
