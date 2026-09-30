# -*- coding: utf-8 -*-
"""
board-saver.py — 대시보드 「💾 저장」 전용 로컬 저장 서버 (127.0.0.1 전용)

목적: task-board.html 을 브라우저에서 수정하고 💾 저장을 누를 때
      「다른 이름으로 저장」 창 없이 **원본 파일을 그 자리에서 덮어쓰기**.
      (브라우저 File System Access API 는 보안 모델상 첫 저장·브라우저 재시작마다 사용자 승인이
       필요해 "묻지 않는 덮어쓰기"가 원천적으로 불가능하다. 그래서 로컬 서버가 대신 파일에 쓴다.)

실행:  python board-saver.py         (또는 프로젝트 루트의 6_대시보드_저장서버.bat)
종료:  Ctrl+C                        (또는 7_대시보드_저장서버_종료.bat)

⛔ 보안 — 이 서버는 파일을 덮어쓰는 쓰기 API 다.
   · 반드시 127.0.0.1 에만 바인딩한다. archive-server.py 의 --share(LAN 공개) 같은 옵션을 절대 만들지 말 것.
   · 요청 IP 가 127.0.0.1 이 아니면 거부. 커스텀 헤더(X-Board-Saver) 를 요구해 단순 POST 유입을 차단.
   · 쓰기 전 형식 검증 + 백업(.prev / _backups 일자별) + 원자적 교체(os.replace).

엔드포인트
  GET  /ping           → {"ok":true, ...}            (대시보드가 서버 가동 여부 탐지)
  POST /save/board     본문 = task-board.html 전문     → 검증·백업 후 그 자리 덮어쓰기
  POST /save/inquiry   본문 = window.INQUIRY_LOG.push(...) 줄들 → append-only 추가(log-inquiry.py 와 동일 규약)
"""
import io, json, os, shutil, sys, datetime, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HOST, PORT = "127.0.0.1", 5178          # ⛔ HOST 는 절대 0.0.0.0 으로 바꾸지 말 것
BASE       = os.path.dirname(os.path.abspath(__file__))
BOARD      = os.path.join(BASE, "task-board.html")
INQ        = os.path.join(BASE, "inquiry-log.js")
BACKUP_DIR = os.path.join(BASE, "_backups")
KEEP_DAILY = 7                          # 보드 일자별 스냅샷 보관 개수(1.7MB×N)
_wlock     = threading.Lock()           # 서버 내부 동시 쓰기 방지


def _log(msg):
    print(datetime.datetime.now().strftime("[%H:%M:%S] ") + msg, flush=True)


def _backup(path, daily_name):
    """쓰기 직전 스냅샷: 최근본(.prev) + 일자별 1회(_backups/). 실패해도 저장은 계속."""
    made = ""
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return made
        shutil.copyfile(path, path + ".prev")
        os.makedirs(BACKUP_DIR, exist_ok=True)
        daily = os.path.join(BACKUP_DIR, daily_name)
        if not os.path.exists(daily):
            shutil.copyfile(path, daily)
            made = os.path.basename(daily)
    except Exception as e:
        _log("[!] 백업 실패(저장은 진행): %s" % e)
    return made


def _prune_daily(prefix, suffix, keep):
    try:
        files = sorted(f for f in os.listdir(BACKUP_DIR)
                       if f.startswith(prefix) and f.endswith(suffix))
        if len(files) > keep:
            for f in files[:-keep]:
                os.remove(os.path.join(BACKUP_DIR, f))
    except Exception:
        pass


def _atomic_write(path, text):
    tmp = path + ".tmp-%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)                       # 같은 볼륨 → 원자적 교체


def save_board(text):
    """task-board.html 전체 덮어쓰기. 형식·크기 검증을 통과해야만 쓴다."""
    if "const TASKS = [" not in text or 'id="editbar"' not in text:
        return False, "보드 형식이 아닙니다(TASKS 배열/편집바 없음) — 저장 중단"
    if "</html>" not in text[-2000:]:
        return False, "문서 끝이 잘렸습니다(</html> 없음) — 저장 중단"
    n = len(text.encode("utf-8"))
    if n < 300000 or n > 30000000:
        return False, "크기가 비정상입니다(%d bytes) — 저장 중단" % n
    if os.path.exists(BOARD):
        old = os.path.getsize(BOARD)
        if old and n < old * 0.5:
            return False, "새 내용이 원본의 절반 이하(%d→%d) — 유실 의심으로 저장 중단" % (old, n)
    with _wlock:
        made = _backup(BOARD, "task-board.%s.html" % datetime.date.today().strftime("%Y%m%d"))
        _atomic_write(BOARD, text)
        _prune_daily("task-board.", ".html", KEEP_DAILY)
    return True, {"bytes": n, "backup": made}


def save_inquiry(text):
    """inquiry-log.js 에 push() 줄 추가(append-only). log-inquiry.py 와 같은 규약."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return False, "추가할 내용이 없습니다"
    if len(text) > 1000000:
        return False, "본문이 너무 큽니다 — 저장 중단"
    for l in lines:                                   # 한 줄이라도 규약 위반이면 전부 거부
        if not (l.startswith("window.INQUIRY_LOG.push(") and l.endswith(");")):
            return False, "허용되지 않는 줄이 있습니다(push 규약 위반) — 저장 중단"
        try:
            json.loads(l[len("window.INQUIRY_LOG.push("):-2])
        except Exception:
            return False, "push 인자가 올바른 JSON 이 아닙니다 — 저장 중단"
    with _wlock:
        if not os.path.exists(INQ):
            _atomic_write(INQ, "window.INQUIRY_LOG = window.INQUIRY_LOG || [];\n")
        cur = io.open(INQ, encoding="utf-8").read()
        if "window.INQUIRY_LOG" not in cur:
            return False, "inquiry-log.js 형식이 아닙니다 — 저장 중단"
        made = _backup(INQ, "inquiry-log.%s.js" % datetime.date.today().strftime("%Y%m%d"))
        with open(INQ, "a", encoding="utf-8", newline="") as f:   # 헬퍼와 동일한 append 방식
            f.write("\n".join(lines) + "\n")
    return True, {"lines": len(lines), "backup": made}


class Handler(BaseHTTPRequestHandler):
    server_version = "BoardSaver/1.0"

    def log_message(self, fmt, *args):
        pass                                     # 접근 로그는 _log 로 직접 찍는다

    def _send(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")               # file:// 은 Origin: null
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Board-Saver")
        self.send_header("Access-Control-Allow-Private-Network", "true")   # 크롬 PNA 프리플라이트 대비
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()
        self.wfile.write(data)

    def _guard(self):
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            self._send(403, {"ok": False, "err": "로컬 전용"})
            return False
        return True

    def do_OPTIONS(self):
        if self._guard():
            self._send(200, {"ok": True})

    def do_GET(self):
        if not self._guard():
            return
        if self.path.split("?")[0] == "/ping":
            self._send(200, {"ok": True, "board": BOARD, "inquiry": INQ, "version": 1})
        else:
            self._send(404, {"ok": False, "err": "no such path"})

    def do_POST(self):
        if not self._guard():
            return
        path = self.path.split("?")[0]
        if self.headers.get("X-Board-Saver") != "1":
            self._send(400, {"ok": False, "err": "헤더 누락 — 대시보드에서만 저장할 수 있습니다"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
        except Exception as e:
            self._send(400, {"ok": False, "err": "본문 수신 실패: %s" % e})
            return
        try:
            if path == "/save/board":
                ok, res = save_board(body)
                label = "task-board.html"
            elif path == "/save/inquiry":
                ok, res = save_inquiry(body)
                label = "inquiry-log.js"
            else:
                self._send(404, {"ok": False, "err": "no such path"})
                return
        except Exception as e:
            _log("[X] 저장 실패(%s): %s" % (path, e))
            self._send(500, {"ok": False, "err": str(e)})
            return
        if ok:
            _log("[OK] %s 저장됨 — %s" % (label, res))
            self._send(200, dict({"ok": True}, **res))
        else:
            _log("[거부] %s — %s" % (label, res))
            self._send(422, {"ok": False, "err": res})


def main():
    print("=" * 62)
    print("  대시보드 저장 서버 (task-board.html / inquiry-log.js)")
    print("  주소: http://%s:%d   (이 PC 전용 · LAN 공개 안 함)" % (HOST, PORT))
    print("  대상: %s" % BASE)
    print("  이 창이 켜져 있는 동안 대시보드의 💾 저장이 원본을 그 자리에서 덮어씁니다.")
    print("  종료: Ctrl+C  (또는 7_대시보드_저장서버_종료.bat)")
    print("=" * 62)
    try:
        srv = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        print("\n  [X] 포트 %d 를 열 수 없습니다: %s" % (PORT, e))
        print("      이미 저장 서버가 켜져 있을 수 있습니다(그러면 그대로 쓰면 됩니다).")
        return 1
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  종료합니다.")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
