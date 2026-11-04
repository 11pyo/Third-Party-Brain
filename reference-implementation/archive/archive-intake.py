#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive-intake.py (v2.0 — SSOT Markdown & Hybrid BM25 Intake Engine)
Indexable Knowledge Archive — new-information intake & data-quality gate

Directly parses canonical Markdown articles (`articles/*/*.md`, with fallback to `archive.html`),
scores relevance via field-weighted hits + char-2gram BM25, and checks:
  1) Duplicate / near-duplicate (hybrid char-2gram + token recall, tolerant of Korean particle variation)
  2) Procedural sequence conflict ([!!] CONFLICT)
  3) Code definition divergence ([?] DEF_DIFF across dictionary articles and incoming text)
  4) Recommended SSOT category and file path (`articles/<cat>/<id>.md` -> `python build_archive.py`)

Usage:
  python archive-intake.py "keyword1" "keyword2" ...
  python archive-intake.py "keyword1" --text "full text to add"
"""

import argparse
import io
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

try:
    from rank_bm25 import BM25Okapi
    _HAS_BM25 = True
except ImportError:
    _HAS_BM25 = False

# ── paths ─────────────────────────────────────────────────────────────
BASE         = Path(__file__).parent
ARTICLES_DIR = BASE / "articles"
ARCHIVE      = BASE / "archive.html"
STRUCTURE    = BASE / "archive-structure.md"

CAT_DIRS = {
    "기초용어":       "01_terms",
    "프로세스":       "02_process",
    "기술설정":       "03_tech",
    "트러블슈팅":     "04_troubleshoot",
    "운영참조매뉴얼": "05_manual",
}

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
    (r"VF11.{0,40}VL09",              r"VL09.{0,40}VF11"),
    (r"회계.{0,15}(먼저|선행)",        r"재고.{0,15}(먼저|선행)"),
]

CODE_RE = re.compile(r"^(Z[A-Z]{1,4}\d{2,5}[A-Z]?|VF\d{2}|VL\d{2}N?|FD\d{2,3}|VKM\d|MMRV|MMPV|SU01D?)$", re.I)

DICT_ARTICLES = {
    "tcode-extended", "tcode-zsd-all", "ztsd-tables", "data-elements",
    "tcode-master", "order-type-io", "sales-order-type", "purchase-type", "doc-matching",
}

ALIASES = {
    "매출취소": ["취소요청", "빌링취소", "ZSD030", "ZSD034", "VF11"],
    "출고취소": ["VL09", "납품취소", "ZTSD075"],
    "권한":     ["SU01", "역할", "ZSD110"],
    "결산":     ["월말", "마감", "D+1", "D+2", "ZSD143"],
    "여신":     ["Credit", "BLOCK", "FD32", "VKM4", "ZTSD071"],
}

W = 66
_ARTS_CACHE = None


def strip_tags(html):
    return re.sub(r"<[^>]+>", " ", html)


def normalize(s):
    return re.sub(r"\s+", " ", s).strip()


def _char_bigrams(t):
    t = re.sub(r"\s+", "", t.lower())
    return set(t[i:i+2] for i in range(len(t) - 1)) if len(t) >= 2 else ({t} if t else set())


def _tok_char2(s):
    s = re.sub(r"\s+", "", s.lower())
    return [s[i:i+2] for i in range(len(s) - 1)] if len(s) >= 2 else ([s] if s else [])


def expand_keywords(keywords):
    expanded = list(keywords)
    for kw in keywords:
        for base, aliases in ALIASES.items():
            if kw.upper() in [a.upper() for a in aliases] or kw == base or base in kw:
                expanded.extend(aliases)
    return list(dict.fromkeys(expanded))


def _def_snippet(ctx, keyword, after=60):
    idx = ctx.lower().find(keyword.lower())
    if idx == -1:
        return ""
    snip = ctx[idx + len(keyword): idx + len(keyword) + after]
    cut = re.search(r"\bZ[A-Z]{2,4}\d{2,5}", snip)
    if cut:
        snip = snip[:cut.start()]
    return normalize(snip)


def _looks_definitional(snip):
    if not snip:
        return False
    s = snip.strip()
    if any(ch in s for ch in ("#", "→", "\"", "“", "”")):
        return False
    if "참조" in s or "순서)" in s:
        return False
    return bool(re.match(r"[A-Za-z가-힣]", s))


def detect_definition_divergence(art_hits, new_text="", keywords=None):
    """Compare definitions of code tokens across DICT_ARTICLES and incoming new_text."""
    by_kw = defaultdict(dict)
    for art_id, items in art_hits.items():
        if art_id not in DICT_ARTICLES and art_id != "NEW":
            continue
        for it in items:
            kw = it["keyword"]
            if not CODE_RE.match(kw) or art_id in by_kw[kw]:
                continue
            snip = _def_snippet(it["ctx"], kw)
            if len(re.sub(r"\s+", "", snip)) >= 4 and _looks_definitional(snip):
                by_kw[kw][art_id] = snip

    if new_text:
        cand_kws = list(keywords or []) + re.findall(r"\b[A-Za-z0-9_]{4,12}\b", new_text)
        for kw in dict.fromkeys(cand_kws):
            if not CODE_RE.match(kw) or "NEW" in by_kw[kw]:
                continue
            snip = _def_snippet(new_text, kw)
            if len(re.sub(r"\s+", "", snip)) >= 4 and _looks_definitional(snip):
                by_kw[kw]["NEW"] = snip

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
                if jac < 0.18:
                    flags.append((kw, a, amap[a], b, amap[b], jac))
    return flags


def load_ssot_articles(use_cache=True):
    """Load canonical Markdown articles from `articles/*/*.md` (fallback to `archive.html`)."""
    global _ARTS_CACHE
    if use_cache and _ARTS_CACHE is not None:
        return _ARTS_CACHE
    arts = []
    if ARTICLES_DIR.exists() and _HAS_YAML:
        for md_file in sorted(ARTICLES_DIR.glob("*/*.md")):
            text = md_file.read_text(encoding="utf-8").lstrip("\ufeff").replace("\r\n", "\n")
            m = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$", text)
            if not m:
                continue
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except Exception:
                continue
            aid = fm.get("id") or md_file.stem
            title = str(fm.get("title") or aid).strip()
            cat = str(fm.get("category") or fm.get("badge_text") or "?").strip()
            tags_str = " ".join([
                str(fm.get("data_tags") or ""),
                str(fm.get("struct_keywords") or ""),
                " ".join(fm.get("tag_chips") or []),
            ]).strip()
            plain_body = normalize(strip_tags(m.group(2)))
            arts.append({
                "id":       aid,
                "title":    title,
                "category": cat,
                "tags":     tags_str,
                "related":  str(fm.get("data_related") or ""),
                "date":     str(fm.get("date") or ""),
                "path":     str(md_file.relative_to(BASE)).replace("\\", "/"),
                "body":     plain_body,
                "full":     f"{title} {tags_str} {plain_body}",
            })
        if arts:
            _ARTS_CACHE = arts
            return arts

    html = ARCHIVE.read_text(encoding="utf-8")
    for m in re.finditer(r'<article[^>]+id="([^"]+)"', html):
        close_idx = html.find("</article>", m.start())
        end = (close_idx + len("</article>")) if close_idx != -1 else len(html)
        chunk = html[m.start():end]
        title_m = re.search(r'class="at">([^<]+)', chunk[:600])
        badge_m = re.search(r'class="badge[^"]*">([^<]+)', chunk[:600])
        tags_m = re.search(r'data-tags="([^"]*)"', chunk[:600])
        aid = m.group(1)
        matches = list(ARTICLES_DIR.glob(f"*/{aid}.md")) if ARTICLES_DIR.exists() else []
        md_path = str(matches[0].relative_to(BASE)).replace("\\", "/") if matches else f"articles/*/{aid}.md"
        plain_body = normalize(strip_tags(chunk))
        arts.append({
            "id":       aid,
            "title":    title_m.group(1).strip() if title_m else "?",
            "category": badge_m.group(1).strip() if badge_m else "?",
            "tags":     tags_m.group(1) if tags_m else "",
            "related":  "",
            "date":     "",
            "path":     md_path,
            "body":     plain_body,
            "full":     plain_body,
        })
    return arts


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


def compute_similarity(new_text, doc_text):
    """Hybrid char-2gram recall + token recall tolerant of Korean particle variation."""
    g_new = _char_bigrams(new_text)
    g_doc = _char_bigrams(doc_text)
    if not g_new or not g_doc:
        return 0.0
    bigram_recall = len(g_new & g_doc) / max(len(g_new), 1)
    new_words = set(re.findall(r"[A-Za-z0-9가-힣_]{2,}", new_text.lower()))
    doc_words = set(re.findall(r"[A-Za-z0-9가-힣_]{2,}", doc_text.lower()))
    word_recall = len(new_words & doc_words) / max(len(new_words), 1) if new_words else 0.0
    return 0.6 * bigram_recall + 0.4 * word_recall


def run(raw_keywords, new_text="", verbose=False):
    arts = load_ssot_articles()
    by_id = {a["id"]: a for a in arts}
    keywords = expand_keywords(raw_keywords)

    print(f"\n{'='*W}")
    print(f"  [INTAKE v2] SSOT MARKDOWN & HYBRID BM25 INTAKE ENGINE")
    print(f"  canonical corpus: {len(arts)} markdown articles (articles/*/*.md)")
    print(f"  input keywords  : {raw_keywords}")
    extras = [k for k in keywords if k not in raw_keywords]
    if extras:
        print(f"  expanded        : +{extras[:10]}")
    print(f"{'='*W}")

    art_hits = defaultdict(list)
    art_scores = defaultdict(float)

    for a in arts:
        aid = a["id"]
        header_hay = f"{a['title']} {a['tags']}".lower()
        for kw in keywords:
            pat = re.compile(re.escape(kw), re.I)
            if pat.search(header_hay):
                art_scores[aid] += 4.0 if kw in raw_keywords else 1.5
            for m in pat.finditer(a["full"]):
                s = max(0, m.start() - 220)
                e = min(len(a["full"]), m.end() + 220)
                ctx = a["full"][s:e]
                art_hits[aid].append({
                    "keyword": kw,
                    "ctx":     ctx,
                    "title":   a["title"],
                    "cat":     a["category"],
                })
                art_scores[aid] += 1.0 if kw in raw_keywords else 0.35

    if _HAS_BM25 and arts and (raw_keywords or new_text):
        query_str = " ".join(raw_keywords) + (" " + new_text if new_text else "")
        bm25 = BM25Okapi([_tok_char2(a["full"]) for a in arts])
        b_scores = bm25.get_scores(_tok_char2(query_str))
        for idx, sc in enumerate(b_scores):
            if sc > 0 and arts[idx]["id"] in art_hits:
                art_scores[arts[idx]["id"]] += float(sc) * 0.5

    if not art_hits:
        print(f"\n  [OK]  no duplicate — not in the archive yet\n")
        cats = suggest_category(new_text or " ".join(raw_keywords))
        rec_cat = cats[0][0]
        rec_dir = CAT_DIRS.get(rec_cat, "04_troubleshoot")
        top = [f"{c}({s})" for c, s in cats if s > 0]
        print(f"  [CAT] suggested category : {rec_cat} (folder: articles/{rec_dir}/)")
        if top:
            print(f"        score evidence     : {' / '.join(top)}")
        print(f"\n  [>>]  recommended action (SSOT Markdown workflow):")
        print(f"        1) create articles/{rec_dir}/<new-id>.md (with YAML frontmatter)")
        print(f"        2) run: python build_archive.py (auto-compiles nav, counts, structure & backlinks)")
        print(f"\n{'='*W}\n")
        return {"status": "NEW", "category": rec_cat}

    ranked_ids = sorted(art_hits.keys(), key=lambda x: -art_scores[x])
    total_hits = sum(len(v) for v in art_hits.values())
    print(f"\n  [HIT] {total_hits} hits  /  {len(ranked_ids)} related articles (ranked by hybrid score)\n")

    art_contexts = {}
    for art_id in ranked_ids[:6]:
        items = art_hits[art_id]
        a_meta = by_id[art_id]
        kws = list(dict.fromkeys(i["keyword"] for i in items))
        print(f"  [ART] #{art_id}  [{a_meta['category']}]  (score: {art_scores[art_id]:.1f})")
        print(f"        title    : {a_meta['title']}")
        print(f"        ssot     : {a_meta['path']}")
        print(f"        keywords : {kws[:7]}")
        for item in items[:2]:
            ex = excerpt(item["ctx"], item["keyword"])
            print(f"        excerpt  : \"{ex}\"")
        print()
        art_contexts[art_id] = " ".join(i["ctx"] for i in items)

    for art_id in ranked_ids[6:]:
        art_contexts[art_id] = " ".join(i["ctx"] for i in art_hits[art_id])

    conflicts = []
    top_check_ids = ranked_ids[:10]
    for i in range(len(top_check_ids)):
        for j in range(i + 1, len(top_check_ids)):
            if detect_conflict(art_contexts[top_check_ids[i]], art_contexts[top_check_ids[j]]):
                conflicts.append((top_check_ids[i], top_check_ids[j], "existing<->existing"))

    if new_text:
        for art_id in top_check_ids:
            if detect_conflict(new_text, art_contexts[art_id]):
                conflicts.append(("NEW", art_id, "new<->existing"))

    if conflicts:
        print(f"  [!!]  conflicts detected ({len(conflicts)}):")
        for a, b, typ in conflicts:
            ta = "new content" if a == "NEW" else f"#{a}"
            print(f"        {ta}  <->  #{b}  [{typ}]")
            print(f"        -> compare/verify the two articles' procedure order")
        print()

    defdiv = detect_definition_divergence(art_hits, new_text=new_text, keywords=keywords)
    if defdiv:
        print(f"  [?]   definition mismatch suspected ({len(defdiv)}) — same code, different desc:")
        for kw, a, sa, b, sb, jac in defdiv:
            print(f"        {kw}: #{a}(\"{sa[:40]}\") vs #{b}(\"{sb[:40]}\") [overlap {jac:.0%}]")
        print()

    if new_text:
        for art_id in ranked_ids[:5]:
            overlap = compute_similarity(new_text, by_id[art_id]["full"])
            if overlap > 0.68:
                print(f"  [DUP] likely duplicate: new content is {overlap:.0%} similar to #{art_id} ({by_id[art_id]['path']})")
                print(f"        -> no new article needed; update SSOT or append via archive-note.py\n")

    print(f"  [>>]  recommended action (SSOT Markdown workflow):")
    top_id = ranked_ids[0]
    top_meta = by_id[top_id]

    if conflicts:
        print(f"        -> compare conflicting articles, then unify SSOT (.md):")
        for a, b, _ in conflicts:
            label = "new" if a == "NEW" else f"#{a}"
            print(f"           {label} vs #{b} -- verify in practice, merge into SSOT")
    elif len(ranked_ids) == 1 or (len(ranked_ids) >= 2 and art_scores[ranked_ids[0]] >= art_scores[ranked_ids[1]] * 1.8):
        print(f"        -> top target article: #{top_id} ({top_meta['title']})")
        print(f"           SSOT file   : {top_meta['path']}")
        print(f"           1-line note : python archive-note.py --id {top_id} --note \"<note>\"")
        print(f"           body update : edit {top_meta['path']} then run python build_archive.py")
    elif len(ranked_ids) == 2:
        print(f"        -> update whichever SSOT article is more relevant:")
        for aid in ranked_ids:
            print(f"           - #{aid} ({by_id[aid]['title']}) -> {by_id[aid]['path']}")
    else:
        cats = suggest_category(new_text or " ".join(raw_keywords))
        rec_cat = cats[0][0]
        rec_dir = CAT_DIRS.get(rec_cat, "04_troubleshoot")
        print(f"        -> top related candidate: #{top_id} ({top_meta['path']})")
        print(f"        -> or if independent topic, create articles/{rec_dir}/<new-id>.md then run python build_archive.py")

    print(f"\n{'='*W}\n")
    return {
        "status":    "CONFLICT" if conflicts else ("UPDATE" if len(ranked_ids) == 1 else "REVIEW"),
        "articles":  ranked_ids,
        "conflicts": conflicts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Archive intake (v2 SSOT) — auto duplicate/conflict/placement check"
    )
    parser.add_argument("keywords", nargs="*", help="search keywords (multiple allowed)")
    parser.add_argument("--text",    default="", help="full text to add (optional)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.keywords and not args.text:
        parser.print_help()
        sys.exit(1)

    run(args.keywords, args.text, args.verbose)
