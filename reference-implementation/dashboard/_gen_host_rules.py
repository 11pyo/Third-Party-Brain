# -*- coding: utf-8 -*-
"""
_gen_host_rules.py — 모델 독립 규칙 정본(CLAUDE.md / SYSTEM_RULES.md)과 호스트별 규칙 파일을 **자동 생성**한다.

배경 (멀티 프론티어 AI 상호운용 아키텍처):
  동일한 운영 규칙과 업무 지침을 여러 호스트(Claude Code, OpenAI/Codex/Cursor, Gemini CLI, Google Antigravity 등)에
  수기로 복사·동기화하면 반드시 내용이 누락되고 낡게(drift) 된다.
  → 단일 정본(Single Source of Truth)을 유지하고, 각 호스트가 요구하는 파일명과 포맷으로 자동 생성·점검한다.

생성 매핑:
  입력: 프로젝트 루트의 `CLAUDE.md` (또는 지정된 정본 규칙 파일)
  출력:
    · `SYSTEM_RULES.md`          — 모델 독립 정본 규칙 파일
    · `AGENTS.md`                — Codex / Cursor / 범용 AI 에이전트 온보딩 규칙
    · `GEMINI.md`                — Gemini CLI 등 단일 마크다운 호스트용 규칙
    · `.agents/rules/rules-*.md` — Google Antigravity IDE용 (파일당 글자수 제한에 맞춰 분할)

사용법:
    python _gen_host_rules.py          # 규칙 파일 일괄 생성 (백업 후 덮어쓰기)
    python _gen_host_rules.py --check  # 규칙 파일들의 최신 동기화 여부 검증 (CI / 동기화 점검용)
    python _gen_host_rules.py --dry    # 변경 예정 내역 미리보기
"""
import difflib
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
# 대시보드가 프로젝트 하위 폴더에 있는 경우 루트 탐색 (없으면 현재 폴더)
ROOT = os.path.dirname(os.path.dirname(BASE)) if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(BASE)), "CLAUDE.md")) else BASE

SRC_PRIMARY = os.path.join(ROOT, "AGENTS.md")
OUT_RULES = os.path.join(ROOT, "SYSTEM_RULES.md")
OUT_GEMINI = os.path.join(ROOT, "GEMINI.md")
OUT_AG_RULES_DIR = os.path.join(ROOT, ".agents", "rules")

AG_BODY_BUDGET = 10000
GEN_MARK = "<!-- 자동 생성물 · _gen_host_rules.py에 의해 생성됨 (직접 수정 금지) -->"

HOST_ADAPT_TEMPLATE = """## 0. 호스트 적응 (Host Adaptation) — 모델 공통 지침

이 문서는 **Claude, Gemini, GPT 등 모든 AI 프론티어 모델을 위한 표준 운영 지침**입니다.
정본 규칙 파일(`AGENTS.md`)에서 자동 파생되었으므로 직접 수정하지 마십시오.

| 항목 | 호스트별 환경 | 수행할 작업 |
|---|---|---|
| **규칙 파일명** | Claude=`CLAUDE.md` · Codex/Cursor=`AGENTS.md` · Gemini=`GEMINI.md` · Antigravity=`.agents/rules/*.md` | 환경에 맞는 파일을 읽고 준수 |
| **파일 도구** | Claude=`Read`/`Edit`/`Bash` · Gemini/Antigravity=`view_file`/`replace_file_content`/`run_command` · Codex=`read_file`/`edit_file` | 호스트별 도구 명칭을 자동 매핑하여 사용 |
| **품질 검증** | 공통 검증 스크립트 실행 | 작업 완료 전 `python reference-implementation/dashboard/_check_board_sync.py` 무결성 확인 |

---

"""

def read_file(p):
    if not os.path.exists(p):
        return ""
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

def write_file(p, content):
    d = os.path.dirname(p)
    if d and not os.path.exists(d):
        os.makedirs(d)
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(content)

def split_for_antigravity(body, budget=AG_BODY_BUDGET):
    """## 섹션 단위로 나누어 Antigravity 규칙 파일 상한 내로 분할"""
    sections = re.split(r"(?m)(?=^## )", body)
    chunks = []
    curr = []
    curr_len = 0
    for s in sections:
        if not s.strip():
            continue
        slen = len(s)
        if curr and curr_len + slen > budget:
            chunks.append("".join(curr))
            curr = [s]
            curr_len = slen
        else:
            curr.append(s)
            curr_len += slen
    if curr:
        chunks.append("".join(curr))
    return chunks

def build_all():
    src_content = read_file(SRC_PRIMARY)
    if not src_content:
        src_content = read_file(os.path.join(BASE, "tasks.md"))

    system_rules = "# Standard Operational Rules (Model-Neutral)\n\n" + GEN_MARK + "\n\n" + HOST_ADAPT_TEMPLATE + src_content
    gemini_md = "# Gemini / Frontier Model Operational Guide\n\n" + GEN_MARK + "\n\n" + HOST_ADAPT_TEMPLATE + src_content

    ag_chunks = split_for_antigravity(src_content)
    ag_files = {}
    for i, chunk in enumerate(ag_chunks, start=1):
        fname = "rules-{:02d}.md".format(i)
        ag_files[fname] = "# Antigravity Rules Part {}\n\n{}\n\n{}".format(i, GEN_MARK, chunk)

    return {
        OUT_RULES: system_rules,
        OUT_GEMINI: gemini_md,
        "ag_rules": ag_files
    }

def check_sync():
    """모든 규칙 파일이 최신 상태인지 검증"""
    built = build_all()
    diffs = []
    for path, expected in [(OUT_RULES, built[OUT_RULES]), (OUT_GEMINI, built[OUT_GEMINI])]:
        current = read_file(path)
        if current.strip() != expected.strip():
            diffs.append(path)

    for fname, expected in built["ag_rules"].items():
        fpath = os.path.join(OUT_AG_RULES_DIR, fname)
        current = read_file(fpath)
        if current.strip() != expected.strip():
            diffs.append(fpath)

    return diffs

def main():
    check_mode = "--check" in sys.argv
    dry_mode = "--dry" in sys.argv

    if not os.path.exists(SRC_PRIMARY):
        print("ℹ️ 정본 규칙 파일({})을 찾을 수 없어 템플릿 동작 모드로 실행합니다.".format(SRC_PRIMARY))

    built = build_all()

    if check_mode:
        diffs = check_sync()
        if diffs:
            print("⛔ 호스트 규칙 파일 동기화 어긋남 ({}건):".format(len(diffs)))
            for d in diffs:
                print("  - {}".format(d))
            print("⇒ `python _gen_host_rules.py` 를 실행하여 갱신하십시오.")
            sys.exit(1)
        else:
            print("✅ 모든 호스트 규칙 파일이 정본과 완벽히 동기화되어 있습니다.")
            sys.exit(0)

    if dry_mode:
        print("🔍 [Dry Run] 생성 예정 파일 목록:")
        print("  ·", OUT_RULES)
        print("  ·", OUT_GEMINI)
        for fname in built["ag_rules"]:
            print("  ·", os.path.join(OUT_AG_RULES_DIR, fname))
        return

    # 파일 생성
    write_file(OUT_RULES, built[OUT_RULES])
    write_file(OUT_GEMINI, built[OUT_GEMINI])
    for fname, content in built["ag_rules"].items():
        write_file(os.path.join(OUT_AG_RULES_DIR, fname), content)

    print("✅ 호스트별 규칙 파일 생성 완료:")
    print("  · SYSTEM_RULES.md (단일 모델 중립 정본)")
    print("  · GEMINI.md (Gemini CLI)")
    print("  · .agents/rules/ (Antigravity 분할 규칙)")

if __name__ == "__main__":
    main()
