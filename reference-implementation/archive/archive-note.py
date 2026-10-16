# -*- coding: utf-8 -*-
"""archive-note.py — 마크다운 정본(articles/*/{id}.md)에 「날짜 + 후속 한 줄」을 추가하고 거울을 빌드한다.

SSOT 아키텍처 (2026-10-15 개편):
  - archive.html 을 직접 수정하지 않고, articles/*/{id}.md 를 찾아 후속 기록을 추가한다.
  - Frontmatter 의 date 값을 갱신(--keep-date 가 아닐 때)한다.
  - 변경 후 build_archive.py 를 자동 실행하여 archive.html 과 archive-structure.md 거울을 동기화한다.

사용:
  python archive-note.py --id man-server-ownership --note "담당 확정 — 차세대ERP팀 장지현 매니저"
  python archive-note.py --id ts-crdr-posnr-untraceable --note "<strong>원인 확정</strong>: …" --dry-run
"""
import argparse
import datetime
import glob
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(ROOT, "articles")
BUILD_SCRIPT = os.path.join(ROOT, "build_archive.py")

INLINE = ("strong", "b", "em", "i", "a", "code", "span", "small", "u", "mark")
SEC_OPEN = '  <div class="sec followups">\n    <div class="st">📌 후속 기록</div>\n'


def die(msg):
    print("❌ " + msg)
    sys.exit(1)


def check_inline(note):
    for t in INLINE:
        o = len(re.findall(r"<%s(\s[^>]*)?>" % t, note))
        c = len(re.findall(r"</%s>" % t, note))
        if o != c:
            die("내용의 <%s> 태그 짝이 안 맞습니다(열림 %d · 닫힘 %d) — 닫지 않은 태그는 레이아웃을 깨뜨립니다." % (t, o, c))
    if re.search(r"</?(article|div|section|script|style)\b", note, re.I):
        die("내용에 블록 태그(article·div·section·script·style)는 넣을 수 없습니다 — 인라인 태그만.")


def find_article_file(aid):
    pattern = os.path.join(ARTICLES_DIR, "*", f"{aid}.md")
    matches = glob.glob(pattern)
    if not matches:
        die(f'id="{aid}" 아티클 파일을 찾지 못했습니다 (검색 경로: articles/*/{aid}.md).')
    if len(matches) > 1:
        die(f'id="{aid}" 아티클 파일이 {len(matches)}개 발견되었습니다: ' + ", ".join(matches))
    return matches[0]


def main():
    ap = argparse.ArgumentParser(description="아카이브 마크다운 정본에 날짜별 후속 한 줄 추가")
    ap.add_argument("--id", required=True, help="아티클 id (예: man-server-ownership)")
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

    target_file = find_article_file(a.id)
    with open(target_file, "r", encoding="utf-8") as f:
        text = f.read()

    m = re.match(r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$', text)
    if not m:
        die(f"Frontmatter 형식이 올바르지 않습니다: {target_file}")

    fm_text = m.group(1)
    body = m.group(2)

    line = '    <p class="small">📌 <strong>%s</strong> · %s</p>\n' % (a.date, note)

    if '<div class="sec followups">' in body:
        fs = body.index('<div class="sec followups">')
        close = body.rfind("</div>")
        if close < fs:
            die("후속 기록 섹션의 닫는 </div>를 찾지 못했습니다")
        at = body.rfind("\n", 0, close) + 1  # 닫는 </div> 줄 앞
        new_body = body[:at] + line + body[at:]
    else:
        new_body = body.rstrip() + "\n\n" + SEC_OPEN + line + "  </div>\n"

    new_fm_text = fm_text
    if not a.keep_date:
        new_fm_text = re.sub(r'date:\s*("[^"]*"|\'[^\']*\'|\S+)', f'date: "{a.date}"', new_fm_text, count=1)
        # Also update nav_desc if it is a date
        new_fm_text = re.sub(r'nav_desc:\s*"\d{4}-\d{2}-\d{2}"', f'nav_desc: "{a.date}"', new_fm_text, count=1)

    new_content = f"---\n{new_fm_text}\n---\n\n{new_body.strip()}\n"

    print("➕ #%s  %s" % (a.id, line.strip()))
    rel_path = os.path.relpath(target_file, ROOT)
    print(f"📄 정본 파일: {rel_path}")

    if a.dry_run:
        print("(dry-run — 파일은 그대로)")
        return

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ 정본 저장 완료: {rel_path}")
    print("🔄 거울 컴파일러(build_archive.py) 자동 실행 중...")

    r = subprocess.run([sys.executable, BUILD_SCRIPT], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        die("build_archive.py 실행 실패")

    print("✅ 거울(archive.html, archive-structure.md) 최신화 완료")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
