# -*- coding: utf-8 -*-
"""
tasks-index.md 생성기 — 세션 착수용 경량 인덱스.

배경(2026-08-25 AI 규칙 총점검 B2):
  tasks.md가 65만자(디스크 1.19MB)로 자라 "세션 착수 시 tasks.md를 먼저 읽어라"는
  CLAUDE.md 규칙이 물리적으로 실행 불가능해졌다. 한 컨텍스트에 안 들어간다.
  → 살아있는 카드 + 카드별 '라인 범위'만 담은 인덱스를 만들어, 세션은 인덱스만 읽고
    필요한 카드만 tasks.md의 해당 구간을 부분 읽기 하도록 한다.

인덱스는 손으로 고치지 말 것 — tasks.md를 고친 뒤 이 스크립트를 재실행한다.
    python task-dashboard/_gen_tasks_index.py
"""
import datetime
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "tasks.md")
OUT = os.path.join(BASE, "tasks-index.md")

CARD_RE = re.compile(r"^#\s+((?:DEV|OPS|TS|ADM)-\d{3})\s*(.*)$")
DONE_MARKS = ("완료", "종결")
DROP_MARKS = ("취소", "철회", "보류폐기")
LIVE_ORDER = {"진행중": 0, "접수": 1, "대기": 2, "미정": 3}
MAXLEN = {"title": 70, "req": 34, "due": 30, "next": 130}


def norm_status(cell):
    """칸반 요약 표의 상태 셀 → 정규화 상태."""
    c = re.sub(r"[*`]", "", cell)
    if "정기" in c or any(k in c for k in ("주례", "월례", "연례")):
        return "정기"
    if any(m in c for m in DROP_MARKS):
        return "철회"
    for k in ("진행중", "접수", "대기"):
        if k in c:
            return k
    if any(m in c for m in DONE_MARKS):
        return "완료"
    return "미정"


def clean(cell, limit=None):
    """표 셀에서 강조·링크 기호를 걷어내 한 줄로. limit 지정 시 잘라낸다."""
    c = re.sub(r"[*`]", "", cell).strip()
    c = re.sub(r"\s+", " ", c).replace("|", "/")
    if limit and len(c) > limit:
        c = c[:limit].rstrip() + "…"
    return c


WAIT_HEAD = "| 대기 근거"
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def parse_wait(cell):
    """카드 요약표의 「대기 근거」 셀 → dict 또는 None.

    형식(CLAUDE.md 「📤 회신·응답 대기 표기」 규칙):
        | 대기 근거 | 📤 외부회신 — <무엇을 누구에게> · 발송 <미확인|미발송|YYYY-MM-DD>
                     · 회신기한 <YYYY-MM-DD> · 기한 경과 시 <조치> |

    ⚠️ 발송 상태의 기본값은 「미확인」이다 — 사용자가 직접 보내고 알려주지 않았을 수 있으므로
       AI 가 「미발송」으로 단정하지 않는다(2026-09-10 실제 사고가 계기).
    """
    c = re.sub(r"[*`]", "", cell).strip()
    if not c:
        return None
    what, sent, due, then = "", "미확인", "", ""
    # 구분자는 **앞뒤 공백이 있는 " · "** — 본문의 한국어 나열 점(예: 홍길동·영업지원팀)과 충돌하지 않게.
    seps = c.split(" · ") if " · " in c else c.split("·")
    for chunk in [x.strip() for x in seps]:
        if not chunk:
            continue
        if chunk.startswith("발송"):
            sent = chunk[2:].strip() or "미확인"
        elif "경과" in chunk:                      # 「기한 경과 시 …」 — 회신기한보다 먼저 판별
            then = chunk.split("시", 1)[-1].strip(" :") or chunk
        elif chunk.startswith("회신기한") or chunk.startswith("기한"):
            due = chunk.split(None, 1)[-1].strip() if " " in chunk else chunk[4:].strip()
        elif not what:
            what = chunk
    m = DATE_RE.search(due)
    duedate = None
    if m:
        try:
            duedate = datetime.date(*[int(x) for x in m.group(1).split("-")])
        except ValueError:
            duedate = None
    if len(what) > 90:
        what = what[:90].rstrip() + "…"
    return {"what": what, "sent": sent, "due": due or "미지정",
            "duedate": duedate, "then": then}


def collect_waits(lines, spans, live):
    """살아있는 카드의 라인 구간에서 「대기 근거」 행을 긁어온다."""
    out = []
    for cid in live:
        sp = spans[cid]
        for ln in lines[sp["start"] - 1:sp["end"]]:
            st = ln.strip()
            if st.startswith(WAIT_HEAD):
                cells = [x for x in st.split("|")]
                if len(cells) >= 3:
                    w = parse_wait(cells[2])
                    if w:
                        w["id"] = cid
                        out.append(w)
                break
    return out


def load_board_meta():
    """task-board.html 의 `const TASKS = [...]` 를 읽어 {id: 카드} 로 돌려준다.

    파싱 로직은 `_check_board_sync.py` 와 공유한다(중복 구현 금지).
    보드 파일이 없거나 깨졌으면 빈 dict — 그 경우 칸반 요약 표만으로 인덱스를 만든다.
    """
    try:
        sys.path.insert(0, BASE)
        import _check_board_sync as chk
        import json as _json

        b = io.open(os.path.join(BASE, "task-board.html"), encoding="utf-8").read()
        m = chk.DECL_RE.search(b)
        if not m:
            return {}
        raw = chk.slice_array(b, b.index("[", m.start()))
        return {t["id"]: t for t in _json.loads(raw, strict=False) if t.get("id")}
    except Exception as e:
        print("⚠️ 보드 TASKS 배열을 읽지 못해 칸반 요약 표만 사용합니다: {}".format(e))
        return {}


def main():
    if not os.path.exists(SRC):
        sys.exit("tasks.md 를 찾을 수 없습니다: " + SRC)

    lines = io.open(SRC, encoding="utf-8").read().split("\n")

    # ① 카드 H1 위치 수집 → 라인 범위 산출
    starts = []
    for i, line in enumerate(lines, start=1):
        m = CARD_RE.match(line)
        if m:
            starts.append((m.group(1), m.group(2).strip(), i))
    if not starts:
        sys.exit("카드 헤딩(# DEV-001 …)을 찾지 못했습니다. tasks.md 형식이 바뀌었는지 확인하세요.")

    spans = {}
    for idx, (cid, title, start) in enumerate(starts):
        end = starts[idx + 1][2] - 1 if idx + 1 < len(starts) else len(lines)
        spans[cid] = {"title": title, "start": start, "end": end}

    # ② 카드 메타(상태·요청자·기한·다음액션) 수집
    #
    #    출처 = **보드 `TASKS` 배열 단일 출처**.
    #    2026-08-25 이전엔 tasks.md 상단 「📊 한눈에 보기」 칸반 요약 표도 같은 데이터를 들고 있었으나,
    #    세 벌(카드 본문 / 요약 표 / 보드 배열) 중 그 표가 가장 잘 낡는 것이 실측돼 표를 걷어냈다.
    #    이제 이 생성기는 보드만 읽고, 보드에 없는 카드는 아래에서 경고로 띄운다.
    meta = {}
    for cid, t in load_board_meta().items():
        meta[cid] = {
            "kind": clean(t.get("cls") or "", 20),
            "title": clean(t.get("title") or "", MAXLEN["title"]),
            "status": norm_status(t.get("status") or ""),
            "req": clean(t.get("req") or "", MAXLEN["req"]),
            "due": clean(t.get("due") or "", MAXLEN["due"]),
            "next": clean(t.get("next") or "", MAXLEN["next"]),
        }

    live, recur, done, unlisted = [], [], [], []
    for cid in sorted(spans):
        m = meta.get(cid)
        if m is None:
            unlisted.append(cid)
        elif m["status"] == "정기":
            recur.append(cid)
        elif m["status"] in ("완료", "철회"):
            done.append(cid)
        else:
            live.append(cid)

    live.sort(key=lambda c: (LIVE_ORDER.get(meta[c]["status"], 9), c))

    src_chars = sum(len(l) for l in lines)
    o = []
    o.append("# SD 운영 Task — 세션 착수 인덱스")
    o.append("")
    o.append("> ⚠️ **이 파일은 자동 생성물이다. 손으로 고치지 말 것.**")
    o.append("> 정본 = `tasks.md`. 정본을 고친 뒤 `python task-dashboard/_gen_tasks_index.py` 를 재실행한다.")
    o.append("")
    o.append("**읽는 법 (세션 착수 순서)**")
    o.append("1. 이 인덱스로 지금 살아있는 카드를 파악한다.")
    o.append("2. 손댈 카드가 정해지면 **그 카드의 라인 범위만** `tasks.md`에서 읽는다 "
             "— 예: `sed -n '106,164p' task-dashboard/tasks.md`")
    o.append("3. 카드 작업 시 **본문 + `### 🤖 AI 참조 로그`를 둘 다** 읽는다(로그에 기확정 산식·방침·함정이 있다).")
    o.append("")
    o.append(f"- 카드 {len(spans)}장 — 살아있음 {len(live)} / 정기 {len(recur)} / 종료 {len(done)}"
             + (f" / ⚠️보드누락 {len(unlisted)}" if unlisted else "")
             + f" · `tasks.md` {src_chars:,}자 / {len(lines):,}줄")
    o.append("")
    o.append("---")
    o.append("")
    o.append("## 🔥 지금 살아있는 카드")
    o.append("")
    if live:
        o.append("| ID | 제목 | 상태 | 요청자 | 기한 | 다음 액션 | tasks.md 라인 |")
        o.append("|---|---|---|---|---|---|---|")
        for cid in live:
            m = meta[cid]
            s = spans[cid]
            o.append("| **{id}** | {t} | {st} | {rq} | {du} | {nx} | L{a}–{b} ({n}줄) |".format(
                id=cid, t=m["title"], st=m["status"], rq=m["req"], du=m["due"],
                nx=m["next"], a=s["start"], b=s["end"], n=s["end"] - s["start"] + 1))
    else:
        o.append("_없음 — 살아있는 카드가 하나도 없습니다._")
    o.append("")
    waits = collect_waits(lines, spans, live)
    today = datetime.date.today()
    o.append("## 📤 회신·응답 대기 — ⏰ **오늘 날짜로 기한을 직접 판정할 것**")
    o.append("")
    if waits:
        o.append("> 이 표는 인덱스를 만든 날(**{}**) 기준이다. **오늘 날짜와 「회신기한」을 비교**해 "
                 "지난 건이 있으면 그 세션에서 사용자에게 **발송·회신 여부를 한 번 묻는다**.".format(today.isoformat()))
        o.append("> ⚠️ 사용자가 직접 보내고 알려주지 않았을 수 있으므로 **「미발송」으로 단정하지 말 것** "
                 "— 물어서 확인된 사실만 카드에 적는다(2026-09-10 실제 사고가 계기).")
        o.append("")
        o.append("| ID | 기다리는 것 | 발송 | 회신기한 | 기한 경과 시 |")
        o.append("|---|---|---|---|---|")
        for w in sorted(waits, key=lambda x: (x["duedate"] or datetime.date.max, x["id"])):
            over = ""
            if w["duedate"]:
                d = (today - w["duedate"]).days
                if d > 0:
                    over = " ⏰**{}일 경과**".format(d)
            o.append("| **{id}** | {what} | {sent} | {due}{ov} | {then} |".format(
                id=w["id"], what=w["what"] or "—", sent=w["sent"],
                due=w["due"], ov=over, then=w["then"] or "—"))
    else:
        o.append("_없음 — 외부 회신·응답을 기다리는 카드가 없습니다._")
    o.append("")
    o.append("## 🔁 정기 카드 (트리거가 오면 실행)")
    o.append("")
    if recur:
        o.append("| ID | 제목 | 주기·트리거 | 다음 액션 | tasks.md 라인 |")
        o.append("|---|---|---|---|---|")
        for cid in recur:
            m, sp = meta[cid], spans[cid]
            o.append("| **{id}** | {t} | {du} | {nx} | L{a}–{b} |".format(
                id=cid, t=m["title"], du=m["due"], nx=m["next"], a=sp["start"], b=sp["end"]))
    else:
        o.append("_없음_")
    o.append("")
    o.append("## ✅ 종료 카드 (완료·철회 — 참조용 색인)")
    o.append("")
    o.append("필요할 때만 해당 라인 구간을 읽는다.")
    o.append("")
    for cid in done:
        sp = spans[cid]
        mark = "❌철회 " if meta[cid]["status"] == "철회" else ""
        o.append("- {mk}**{id}** — {t} · L{a}–{b}".format(
            mk=mark, id=cid, t=meta[cid]["title"], a=sp["start"], b=sp["end"]))
    if unlisted:
        o.append("")
        o.append("## ⚠️ 보드에 없는 카드")
        o.append("")
        o.append("아래 카드는 `tasks.md` 본문에는 있으나 `task-board.html` 의 `TASKS` 배열에 없다 "
                 "— 보드 화면에 안 뜨고 메타(상태·기한)도 없다. 배열에 추가할 것.")
        o.append("")
        for cid in unlisted:
            s = spans[cid]
            o.append("- **{id}** — {t} · L{a}–{b}".format(
                id=cid, t=spans[cid]["title"], a=s["start"], b=s["end"]))
    o.append("")

    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(o))
    over_n = len([w for w in waits if w["duedate"] and w["duedate"] < today])
    print("생성 완료: {}".format(OUT))
    if over_n:
        print("  ⏰ 회신기한 경과 {}건 — 인덱스 「📤 회신·응답 대기」 확인".format(over_n))
    print("  카드 {}장 (살아있음 {} / 정기 {} / 종료 {} / 보드누락 {})".format(
        len(spans), len(live), len(recur), len(done), len(unlisted)))
    print("  tasks.md {:,}자 → 인덱스 {:,}자".format(src_chars, sum(len(x) for x in o)))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
