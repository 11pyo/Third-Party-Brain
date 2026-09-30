---
doc_type: ai_reference
topic: automation_and_readonly_ops_model
version: 1.0
last_updated: 2026-09-28
purpose: "반복 산출물 자동화(자가갱신 잠긴 스프레드시트) + 읽기전용 운영시스템 안전모델(read-structure/guide-prod) + 크로스레포 업적적재. 재현 시 참조."
---

# AUTOMATION & OPS MODEL

## 1. 자가갱신 잠긴 산출물 (생성기 패턴)
- 정형 스프레드시트: 누계/총계/차트 = 수식·참조 자동. 값만 바꾸면 전파.
- 연/월 auto-extend: 데이터 N으로 차트 앵커(two-cell anchor류)·합계 범위 동적 계산 → 행 추가 시 자동 포함. 최신 행/연도 강조도 max(year)로 추종.
- 잠금: sheet protection + workbook structure lock. 갱신 = 생성기 재실행만(수기편집 차단).
- 무손실 시트 재정렬: 라이브러리 재저장(서식손실) 대신 zip 내부 `<sheet>` 엘리먼트 순서만 교체(sheetId/rId 불변 → 데이터·차트 무손실).
- 규율: 손수정 금지·생성기 재실행 / 파일 open이면 저장 불가(닫고 재생성) / 데이터·비번은 공유폴더 밖 / 라벨 글꼴은 txPr로 축소(겹침 완화).

## 2. ⭐ READ-STRUCTURE / GUIDE-PROD (읽기–가이드 분리)
- 전제: 운영시스템 직접 접근/쓰기 차단(API/권한 막힘) → AI 조회조차 불가.
- 모델: 인접 개발/구조 시스템(읽기 가능)으로 구조·소스·데이터흐름 read → 근거로 사람이 prod GUI에서 할 일을 화면·필드·키값·단계로 guide → 결과(스크린샷/값) 받아 재해석·next step.
- AI = 보는눈(구조) + 길잡이(prod GUI). 실행 = 사람. 변경은 정식 절차.
- 일반화: 권한막힌 환경에서 "읽을 수 있는 인접 시스템 + 사람 실행"으로 가치 산출. 재시도로 막힌 접근 뚫으려 말 것(차단은 정책).

## 3. 업적 적재 (cross-repo, append-only)
- 유의미 성과 → 별도 커리어 레포에 append. dedup(ID/제목). **공개수준 분류**(PUBLIC/INTERNAL/CONFIDENTIAL), 기밀=외부 미포함.

## 4. 규칙→도구 집행 (Claude Code 훅, 2026-09-28)
- UserPromptSubmit `prompt_context.py` = 세 곳 선행검색 자동 주입(경량 RAG, ≤1,500자) · Stop `stop_board_sync.py` = 카드 변경 시 인덱스 재생성+동기화 점검, 어긋나면 block 1회 · `permissions.ask` = 개발계 전송요청 생성·릴리즈·삭제 확인창.
- 원칙: 기억에 의존하는 수기 단계는 수정 시각·이벤트로 판정하는 도구로 옮긴다. 훅 출력은 매 라운드 재독되므로 짧게.

## 5. ⭐ 멀티 프론티어 AI 상호운용성 (Multi-Frontier AI Interoperability, 2026-09-30)
- **전제**: AI 모델·도구는 영구적이지 않다(Claude, Gemini, GPT, Cursor 등 세대교체 지속). 시스템은 특정 벤더에 종속되지 않고 '두뇌 엔진'만 갈아 끼워도 동작해야 한다.
- **규칙 파이프라인 패턴 (`_gen_host_rules.py`)**: 단일 모델 독립 정본(`SYSTEM_RULES.md`)을 기준으로 호스트별 규격(Claude `.claude/CLAUDE.md`, Codex/Cursor `AGENTS.md`, Gemini `GEMINI.md`, Antigravity `.agents/rules/rules-*.md`)을 자동 생성. 사람이 여러 벌을 손수 맞추지 않는다.
- **도구 기능적 추상화 (Tool-Agnostic Abstraction)**: 도구 이름(Read vs view_file vs read_file)이 달라도 '행동 원칙(근거 라벨링 A/B/C/D, 파괴적 작업 전 중단)'과 '접근 권한 게이트'는 동일하게 제어.
- **비-훅(Hook-less) 자율 가드레일**: 훅이 없는 호스트에서도 AI가 자율적으로 "선행 검색 3곳(인덱스·구조표·문의로그)"과 "종료 전 보드 동기화 검증(`_check_board_sync.py`)"을 직접 수행하도록 지침 표준화.
- **일반화**: "AI는 교체 가능한 엔진, 핵심은 독립적인 지식·협업 운영체계". 벤더 락인 제로 달성.

## 보안/공개수준 (정직)
- 공유본 = 실데이터 익명화 / 내부트래커 = 실명 OK / 기밀·PII = 비공유 로컬.
- ⚠️ 가역인코딩(base64)·sheet protection ≠ 암호화(억지력). 진짜 보호 = 공유 안 되는 위치. 한계 명시 의무.

## 재현 트리거
"정형 보고 자동화/운영 가이드/업적 적재/멀티 AI 호환" → ① 수식·차트 자가갱신 + 잠금 생성기 ② read-structure→guide-prod 가이드 작성 ③ 공개수준 분류 append ④ 모델 중립 규칙 파이프라인 생성.
