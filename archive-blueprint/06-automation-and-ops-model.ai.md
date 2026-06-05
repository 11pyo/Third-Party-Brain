---
doc_type: ai_reference
topic: automation_and_readonly_ops_model
version: 1.0
last_updated: 2026-06-05
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

## 보안/공개수준 (정직)
- 공유본 = 실데이터 익명화 / 내부트래커 = 실명 OK / 기밀·PII = 비공유 로컬.
- ⚠️ 가역인코딩(base64)·sheet protection ≠ 암호화(억지력). 진짜 보호 = 공유 안 되는 위치. 한계 명시 의무.

## 재현 트리거
"정형 보고 자동화/운영 가이드/업적 적재" → ① 수식·차트 자가갱신 + 잠금 생성기 ② read-structure→guide-prod 가이드 작성 ③ 공개수준 분류 append.
