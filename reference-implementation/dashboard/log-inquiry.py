# -*- coding: utf-8 -*-
"""
log-inquiry.py — 일반·단순·긴급 문의를 대시보드 로그(inquiry-log.js)에 기록.
append-only(push 한 줄) + id 병합 → 여러 세션 동시 기록해도 충돌 없음.
상태: 접수 → 진행중 → 대기 → 완료 (대시보드 4열 보드로 표시, 완료열은 스크롤).

① 접수(문의 들어옴): '접수'로 박음 → 보드 접수열 맨 위
   python log-inquiry.py --new --type 단순문의 --q "문의 요약" --by 담당자 [--date 2026-06-04]
   → stdout 'NEW id=INQ...' 의 id 를 기억할 것.

② 상태 전이 / 채우기 (같은 id):
   python log-inquiry.py --id INQ123 --status 진행중
   python log-inquiry.py --id INQ123 --status 대기
   python log-inquiry.py --done --id INQ123 --a "처리·답변 요약" --ref "#some-article"   # =완료

※ 접수와 동시에 답이 끝났으면 ①에서 --a(또는 --status 완료)까지 주면 바로 완료.
type 예: 단순문의 | 일반요청 | 긴급문의   /   status: 접수 | 진행중 | 대기 | 완료
"""
import argparse, json, sys, io, os, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inquiry-log.js")
VALID = ("접수", "진행중", "대기", "완료")

def ensure():
    if not os.path.exists(LOG):
        with open(LOG, "w", encoding="utf-8") as f:
            f.write("window.INQUIRY_LOG = window.INQUIRY_LOG || [];\n")

def _lock(lf):
    # 짧은 OS 락: 동시에 두 세션이 같은 EOF에 써서 한 줄이 사라지는 것 방지.
    # Windows의 평범한 append("a")는 원자적이지 않음(lseek→write 경쟁). best-effort.
    try:
        if os.name == "nt":
            import msvcrt
            lf.seek(0); msvcrt.locking(lf.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lf, fcntl.LOCK_EX)
    except Exception:
        pass

def _unlock(lf):
    try:
        if os.name == "nt":
            import msvcrt
            lf.seek(0); msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lf, fcntl.LOCK_UN)
    except Exception:
        pass

def append(obj):
    ensure()
    line = "window.INQUIRY_LOG.push(" + json.dumps(obj, ensure_ascii=False) + ");\n"
    lockpath = LOG + ".lock"
    try:
        with open(lockpath, "a+") as lf:        # 락 게이트(내용 무관)
            _lock(lf)
            try:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(line)               # 락 보유 중 원자적 append
            finally:
                _unlock(lf)
    except Exception:
        with open(LOG, "a", encoding="utf-8") as f:   # 락 자체 실패 시에도 기록은 유지
            f.write(line)

ap = argparse.ArgumentParser()
ap.add_argument("--new",  action="store_true", help="접수: 새 문의 기록")
ap.add_argument("--done", action="store_true", help="완료 처리(=--status 완료)")
ap.add_argument("--id",   default="", help="전이/채우기 대상 id (--new 출력값)")
ap.add_argument("--status", default="", help="접수|진행중|대기|완료")
ap.add_argument("--date", default="", help="YYYY-MM-DD (오늘)")
ap.add_argument("--type", default="", help="단순문의|일반요청|긴급문의")
ap.add_argument("--q",    default="", help="문의 요약")
ap.add_argument("--a",    default="", help="처리/답변 요약")
ap.add_argument("--by",   default="", help="기록 담당자(보통 담당자)")
ap.add_argument("--ref",  default="", help="archive 앵커(선택, 예 #some-article)")
ap.add_argument("--req",  default="", help="요청자·조직 (카드 코드 옆 칩으로 표시, 예: 요청자·영업·샘플)")
x = ap.parse_args()

if x.status and x.status not in VALID:
    sys.exit("[오류] --status 는 " + "|".join(VALID))

if x.new:
    iid = x.id or ("INQ-" + time.strftime("%y%m%d-%H%M%S"))   # 예: INQ-260604-143022 (읽기 좋은 고유코드)
    status = x.status or ("완료" if x.a else "접수")
    obj = {"id": iid, "date": x.date, "type": (x.type or "단순문의"), "q": x.q,
           "by": x.by, "req": x.req, "a": x.a, "ref": x.ref, "status": status}
    append(obj)
    print("NEW id=" + iid + " status=" + status)
elif x.id:
    obj = {"id": x.id}
    if x.done:
        obj["status"] = "완료"
    elif x.status:
        obj["status"] = x.status
    for k in ("a", "ref", "q", "by", "req", "date", "type"):   # 준 값만 갱신(빈값 무시)
        v = getattr(x, k)
        if v:
            obj[k] = v
    if len(obj) == 1:
        sys.exit("[오류] --id 만으로는 변경할 게 없음 (--status/--done/--a/--ref 등 필요)")
    append(obj)
    print("UPDATE id=" + x.id + (" status=" + obj["status"] if "status" in obj else ""))
else:
    sys.exit("[오류] --new (접수) 또는 --id (전이/완료) 를 지정")
