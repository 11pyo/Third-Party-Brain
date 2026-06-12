# 운영 대시보드 — 참조 구현 (익명 동작본)

> `archive-blueprint/07-dashboard-operating-guide`에서 **설명만** 하던 대시보드를, 실제로 **더블클릭하면 돌아가는** 익명 동작본으로 제공합니다.
> ⚠️ **여기 들어있는 모든 데이터(태스크·문의·요청자 이름)는 가상 샘플입니다.** 실제 회사 데이터는 포함되지 않습니다.

---

## 무엇인가
서버·DB·빌드 없이 **파일 4개**로 도는 운영 작업판입니다. 칸반(일회성)·정기업무(주/월/연)·문의 처리이력 3보드를 한 화면에 표시하고, 문의 로그는 **추가전용 id-병합** 방식이라 여러 세션이 동시에 기록해도 충돌하지 않습니다.

원리·규칙·상세 설계는 블루프린트 문서를 보세요:
- `archive-blueprint/07-dashboard-operating-guide.human.md` (규칙 R1~R8·사용법)
- `archive-blueprint/05-operational-layer.human.md` (왜 이런 레이어인가)

## 영감 — 토요타 칸반 · Inspiration — Toyota Kanban
**KO** — 보드 형태(작업을 카드로 만들어 상태 컬럼 사이로 흘려보냄)는 **토요타 생산방식(TPS)의 칸반(看板)** JIT 신호에서 유래해 Lean·Agile의 칸반 방식으로 이어진 계보를 따릅니다. 즉 *작업 흐름 시각화*는 토요타 칸반에서 영감. 단, **추가전용+id병합 동시기록 안전·무백엔드**는 토요타가 아니라 **이벤트 소싱/로그 구조** 계열의 별개 아이디어입니다.
**EN** — The board form (cards flowing across status columns) descends from the **Toyota Production System's kanban (看板)** JIT signaling, via the Lean/Agile Kanban method — so the *work-flow visualization* is inspired by Toyota. The **append-only + id-merge, backend-less concurrency safety** is a separate, event-sourcing-style idea (not from Toyota).

## 구성 파일

| 파일 | 역할 |
|------|------|
| `task-board.html` | **화면.** 더블클릭하면 브라우저에서 열림(서버 불요). 안에 `const TASKS=[…]` 샘플 카드 배열을 품고, `inquiry-log.js`를 `<script src>`로 읽음. |
| `tasks.md` | **정본(正本).** 프로젝트 태스크의 원본(마크다운). 화면은 이걸 미러링한 것. |
| `inquiry-log.js` | **문의 처리이력 데이터.** 추가전용 푸시로그(같은 id 재push=상태 전이 병합). |
| `log-inquiry.py` | **문의 로그 헬퍼 CLI.** 로그를 직접 편집하지 않고 이 스크립트로 한 줄씩 안전하게 덧붙임(OS 파일락). |

## 실행

**① 화면 보기** — `task-board.html` 더블클릭 (또는 브라우저로 열기, 서버 불요).
**② 문의 기록은 AI에게 말로** — 명령어를 직접 칠 필요 없이, AI에게 *"이 문의 접수해줘 / 진행중으로 바꿔줘 / 답변 달고 완료해줘"* 라고 하면 AI가 아래 `log-inquiry.py`를 **대신 실행**합니다. (핵심 = 사람이 CLI를 외우는 게 아니라 **AI가 대신 안전하게 기록**.)
**③ 브라우저 새로고침** = 반영.

<details><summary>↳ AI가 실제로 실행하는 명령 (직접 쓰고 싶을 때만 펼쳐 보세요)</summary>

```bash
# 새 문의 접수 → 상태 전이 → 완료 (같은 id 재사용 = 병합)
python log-inquiry.py --new --type 단순문의 --q "<문의 요약>" --by <기록자> --req "<요청자·조직>"
#   → 'NEW id=INQ-YYMMDD-HHMMSS' 의 id 를 기억
python log-inquiry.py --id <그-id> --status 진행중
python log-inquiry.py --done --id <그-id> --a "<처리 요약>" --ref "#<관련-앵커>"
```
</details>

- 카드를 **✏️수정**한 뒤 편집바의 **💾 파일에 저장**을 누르면 **서버·클로드 없이 파일(`task-board.html`)에 바로 기록**됩니다 (Chrome·Edge는 File System Access API로 즉시 저장 / 그 외 브라우저는 다운로드). 「변경분 내보내기(JSON)」는 `tasks.md`를 클로드로 동기화하던 옛 방식입니다. · **EN:** edit a card, then **💾 Save to file** writes it straight back to `task-board.html` (no server, no Claude); the JSON export is the old Claude-sync path.
- **🤖 AI 참조 로그 — 카드 2층 구조 (2026-06-12)**: 카드 = **본문**(사람용·잘 정리된 현재 상태) + 접힘 **`ailog`**(AI용 — 시계열 작업로그·교훈·AI 방침). 긴 개발 카드도 **내용을 줄이지 않고(AI 문맥 전부 보존) 사람 화면은 깔끔하게**. **AI는 카드 작업 시 접힌 로그까지 반드시 정독**(기확정 사항이 거기 있음), 사람은 본문까지만. 갱신=로그에 append(축약 금지)+본문은 현재형 재정리. · **EN:** two-layer cards — curated body for humans + collapsed `ailog` (work log / lessons / AI policies) that **AI assistants must also read**; humans can skip it. Append to the log, keep the body curated.
  - 💡 **"덮어쓰기"가 걱정되면:** 내 파일을 방금 한 편집으로 갱신하는 것뿐(데이터 삭제 아님). **처음 한 번만** 파일을 골라 확인하면 이후엔 위치를 **기억해 한 번에** 저장(폴더 안 찾음). 화면 띄워둔 채로 OK. · **EN:** overwriting just updates *your own* file with your edits; pick it once, then one-click saves remember the location.
- 완료 열은 높이 고정+스크롤이고, 열 머리의 **`⤢ 전체보기`**로 완료 카드를 큰 모달에서 모아 봅니다.

## 카드 폼 구조 (수정 전 필독) · Card form structure (read before editing)

**KO** — 두 종류의 카드 모두 **"헤더(요약) + 클릭하면 펼쳐지는 상세"** 패턴입니다.

- **① 프로젝트 카드 `.card`** — `viewHTML()`로 렌더. 헤더: ID·제목·기한 + 노란 `.next`(다음 액션 요약). 클릭 → `.detail` 펼침(`.open` 토글).
- **② 문의 카드 `.inq-card`** — `inqCard()`로 렌더. 헤더 `.inq-head`(항상 보임=클릭 영역): ▸캐럿 + INQ코드 + 요청자 칩 + 유형 배지(단순/일반/긴급) + 노란 `.inq-sum`(질문). `.inq-detail`(접힘): 처리/답변 + 참조링크 + 날짜·기록자. 헤더 클릭 시 펼침. 토글은 `#inqboard`에 **이벤트 위임**(재렌더에도 유지), 완료열 「⤢ 전체보기」 모달에선 자동 펼침.

**렌더 ≠ 데이터** (꼭 구분):

| 카드 | 렌더 함수 | 데이터 출처 | 수정 방법 |
|------|-----------|-------------|-----------|
| 프로젝트 카드 | `viewHTML()` | JS `TASKS` 배열 | `tasks.md`와 **수기 동기화** (브라우저 편집은 localStorage만) |
| 문의 카드 | `inqCard()` | `inquiry-log.js`의 `INQUIRY_LOG` | **`log-inquiry.py` 헬퍼로만** (직접 편집 금지) |

> ⚠️ 폼 수정 시 **`.inq-sum`·`.inq-detail`·`.inq-cy` CSS와 `#inqboard` 토글 위임을 함께 유지**할 것.
> 이건 **대시보드 UI**라 **아카이브 블루프린트 동기화 대상이 아님**(코어 아카이브의 도구·알고리즘·구조 변경이 아니므로).

**EN** — Both card types now follow a **"header (summary) + click-to-expand detail"** pattern.

- **Project card `.card`** (rendered by `viewHTML()`): header = ID · title · due + yellow `.next` (next-action summary); click → `.detail` expands (`.open` toggle).
- **Inquiry card `.inq-card`** (rendered by `inqCard()`): header `.inq-head` (always visible = click target) = ▸caret + INQ code + requester chip + type badge (simple/normal/urgent) + yellow `.inq-sum` (the question). `.inq-detail` (collapsed) = resolution/answer + ref link + date/recorder; click the header to expand. Toggle uses **event delegation on `#inqboard`** (survives re-render); auto-expanded inside the done-column "⤢ view all" modal.
- **Render ≠ data:** project card ← `TASKS` array (sync with `tasks.md` by hand; browser edits are localStorage-only); inquiry card ← `INQUIRY_LOG` in `inquiry-log.js` (append **only** via `log-inquiry.py`, never hand-edit).
- ⚠️ When changing the form, keep the `.inq-sum` / `.inq-detail` / `.inq-cy` CSS and the `#inqboard` toggle delegation **together**. This is **dashboard UI → NOT subject to archive-blueprint sync**.

## 자기 도메인에 맞추기
1. `tasks.md` + `task-board.html`의 `const TASKS` 배열을 본인 업무 카드로 교체(둘 다 동기화).
2. `inquiry-log.js`의 샘플 push를 지우고, 실제 문의는 `log-inquiry.py`로만 덧붙임.
3. 카드 분류 색상(dev/ops/ts/adm)·정기 주기(주례/월례/연례)는 그대로 쓰거나 도메인에 맞게.

> 🔒 **공개 주의**: 이 작업판을 다시 외부에 공유한다면, `tasks.md`·`inquiry-log.js`·`task-board.html`의 `TASKS`에 들어간 **실제 고객명·문서번호·금액·실명은 반드시 가린 뒤** 공유하세요. (이 참조 구현이 그 익명화의 본보기입니다.)
