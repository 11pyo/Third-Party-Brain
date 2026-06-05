---
doc_type: ai_reference
topic: operational_layer_dashboard_conflictfree_log_orgmap
version: 1.0
last_updated: 2026-06-05
purpose: "정적 아카이브 위 '운영 레이어' — 무서버 대시보드 + 충돌없는 append-only 로그(멀티세션) + AI유지 조직맵. 재현/확장 시 참조."
---

# OPERATIONAL LAYER

## 1. 대시보드 (static, no-server)
- `task-board.html`(단일) + 데이터파일. 더블클릭 실행, 서버 불요.
- 보드 3: 일회성(상태 칸반 접수/진행중/대기/완료) · 정기업무(주/월/연 cadence) · 문의이력.
- 정본=마크다운(`tasks.md`), 화면=미러 HTML. 동기화 규율(정본↔화면).
- UX: 완료 컬럼 max-height+overflow, 카드 newest-first(list.reverse), 카드 inline-edit(localStorage override + 변경분 export).

## 2. ⭐ CONFLICT-FREE APPEND-ONLY LOG (멀티 writer)
- 1줄=1이벤트. push-log(`window.LOG = window.LOG || []; window.LOG.push({...})`), append만.
- **id-merge**: 같은 id 후속 push가 prior 필드 `Object.assign` 병합 → 상태전이=append(수정 아님). 렌더 시 id별 최종 병합.
- writer=헬퍼 스크립트만(파일 직접편집 금지). OS append 원자성 → 동시기록 충돌 0.
- file:// fetch 제약 → 데이터를 `<script src="log.js">`로 로드(JS push-log). HTTP 서버 불요.
- 불변식: 헬퍼만 append / id=병합키 / 화면은 새로고침 시 반영 / 빈값 필드는 병합서 무시.

## 3. 조직맵 (AI-maintained)
- 단일 표(조직·역할·담당·채널). 문의 식별·라우팅용. 아카이브 아티클 1개로 둘 수도 있음(검색가능).
- 자동 갱신 규율(프로젝트 지침에 명시): 업무 처리 시마다 ①신규조직 행추가 ②기존조직 유형보강 ③담당/채널 변경 반영. 로그 헬퍼의 requester 필드와 짝.
- PII(사번·전화·이메일) 미기록 → 비공유 로컬.

## 설계 불변식
- INV-OL1: 동시성 = append-only + id-merge (락/DB 없음).
- INV-OL2: 데이터는 `<script src>` 로드 (file:// 호환, 무서버).
- INV-OL3: 정본(md) ↔ 화면(html) 동기화는 작업의 일부.
- INV-OL4: 살아있는 문서(대시보드·조직맵)는 AI가 규율로 유지.

## 재현 트리거
"대시보드/문의로그/조직맵 만들어줘" → ① task-board.html(칸반 3보드) ② log 헬퍼(append+id-merge) + `<script src>` 데이터 ③ 조직맵 표 + 자동갱신 규율을 프로젝트 지침에 기입.
