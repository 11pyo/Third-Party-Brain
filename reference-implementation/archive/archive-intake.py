#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive-intake.py
Indexable Knowledge Archive — new-information intake checker

Before you add new content to the archive, this tells you:
  1) is it a duplicate?   2) does it conflict with existing content?
  3) where should it go (which category / which article)?
…so the archive stays consistent instead of accumulating contradictions.

Usage:
  python archive-intake.py "keyword1" "keyword2" ...
  python archive-intake.py "keyword1" --text "full text to add"

Examples:
  python archive-intake.py "ZSD030" "매출취소"
  python archive-intake.py "ZTSD071" "여신 한도"
  python archive-intake.py "신규 입사자" "SU01" --text "Account managed by the IT team"
"""

import re, sys, argparse
from pathlib import Path
from collections import defaultdict

# force UTF-8 stdout (Windows CP949 environments)
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── paths ─────────────────────────────────────────────────────────────
BASE      = Path(__file__).parent
ARCHIVE   = BASE / "archive.html"
STRUCTURE = BASE / "archive-structure.md"

# ── category classification signals ──────────────────────────────────
CATEGORY_SIGNALS = {
    "기초용어":       ["유형", "코드", "정의", "용어", "T-Code", "테이블", "데이터 엘리먼트"],
    "프로세스":       ["흐름", "절차", "단계", "순서", "프로세스", "오더", "승인"],
    "기술설정":       ["설정", "아키텍처", "결산", "CTS", "환경", "배치", "세그먼트"],
    "트러블슈팅":     ["오류", "에러", "Error", "Dump", "문제", "해결", "안 된다", "Block"],
    "운영참조매뉴얼": ["매뉴얼", "참조", "가이드", "임시", "변경 불가"],
}

# ── conflict patterns (detect reversed procedure order) ──────────────
#   Sample codes (ZTSD*/ZMM*) are fictional; VL09/VF11 are standard SAP.
CONFLICT_PAIRS = [
    (r"먼저.{0,30}다음",              r"다음.{0,30}먼저"),
    (r"삭제.{0,20}후.{0,20}취소",     r"취소.{0,20}후.{0,20}삭제"),
    (r"ZTSD070.{0,40}ZMM213",         r"ZMM213.{0,40}ZTSD070"),
    (r"VL09.{0,40}ZTSD",              r"ZTSD.{0,40}VL09"),
    (r"VF11.{0,40}VL09",              r"VL09.{0,40}VF11"),         # accounting-cancel→stock-cancel vs reverse
    (r"회계.{0,15}(먼저|선행)",        r"재고.{0,15}(먼저|선행)"),   # accounting-first vs stock-first
]

# ── definition-divergence heuristic (same code, different description) ─
#   Catches "definition conflicts" where the same code is described differently across articles.
#   Collects the 'description' following a code token per article and compares with char-bigram
#   similarity → low similarity flags a suspect.
#   ⚠️ It's a heuristic (false positives possible) → reported as a soft "[?] suspect", distinct
#   from a hard CONFLICT.
CODE_RE = re.compile(r"^(Z[A-Z]{1,4}\d{2,5}[A-Z]?|VF\d{2}|VL\d{2}N?|FD\d{2,3}|VKM\d|MMRV|MMPV|SU01D?)$", re.I)

# The "canonical" definitions live in dictionary/reference articles — only a mismatch *between
# these* is a real problem. (Codes quoted in prose inside troubleshooting/process articles are
# not definitions, so they're excluded to avoid false positives.)
DICT_ARTICLES = {
    "tcode-extended", "tcode-zsd-all", "ztsd-tables", "data-elements",
    "tcode-master", "order-type-io", "sales-order-type", "purchase-type", "doc-matching",
}

def _def_snippet(ctx, keyword, after=60):
    idx = ctx.lower().find(keyword.lower())
    if idx == -1:
        return ""
    snip = ctx[idx + len(keyword): idx + len(keyword) + after]
    # cut at the next 'custom code' so we don't bleed into the next row's description.
    # keep CR/DR, I/O etc. — so we do NOT cut on '/' or arrows.
    cut = re.search(r"\bZ[A-Z]{2,4}\d{2,5}", snip)
    if cut:
        snip = snip[:cut.start()]
    return normalize(snip)

def _char_bigrams(t):
    t = re.sub(r"\s+", "", t)
    return set(t[i:i+2] for i in range(len(t) - 1))

def _looks_definitional(snip):
    """Only let 'definition-like' snippets through — blocks false positives from prose/cross-link
    fragments. (A code quoted mid-sentence, rather than in a definition table, is excluded.)"""
    if not snip:
        return False
    s = snip.strip()
    # link/sentence-fragment markers → not a definition
    if any(ch in s for ch in ("#", "→", "\"", "“", "”")):
        return False
    if "참조" in s or "순서)" in s:
        return False
    # first meaningful char must be Hangul/Latin (drops fragments cut mid-sentence)
    return bool(re.match(r"[A-Za-z가-힣]", s))

def detect_definition_divergence(art_hits):
    """If a code keyword appears in 2+ articles but the 'descriptions' differ a lot → suspect a
    definition mismatch."""
    by_kw = defaultdict(dict)  # kw -> {art_id: snippet}
    for art_id, items in art_hits.items():
        if art_id not in DICT_ARTICLES:      # compare only dictionary articles (avoid prose-quote false positives)
            continue
        for it in items:
            kw = it["keyword"]
            if not CODE_RE.match(kw) or art_id in by_kw[kw]:
                continue
            snip = _def_snippet(it["ctx"], kw)
            if len(re.sub(r"\s+", "", snip)) >= 4 and _looks_definitional(snip):
                by_kw[kw][art_id] = snip
    flags = []
    for kw, amap in by_kw.items():
        ids = list(amap.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                ga, gb = _char_bigrams(amap[a]), _char_bigrams(amap[b])
                if not ga or not gb:
                    continue
                jac = len(ga & gb) / len(ga | gb)
                if jac < 0.18:   # conservative threshold — minimize noise
                    flags.append((kw, a, amap[a], b, amap[b], jac))
    return flags

# ── synonym / alias map (auto query expansion) ───────────────────────
ALIASES = {
    "매출취소": ["취소요청", "빌링취소", "ZSD030", "ZSD034"],
    "출고취소": ["VL09", "납품취소", "ZTSD075"],
    "권한":     ["SU01", "역할", "ZSD110"],
    "결산":     ["월말", "마감", "D+1", "D+2", "ZSD143"],
    "여신":     ["Credit", "BLOCK", "FD32", "VKM4", "ZTSD071"],
}

W = 62  # output width

# ─────────────────────────────────────────────────────────────────────
def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html)

def normalize(s):
    return re.sub(r"\s+", " ", s).strip()

def expand_keywords(keywords):
    """Expand the search scope via synonyms."""
    expanded = list(keywords)
    for kw in keywords:
        for base, aliases in ALIASES.items():
            if kw.upper() in [a.upper() for a in aliases] or kw == base:
                expanded.extend(aliases)
    return list(dict.fromkeys(expanded))  # dedupe, keep order

def load_articles(html):
    arts = []
    for m in re.finditer(r'<article[^>]+id="([^"]+)"', html):
        title_m = re.search(r'class="at">([^<]+)', html[m.start():m.start()+400])
        badge_m = re.search(r'class="badge[^"]*">([^<]+)', html[m.start():m.start()+500])
        arts.append({
            "id":       m.group(1),
            "title":    title_m.group(1).strip() if title_m else "?",
            "category": badge_m.group(1).strip() if badge_m else "?",
            "pos":      m.start(),
        })
    return arts

def article_at(arts, pos):
    best = arts[0] if arts else {"id": "?", "title": "?", "category": "?"}
    for a in arts:
        if a["pos"] <= pos:
            best = a
        else:
            break
    return best

def search_archive(html, keywords):
    results = []
    for kw in keywords:
        pat = re.compile(re.escape(kw), re.I)
        for m in pat.finditer(html):
            s   = max(0, m.start() - 250)
            e   = min(len(html), m.end() + 250)
            ctx = normalize(strip_tags(html[s:e]))
            results.append({"keyword": kw, "pos": m.start(), "ctx": ctx})
    return results

def suggest_category(text):
    scores = {
        cat: sum(1 for sig in sigs if re.search(sig, text, re.I))
        for cat, sigs in CATEGORY_SIGNALS.items()
    }
    return sorted(scores.items(), key=lambda x: -x[1])

def detect_conflict(ctx_a, ctx_b):
    for pat_a, pat_b in CONFLICT_PAIRS:
        a_in_a = bool(re.search(pat_a, ctx_a, re.I | re.S))
        b_in_b = bool(re.search(pat_b, ctx_b, re.I | re.S))
        a_in_b = bool(re.search(pat_a, ctx_b, re.I | re.S))
        b_in_a = bool(re.search(pat_b, ctx_a, re.I | re.S))
        if (a_in_a and b_in_b) or (a_in_b and b_in_a):
            return True
    return False

def excerpt(ctx, keyword, window=55):
    idx = ctx.lower().find(keyword.lower())
    if idx == -1:
        return ctx[:110]
    s = max(0, idx - window)
    e = min(len(ctx), idx + len(keyword) + window)
    prefix = "..." if s > 0 else ""
    suffix = "..." if e < len(ctx) else ""
    return prefix + ctx[s:e] + suffix

# ─────────────────────────────────────────────────────────────────────
def run(raw_keywords, new_text="", verbose=False):
    html = ARCHIVE.read_text(encoding="utf-8")
    arts = load_articles(html)
    keywords = expand_keywords(raw_keywords)

    print(f"\n{'='*W}")
    print(f"  [INTAKE] ARCHIVE INTAKE CHECK")
    print(f"  input keywords  : {raw_keywords}")
    extras = [k for k in keywords if k not in raw_keywords]
    if extras:
        print(f"  expanded        : +{extras}")
    print(f"{'='*W}")

    # ── STEP 1: search ──────────────────────────────────────────────
    hits = search_archive(html, keywords)

    if not hits:
        print(f"\n  [OK]  no duplicate — not in the archive yet\n")
        cats = suggest_category(new_text or " ".join(raw_keywords))
        top  = [f"{c}({s})" for c, s in cats if s > 0]
        print(f"  [CAT] suggested category : {cats[0][0]}")
        if top:
            print(f"        score evidence     : {' / '.join(top)}")
        print(f"\n  [>>]  recommended action :")
        print(f"        -> write a new article  (category: {cats[0][0]})")
        print(f"        -> add a sidebar nav link")
        print(f"        -> bump the category count +1")
        print(f"        -> sync archive-structure.md")
        print(f"\n{'='*W}\n")
        return {"status": "NEW", "category": cats[0][0]}

    # ── STEP 2: aggregate hits per article ──────────────────────────
    art_hits = defaultdict(list)
    for h in hits:
        a = article_at(arts, h["pos"])
        art_hits[a["id"]].append({
            "keyword": h["keyword"],
            "ctx":     h["ctx"],
            "title":   a["title"],
            "cat":     a["category"],
        })

    total_hits = sum(len(v) for v in art_hits.values())
    print(f"\n  [HIT] {total_hits} hits  /  {len(art_hits)} articles\n")

    art_contexts = {}
    for art_id, items in art_hits.items():
        title = items[0]["title"]
        cat   = items[0]["cat"]
        kws   = list(dict.fromkeys(i["keyword"] for i in items))
        print(f"  [ART] #{art_id}  [{cat}]")
        print(f"        title    : {title}")
        print(f"        keywords : {kws[:6]}")
        for item in items[:2]:
            ex = excerpt(item["ctx"], item["keyword"])
            print(f"        excerpt  : \"{ex}\"")
        print()
        art_contexts[art_id] = " ".join(i["ctx"] for i in items)

    # ── STEP 3: conflict detection ──────────────────────────────────
    art_ids   = list(art_hits.keys())
    conflicts = []

    for i in range(len(art_ids)):
        for j in range(i + 1, len(art_ids)):
            if detect_conflict(art_contexts[art_ids[i]], art_contexts[art_ids[j]]):
                conflicts.append((art_ids[i], art_ids[j], "existing<->existing"))

    if new_text:
        for art_id, ctx in art_contexts.items():
            if detect_conflict(new_text, ctx):
                conflicts.append(("NEW", art_id, "new<->existing"))

    if conflicts:
        print(f"  [!!]  conflicts detected ({len(conflicts)}):")
        for a, b, typ in conflicts:
            ta = "new content" if a == "NEW" else f"#{a}"
            print(f"        {ta}  <->  #{b}  [{typ}]")
            print(f"        -> compare/verify the two articles' procedure order")
        print()

    # ── STEP 3b: definition-divergence heuristic (same code, different desc) ─
    defdiv = detect_definition_divergence(art_hits)
    if defdiv:
        print(f"  [?]   definition mismatch suspected ({len(defdiv)}) — same code, different desc:")
        for kw, a, sa, b, sb, jac in defdiv:
            print(f"        {kw}:")
            print(f"          #{a}: \"{sa[:46]}\"")
            print(f"          #{b}: \"{sb[:46]}\"   (overlap {jac:.0%})")
            print(f"        -> compare/unify the {kw} definition (heuristic, may be a false positive)")
        print()

    # ── STEP 4: duplicate judgment ──────────────────────────────────
    if new_text:
        new_words = set(re.findall(r"\w{2,}", new_text))
        for art_id, ctx in art_contexts.items():
            ctx_words = set(re.findall(r"\w{2,}", ctx))
            overlap   = len(new_words & ctx_words) / max(len(new_words), 1)
            if overlap > 0.70:
                print(f"  [DUP] likely duplicate: new content is {overlap:.0%} similar to #{art_id}")
                print(f"        -> probably no new article needed; update the existing one\n")

    # ── STEP 5: recommended action ──────────────────────────────────
    print(f"  [>>]  recommended action:")

    if conflicts:
        print(f"        -> compare conflicting articles, then decide manually:")
        for a, b, _ in conflicts:
            label = "new" if a == "NEW" else f"#{a}"
            print(f"           {label} vs #{b} -- verify in practice, merge into one")

    elif len(art_hits) == 1:
        art_id = art_ids[0]
        title  = art_hits[art_id][0]["title"]
        print(f"        -> #{art_id} ({title})")
        print(f"           add a section to / update the existing article")

    elif len(art_hits) == 2:
        print(f"        -> add to whichever of {art_ids} is more relevant")
        print(f"           or cross-link the two articles")

    else:
        cats = suggest_category(new_text or " ".join(raw_keywords))
        print(f"        -> many related articles ({len(art_hits)}) -- a new article is recommended")
        print(f"           suggested category: {cats[0][0]}")

    if new_text:
        cats = suggest_category(new_text)
        if cats[0][1] > 0:
            print(f"\n  [CAT] new-content category estimate: {cats[0][0]}")

    print(f"\n{'='*W}\n")

    return {
        "status":    "CONFLICT" if conflicts else ("UPDATE" if len(art_hits) == 1 else "REVIEW"),
        "articles":  art_ids,
        "conflicts": conflicts,
    }

# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive intake — auto duplicate/conflict/placement check"
    )
    parser.add_argument("keywords", nargs="*", help="search keywords (multiple allowed)")
    parser.add_argument("--text",    default="", help="full text to add (optional)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.keywords and not args.text:
        parser.print_help()
        sys.exit(1)

    run(args.keywords, args.text, args.verbose)
