# -*- coding: utf-8 -*-
"""archive-note.py — append a dated follow-up line to an existing article, safely.
아티클에 「날짜 + 후속 한 줄」을 안전하게 덧붙인다 (2026-09-28 도입).

Why: as an investigation unfolds, facts arrive one at a time. Appending each by hand-written
one-off edit scripts breaks when anchors move, and one unclosed inline tag nests every
following article inside it. This tool fixes the procedure: exactly-one id, balanced inline
tags, article count unchanged, backup then atomic replace.


왜: 조사가 이어지며 사실이 하나씩 늘 때마다 매번 일회용 편집 스크립트를 새로 짜서
    앵커 문자열을 찾아 붙였다(한 문단에 6번). 앵커가 바뀌면 깨지고, 인라인 태그를 안 닫으면
    뒤 아티클이 통째로 중첩되는 사고(2026-08-20)가 난다. 이 도구가 그 절차를 고정한다.

동작:
  - `id="<아티클id>"` 아티클을 정확히 1개 찾는다(없거나 여럿이면 중단).
  - 그 아티클 끝에 「📌 후속 기록」 섹션(`<div class="sec followups">`)이 없으면 만들고,
    그 안에 `<p class="small">📌 <strong>날짜</strong> · 내용</p>` 한 줄을 추가한다(최신이 아래).
  - 머리의 기록 날짜(`<span class="db">`)를 그 날짜로 올린다 → 🕒 최근 색인에 뜬다(`--keep-date`로 끔).
  - 쓰기 전 검증: 내용의 인라인 태그 짝 · 아티클 수 불변 · 대상 아티클이 여전히 1개.
    통과하면 `archive.html.prev` 백업 후 교체. `--dry-run` 이면 결과 줄만 보여 주고 쓰지 않는다.
  - 아티클 추가·삭제가 아니므로 archive-structure.md 표는 바뀌지 않는다(행·카운트 동일).

사용:
  python archive-note.py --id tcode-master --note "owner confirmed — see ticket INQ-260105-101200"
  python archive-note.py --id ztsd-tables --note "<strong>원인 확정</strong>: …" --date 2026-09-28 --dry-run
"""
import argparse
import datetime
import io
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(HERE, "archive.html")
INLINE = ("strong", "b", "em", "i", "a", "code", "span", "small", "u", "mark")
SEC_OPEN = '<div class="sec followups">\n    <div class="st">📌 후속 기록</div>\n'


def die(msg):
    print("❌ " + msg)
    sys.exit(1)


def check_inline(note):
    for t in INLINE:
        o = len(re.findall(r"<%s(\s[^>]*)?>" % t, note))
        c = len(re.findall(r"</%s>" % t, note))
        if o != c:
            die("내용의 <%s> 태그 짝이 안 맞습니다(열림 %d · 닫힘 %d) — 닫지 않은 태그는 뒤 아티클을 삼킵니다." % (t, o, c))
    if re.search(r"</?(article|div|section|script|style)\b", note, re.I):
        die("내용에 블록 태그(article·div·section·script·style)는 넣을 수 없습니다 — 인라인 태그만.")


def count_articles(html):
    return len(re.findall(r'<article\s+class="article[^"]*"', html))


def main():
    ap = argparse.ArgumentParser(description="아카이브 아티클에 날짜별 후속 한 줄 추가")
    ap.add_argument("--id", required=True, help="아티클 id (예: tcode-master)")
    ap.add_argument("--note", required=True, help="추가할 한 줄 (인라인 HTML 허용: strong·a·code 등)")
    ap.add_argument("--date", default=datetime.date.today().isoformat(), help="기본 = 오늘")
    ap.add_argument("--keep-date", action="store_true", help="머리의 기록 날짜를 올리지 않음")
    ap.add_argument("--dry-run", action="store_true", help="쓰지 않고 결과만 표시")
    a = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
        die("--date 형식은 YYYY-MM-DD")
    note = a.note.strip()
    if not note:
        die("--note 가 비었습니다")
    check_inline(note)

    html = io.open(ARCHIVE, encoding="utf-8").read()
    before = count_articles(html)
    starts = [m.start() for m in re.finditer(r'<article\s+class="article[^"]*"[^>]*\bid="%s"' % re.escape(a.id), html)]
    if len(starts) != 1:
        die('id="%s" 아티클이 %d개입니다(정확히 1개여야 함). archive-structure.md 표에서 id를 확인하세요.' % (a.id, len(starts)))
    s = starts[0]
    e = html.find("</article>", s)
    if e < 0:
        die("아티클 끝(</article>)을 찾지 못했습니다")
    art = html[s:e]
    if art.count("<article") != 1:
        die("아티클 안에 다른 <article>이 들어 있습니다 — 태그가 이미 깨진 상태, 먼저 고쳐야 합니다.")

    line = '    <p class="small">📌 <strong>%s</strong> · %s</p>\n' % (a.date, note)
    if '<div class="sec followups">' in art:
        fs = art.index('<div class="sec followups">')
        close = art.rfind("</div>")
        if close < fs:
            die("후속 기록 섹션의 닫는 </div>를 찾지 못했습니다")
        at = art.rfind("\n", 0, close) + 1  # 닫는 </div> 줄의 맨 앞(들여쓰기 보존)
        new_art = art[:at] + line + art[at:]
    else:
        body = art.rstrip()
        new_art = body + "\n  " + SEC_OPEN + line + "  </div>\n"

    if not a.keep_date:
        new_art, n = re.subn(r'(<span class="db">)\d{4}-\d{2}-\d{2}(</span>)', r"\g<1>%s\g<2>" % a.date, new_art, count=1)

    out = html[:s] + new_art + html[e:]
    if count_articles(out) != before:
        die("아티클 수가 바뀌었습니다(%d → %d) — 중단" % (before, count_articles(out)))
    if len(re.findall(r'\bid="%s"' % re.escape(a.id), out)) != 1:
        die("대상 id가 1개가 아닙니다 — 중단")

    print("➕ #%s  %s" % (a.id, line.strip()))
    if a.dry_run:
        print("(dry-run — 파일은 그대로)")
        return
    shutil.copyfile(ARCHIVE, ARCHIVE + ".prev")
    tmp = ARCHIVE + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="").write(out)
    os.replace(tmp, ARCHIVE)
    print("✅ 저장 (백업 archive.html.prev) · 아티클 수 %d 그대로" % before)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
