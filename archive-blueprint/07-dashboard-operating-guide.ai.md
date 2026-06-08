---
doc_type: ai_reference
topic: dashboard_operating_rules_and_usage
version: 1.0
last_updated: 2026-06-08
purpose: "운영 대시보드(무서버 칸반 + 추가전용 id-병합 문의로그)를 실제로 굴리는 규칙·CLI 사용법. 05-operational-layer(개념)의 실무 매뉴얼. 재현/운영 시 참조."
related: [05-operational-layer]
---

# DASHBOARD — OPERATING RULES & USAGE

> 05-operational-layer = 개념/불변식(INV-OL1~4). 이 문서 = 운영 규칙(R1~R8) + 헬퍼 CLI 계약 + 렌더 시맨틱.

## ARTIFACTS (4)
| 파일 | 역할 | writer |
|------|------|--------|
| `tasks.md` | 정본(正本) — 프로젝트 태스크 칸반·상세(마크다운) | 사람/AI 직접 |
| `task-board.html` | 화면 — `tasks.md` 미러(단일 HTML, 더블클릭, 서버불요). `const TASKS=[...]` 배열 + `<script src="inquiry-log.js">` | 정본 미러 |
| `inquiry-log.js` | 문의이력 데이터 — append-only push-log | ⚠️ 헬퍼 전용(직접편집 금지) |
| `log-inquiry.py` | 문의 로그 헬퍼 CLI — 1줄 append + id-merge + OS락 | 호출만 |

## BOARDS (3, in task-board.html)
- **프로젝트 태스크**: 상태 칸반 접수/진행중/대기/완료. cards = `const TASKS` (정본 미러).
- **정기업무**: 주/월/연 cadence 별보드(일회성과 분리, 평소 "트리거 대기").
- **문의이력**: 상태 칸반 4열, 데이터=`inquiry-log.js`(id-merge fold).
- 카드: id + title + **requester chip(req)** + due + next-action + detail(collapsible). 완료열 max-height+overflow, newest-first; **완료열 한정** `+전체보기`(완료 카드≥1)→모달(openFullView).
- TASKS 카드 스키마(프로젝트 태스크): `{id, cls(분류→색상클래스: 개발|운영|트러블 등), title, status:"접수"|"진행중"|"대기"|"완료", req(요청자·조직), due, next, detail, warn:bool}`. **정기업무 카드는 status 대신 반복주기(cadence: 주례|월례|연례)** 를 가져 정기 보드로 분리 렌더(평소 "트리거 대기"). ↔ 문의로그 FIELD SCHEMA는 아래 HELPER 절.

## HELPER CLI CONTRACT (log-inquiry.py)
```
① 접수:  --new --type 단순문의|일반요청|긴급문의 --q "<요약>" --by <기록자> --req "<요청자·조직>" [--date YYYY-MM-DD]
          → stdout 'NEW id=INQ-YYMMDD-HHMMSS' (id 보존 필수; --id 미지정 시 타임스탬프로 자동생성)
② 전이:  --id <id> --status 진행중|대기
③ 완료:  --done --id <id> --a "<처리/답변>" --ref "#<앵커>"   (=--status 완료)
※ 접수+즉답: ①에 --a 또는 --status 완료 동봉 → 바로 완료
```
- FIELD SCHEMA: `{id, date, type, q, a, by, req, ref, status:"접수"|"진행중"|"대기"|"완료"}`.
- APPEND 시맨틱: 매 호출 = `window.INQUIRY_LOG.push({...})` 1줄 추가. **빈 값 필드는 안 보냄**(준 값만 갱신).
- ID-MERGE: 같은 id 후속 push가 prior 필드 덮어쓰기 병합 → 상태전이=append(수정 아님). 렌더가 id별 fold.
- CONCURRENCY: append를 OS 파일락(`.lock` 게이트; Windows msvcrt.locking / POSIX fcntl.flock)으로 보호. 락 실패해도 기록 유지(best-effort). → 멀티 writer 충돌 0.
- VALIDATION: status는 4값만; `--id`만 주고 변경필드 없으면 거부; `--new`도 `--id`도 없으면 거부.

## RENDER SEMANTICS (task-board.html)
- `mergedTasks() = TASKS.map(t => ({...t, ...overrides[t.id]}))` — localStorage override 병합.
- 편집(openEdit)=localStorage override만(정본 불변) + 「변경분 내보내기(JSON)」로 정본 역동기화(한 방향).
- 문의보드: INQUIRY_LOG를 id별 최종병합 → 상태별 컬럼 분배 → 완료열 scroll. 새로고침=반영(빌드 없음).

## OPERATING RULES (R1~R8)
- R1 정본=`tasks.md`(md), 화면=`task-board.html` 미러. 태스크 변경=둘 다 갱신(동기화는 작업의 일부).
- R2 `inquiry-log.js`는 헬퍼 전용(append-only+id-merge 무결성 — 직접편집 금지).
- R3 멀티세션 전권(파일 도메인 분리 없음; 빈 세션 1=프로젝트 1 완주). 충돌방지 2: ①편집 직전 재읽기 ②문의로그는 헬퍼만.
- R4 requester chip(req=요청자·조직) 채움 → 추적·라우팅.
- R5 태스크 추가/삭제 시 3곳 동기화: 정본 md / 화면 TASKS / 집계 카운트.
- R6 정기업무는 일회성과 분리·트리거 대기.
- R7 완료열 scroll·newest-first·전체보기 모달.
- R8 민감정보는 데이터파일(로컬)에만. 공개본=구조·규칙·익명예시만. PII(전화·이메일·사번) 데이터파일에도 미기록(비공유 로컬).

## SANITIZATION (공개 시)
- 실데이터(`tasks.md`/`inquiry-log.js`)엔 고객사명·실명·문서번호(주문/계산서/결재)·금액·커스텀코드 세부 포함 → **데이터파일 자체는 비공개**.
- 공개 = 보드구조 + id-merge 로그패턴 + 헬퍼 CLI 설계 + R1~R8 + 익명예시.
- DENYLIST(공개 산출물에 등장 금지): 회사/고객/사람 고유명, 커스텀 T-Code/테이블/CTS/SR/IO/오더유형 식별자, 실 문서·금액·사번, 전화·이메일.

## 재현 트리거
"대시보드/문의로그 만들어줘" → ① `task-board.html`(칸반 3보드: 일회성·정기·문의) ② `log-inquiry.py`(append-only id-merge + OS락) + `<script src>` 데이터(`inquiry-log.js`) ③ R1~R8을 프로젝트 지침(에이전트 규칙 파일)에 기입.
