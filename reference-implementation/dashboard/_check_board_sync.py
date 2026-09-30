# -*- coding: utf-8 -*-
"""
tasks.md  <->  task-board.html(TASKS 배열)  동기화 점검기.

배경(2026-08-25 AI 규칙 총점검 B3):
  카드를 tasks.md 와 task-board.html 의 `const TASKS=[...]` 양쪽에 수기로 이중 입력하는
  구조라, 한쪽만 갱신하는 드리프트가 반복됐다(카드 여러 장이 보드에서 누락된 전례).
  메모리 규칙만으로 막아 왔으나 규칙은 잊히므로, "조용한 어긋남"을 "시끄러운 실패"로 바꾼다.

  같은 날 개편: 중복본이던 tasks.md 상단 「📊 한눈에 보기」 칸반 요약 표를 걷어내 **두 벌**로 줄였다.
    - tasks.md 카드 본문 = 서사·확정사항·AI 로그의 **정본**
    - 보드 TASKS 배열    = 상태·요청자·기한·다음액션 등 구조화 메타의 **단일 출처**
  이 점검기는 둘의 **카드 집합이 일치하는지**를 본다(+ 카드 본문에 `| 상태 |` 행이 있으면 그것도 대조).

  ⚠️ 이 스크립트는 고치지 않는다. 어긋난 곳을 찾아 보고만 한다(무엇이 사실인지는 사람/AI 판단).

사용:
    python task-dashboard/_check_board_sync.py
    → 어긋남이 있으면 종료코드 1 (카드 추가·수정 작업 끝에 항상 한 번 돌릴 것)
"""
import difflib
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
TASKS_MD = os.path.join(BASE, "tasks.md")
BOARD = os.path.join(BASE, "task-board.html")
INDEX_MD = os.path.join(BASE, "tasks-index.md")

# 인덱스 머리말의 "`tasks.md` 761,826자 / 2,641줄" 을 읽기 위한 패턴
INDEX_SIZE_RE = re.compile(r"`tasks\.md`\s*([\d,]+)\s*자\s*/\s*([\d,]+)\s*줄")
MTIME_SLACK = 2  # 초. 파일시스템 타임스탬프 오차 허용

CARD_RE = re.compile(r"^#\s+((?:DEV|OPS|TS|ADM)-\d{3})\s*(.*)$")
STATUS_ROW_RE = re.compile(r"^\|\s*상태\s*\|")
OBJ_RE = re.compile(r"\{\s*id\s*:")
DECL_RE = re.compile(r"const\s+TASKS\s*=\s*\[")
BACKSLASH = chr(92)
NL = chr(10)
# JS 문자열 값: "..." 안에서 역슬래시 이스케이프 허용
VAL_TMPL = r'{name}\s*:\s*"((?:[^"{bs}]|{bs}.)*)"'


def js_field(chunk, name):
    """TASKS 배열 객체 조각에서 문자열 필드 하나를 꺼낸다(정규식 폴백 경로 전용)."""
    pat = VAL_TMPL.format(name=name, bs=BACKSLASH + BACKSLASH)
    m = re.search(pat, chunk)
    if not m:
        return ""
    try:
        return json.loads('"' + m.group(1) + '"')
    except ValueError:
        return m.group(1)


def norm_status(cell):
    c = re.sub(r"[*`~]", "", cell)
    if "정기" in c or any(k in c for k in ("주례", "월례", "연례")):
        return "정기"
    if any(k in c for k in ("취소", "철회")):
        return "철회"
    for k in ("진행중", "접수", "대기", "신규"):
        if k in c:
            return k
    if any(k in c for k in ("완료", "종결")):
        return "완료"
    return "미정"


def norm_title(t):
    """제목 비교용 정규화 — 한글·영숫자만 남긴다.

    tasks.md 의 H1 은 `# DEV-003 🟦 제목` 처럼 분류 아이콘이 붙고 보드 title 에는 없다.
    이모지·공백·강조·괄호 등을 통째로 걷어내야 같은 카드가 '제목 다름'으로 잘못 뜨지 않는다.
    """
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", t or "").lower()


def load_tasks_md():
    """tasks.md 를 읽어 {카드ID: {title, line, status}} 로 돌려준다.

    status 는 카드 본문의 `| 상태 | … |` 행에서만 뽑는다. 그 행이 없는 카드는 None —
    결함이 아니다(상태의 단일 출처는 보드다).
    """
    lines = io.open(TASKS_MD, encoding="utf-8").read().split(NL)
    starts = []
    for i, line in enumerate(lines, start=1):
        m = CARD_RE.match(line)
        if m:
            starts.append((m.group(1), m.group(2).strip(), i))

    body = {}
    for idx, (cid, title, start) in enumerate(starts):
        end = starts[idx + 1][2] - 1 if idx + 1 < len(starts) else len(lines)
        status = None
        for line in lines[start:end]:
            if STATUS_ROW_RE.match(line):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 2:
                    status = norm_status(cells[1])
                break
        body[cid] = {"title": title, "line": start, "status": status}
    return body


def slice_array(text, open_at):
    """open_at 위치의 '[' 부터 짝이 맞는 ']' 까지 잘라낸다. 문자열 안의 괄호는 무시."""
    depth, i, n = 0, open_at, len(text)
    in_str = esc = False
    while i < n:
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == BACKSLASH:
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[open_at:i + 1]
        i += 1
    return None


def load_board():
    b = io.open(BOARD, encoding="utf-8").read()
    # ⚠️ 단순 find("const TASKS") 는 카드 ailog 본문에 적힌 "const TASKS 배열" 같은
    #    산문 언급에 먼저 걸린다(2026-08-25 실제로 걸렸음). 선언부 패턴으로 찾는다.
    m = DECL_RE.search(b)
    if not m:
        sys.exit("task-board.html 에서 `const TASKS = [` 선언을 찾지 못했습니다. 파일 구조를 확인하세요.")
    open_at = b.index("[", m.start())

    # 이 배열은 보드의 저장/내보내기가 JSON.stringify 로 써서 **정식 JSON**이다(키도 따옴표).
    # 우선 json 으로 읽고, 혹시 수기 편집으로 JS 문법(따옴표 없는 키)이 섞이면 정규식으로 폴백한다.
    raw = slice_array(b, open_at)
    out = {}
    if raw:
        try:
            for t in json.loads(raw, strict=False):
                cid = t.get("id", "")
                if re.match(r"^(?:DEV|OPS|TS|ADM)-\d{3}$", cid):
                    out[cid] = {
                        "title": t.get("title") or "",
                        "status": norm_status(t.get("status") or ""),
                        "detail_len": len(t.get("detail") or ""),
                        "ailog_len": len(t.get("ailog") or ""),
                    }
            return out
        except ValueError as e:
            print("⚠️ TASKS 배열 JSON 파싱 실패({}) → 정규식 폴백. "
                  "**보드가 깨져 있을 수 있으니 확인하세요.**".format(e))

    arr = b[m.start():]
    starts = [mm.start() for mm in OBJ_RE.finditer(arr)]
    for i, s0 in enumerate(starts):
        s1 = starts[i + 1] if i + 1 < len(starts) else len(arr)
        chunk = arr[s0:s1]
        cid = js_field(chunk, "id")
        if re.match(r"^(?:DEV|OPS|TS|ADM)-\d{3}$", cid or ""):
            out[cid] = {
                "title": js_field(chunk, "title"),
                "status": norm_status(js_field(chunk, "status")),
                "detail_len": len(js_field(chunk, "detail")),
                "ailog_len": len(js_field(chunk, "ailog")),
            }
    return out


def check_index_freshness():
    """세션 착수 인덱스(tasks-index.md)가 tasks.md 보다 낡았는지 본다.

    2026-09-01 AI 규칙 총점검(B2'): "카드를 고쳤으면 인덱스를 재생성한다"는 규칙이
    실제로 새어 나갔다(인덱스가 tasks.md 보다 22분 낡은 채 방치). 규칙 대신 도구로 잡는다.
    반환: 문제 문자열 리스트(없으면 빈 리스트).
    """
    fix = "  ⇒ `python task-dashboard/_gen_tasks_index.py` 재실행"
    if not os.path.exists(INDEX_MD):
        return ["[인덱스 없음] tasks-index.md 가 없다 — 세션 착수 인덱스가 비어 있는 상태." + fix]

    out = []
    try:
        if os.path.getmtime(INDEX_MD) + MTIME_SLACK < os.path.getmtime(TASKS_MD):
            out.append("[인덱스 낡음] tasks-index.md 가 tasks.md 보다 오래됐다 "
                       "(카드를 고친 뒤 인덱스를 재생성하지 않음)." + fix)
    except OSError:
        pass

    # 내용 기준 2차 확인 — mtime 만으로는 못 잡는 경우(복사·되돌리기 등)를 보완
    try:
        head = io.open(INDEX_MD, encoding="utf-8").read(4000)
        md = io.open(TASKS_MD, encoding="utf-8").read()
    except OSError:
        return out
    m = INDEX_SIZE_RE.search(head)
    if m:
        chars = int(m.group(1).replace(",", ""))
        lines = int(m.group(2).replace(",", ""))
        # ⚠️ _gen_tasks_index.py 와 **같은 정의**를 써야 한다:
        #    lines = read().split("\n") / src_chars = 개행 제외 글자수
        real_lines = md.count(NL) + 1
        real_chars = len(md) - md.count(NL)
        if (chars, lines) != (real_chars, real_lines):
            out.append("[인덱스 낡음] tasks-index.md 표기 {:,}자/{:,}줄 vs 실제 {:,}자/{:,}줄".format(
                chars, lines, real_chars, real_lines) + fix)
    return out


def main():
    body = load_tasks_md()
    board = load_board()
    problems, notes = [], []
    problems.extend(check_index_freshness())

    print("tasks.md 카드 {}장 · 보드 TASKS {}건".format(len(body), len(board)))
    print("-" * 66)

    for cid in sorted(set(body) - set(board)):
        problems.append(
            "[보드 누락] {} — tasks.md L{} 에 카드가 있으나 `TASKS` 배열에 없음 "
            "(보드에 안 뜨고 상태·기한 메타도 없음)".format(cid, body[cid]["line"]))
    for cid in sorted(set(board) - set(body)):
        problems.append(
            "[정본 누락] {} — `TASKS` 배열에 있으나 tasks.md 에 카드 본문이 없음 "
            "(정본에 서사가 없는 카드)".format(cid))

    for cid in sorted(set(body) & set(board)):
        ts, bs = body[cid]["status"], board[cid]["status"]
        if ts and ts != bs:
            # '정기'는 상태가 아니라 **반복성**이다. 정기 카드는 카드 본문이 "정기(월례)"라 적고
            # 보드는 그 순간의 상태("대기" 등)를 적는 게 정상이므로 불일치로 치지 않는다.
            if "정기" in (ts, bs):
                notes.append("[정기 카드 표기 차이] {} — 카드 본문 '{}' vs 보드 '{}' "
                             "(반복성 vs 현재 상태 — 정상)".format(cid, ts, bs))
            else:
                problems.append(
                    "[상태 불일치] {} — 카드 본문 '{}' vs 보드 '{}'  ⇒ 사실 확인 후 통일"
                    "(상태의 단일 출처는 보드)".format(cid, ts, bs))
        ratio = difflib.SequenceMatcher(
            None, norm_title(body[cid]["title"]), norm_title(board[cid]["title"])).ratio()
        if ratio < 0.7:
            notes.append("[제목 크게 다름 {:.0%}] {}".format(ratio, cid)
                         + NL + "      tasks.md: " + body[cid]["title"][:80]
                         + NL + "      보드    : " + board[cid]["title"][:80])

    empty_log = [cid for cid in sorted(board) if board[cid]["ailog_len"] == 0]
    if empty_log:
        notes.append("[AI로그 없음] 보드 카드 {}건의 ailog 가 빈 값: {}".format(
            len(empty_log), ", ".join(empty_log)))

    if notes:
        print("ℹ️ 참고 {}건 (실패로 치지 않음)".format(len(notes)))
        for n in notes:
            print("  · " + n)
        print()

    if not problems:
        print("✅ 반드시 맞춰야 할 어긋남 없음 — tasks.md 와 보드가 동기화돼 있습니다.")
        return 0

    print("⛔ 반드시 맞춰야 할 어긋남 {}건".format(len(problems)))
    for p in problems:
        print("  - " + p)
    print()
    print("※ 이 스크립트는 자동으로 고치지 않습니다. 위 항목을 직접 맞춘 뒤 다시 실행하세요.")
    return 1


def _host_rules_check():
    """호스트 규칙 파일(SYSTEM_RULES·AGENTS·GEMINI)이 정본 CLAUDE.md 와 어긋나지 않는지 함께 본다.

    2026-09-18 추가: 사람이 손으로 세 벌을 맞추던 구조라 실제로 최근 규칙 4개가 빠져 있었다.
    카드 작업 끝에 이미 돌리는 이 점검에 얹어, 기억이 아니라 도구가 집행하게 한다.
    """
    import subprocess
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_gen_host_rules.py")
    if not os.path.exists(gen):
        return 0
    r = subprocess.run([sys.executable, gen, "--check"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    if r.returncode:
        print()
        print(out)
    return r.returncode


def _archive_check():
    """archive.html ↔ archive-structure.md 구조 동기화(2026-09-29 · _check_archive_sync.py)."""
    import subprocess
    chk = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_check_archive_sync.py")
    if not os.path.exists(chk):
        return 0
    r = subprocess.run([sys.executable, chk], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    print()
    print((r.stdout or "").strip())
    return r.returncode


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rc = main()
    sys.exit(max(rc, _host_rules_check(), _archive_check()))
