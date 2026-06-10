# Reference implementation — Archive engine · 레퍼런스 구현 — 아카이브 엔진

> **EN** — A runnable, fully **anonymized** reference implementation of the "third brain"
> knowledge-archive engine described in `../../archive-blueprint/` (chapters 01–04). All data
> here is **fictional sample data**. This is the engine; bring your own `archive.html` content.
>
> **KO** — `../../archive-blueprint/`(01–04장)에서 설명하는 "제3의 뇌" 지식 아카이브 엔진의
> **실행 가능한 익명 레퍼런스 구현**입니다. 여기 데이터는 전부 **가짜 샘플**입니다. 엔진만 제공하니
> `archive.html` 내용은 본인 도메인으로 채우세요.

---

## What it does · 기능
- **AI search server** (`archive-server.py`) — serves `archive.html`, retrieves the most relevant
  sections with **BM25 (char-2gram)**, asks the local **Claude CLI**, and scrolls the page to the
  source. `--share` binds `0.0.0.0` for LAN.
- **Intake checker** (`archive-intake.py`) — before adding content, flags duplicates, **detects
  contradictions**, and recommends placement.
- **Terminal UI** (`archive-menu.py`) — keyboard-only search/status, for servers/SSH.

- **AI 검색 서버** — `archive.html` 서빙 + BM25(char-2gram) 검색 → 로컬 Claude CLI 답변 + 원문 위치로 스크롤. `--share`로 LAN 공유.
- **인테이크 체커** — 추가 전 중복·**모순 충돌** 탐지 + 배치 추천.
- **터미널 UI** — 키보드 전용 검색/현황 (서버·SSH용).

## Run · 실행
```bash
pip install -r requirements.txt        # optional: enables BM25 (else fallback) · 선택(BM25 활성화)
python archive-server.py               # → http://localhost:5174
python archive-server.py --share       # LAN
python archive-intake.py "ZSD030" "매출취소"   # intake check · 인테이크 점검
python archive-menu.py                 # terminal UI · 터미널 UI
```
Windows: double-click `run-server.bat` / `run-server-lan.bat` / `run-menu.bat`.
The Claude CLI is only needed for AI answers; search/intake/TUI work without it.
Claude CLI는 AI 답변에만 필요 — 검색·인테이크·TUI는 없어도 동작.

## ✏️ Edit directly (no Claude, no server) · 직접 수정 (클로드·서버 불필요)
**EN** — Open `archive.html` and click **✏️ 편집** (bottom-right): fix any text in place, **➕ 새 글** to add an article (it builds the structure + sidebar link + count for you), then **💾 저장**. On Chrome/Edge it writes back to the file via the File System Access API; other browsers download the updated file. No server, no Claude needed for simple knowledge entry/edits.

**KO** — `archive.html`을 열고 우하단 **✏️ 편집** → 글을 바로 고치고 **➕ 새 글**로 추가(구조·사이드바·카운트 자동) → **💾 저장**. Chrome·Edge는 File System Access API로 파일에 바로 저장 / 그 외 브라우저는 다운로드. 간단한 지식 입력·수정은 **서버도 클로드도 불필요**.

> 💡 **"기존 파일 덮어쓰기"가 걱정되면:** 내 파일을 방금 한 편집으로 갱신하는 것뿐이라 안전합니다(데이터 삭제 아님, 수정 반영). **처음 한 번만** `archive.html`을 골라 "덮어쓰기" 확인 → 이후엔 위치를 **기억해 한 번에** 저장. 화면 띄워둔 채로 OK. · **EN:** overwriting just updates *your own* file with your edits (nothing is wiped); pick the file once, then it's remembered for one-click saves — keep the page open while you do it.

## Files · 파일
| File | Role · 역할 |
|------|------|
| `archive.html` | the knowledge base (one file) · 지식 베이스 (단일 파일). Ships fictional sample · 가짜 샘플 |
| `archive-server.py` | BM25 retrieval + Claude CLI + in-page AI panel · 검색서버 |
| `archive-intake.py` | duplicate/conflict/placement checker · 인테이크 |
| `archive-menu.py` | terminal UI · 터미널 UI |
| `archive-structure.md` | the HTML-contract map + authoring reference · HTML 계약·작성 레퍼런스 |
| `run-*.bat`, `run-server.sh` | launchers · 실행 스크립트 |

## Rules · 규칙
- **Fictional sample data only** — never put real names/customers/T-Codes/secrets here.
  **가짜 샘플만** — 실명·고객·실 T-Code·자격증명 금지.
- Keep `archive-structure.md` in sync with `archive.html` (counts, ids). · 구조 인덱스 동기화.
- Retrieval design (why synonym expansion is NOT applied to ranking) is documented in
  `archive-server.py` (`_rank_scored`). · 랭킹 설계 주석 참고.
- The methodology behind this engine is in `../../archive-blueprint/`.
  엔진의 방법론 전체는 `../../archive-blueprint/`.
