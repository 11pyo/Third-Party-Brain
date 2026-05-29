---
doc_type: ai_reference
topic: buildup_process_chronology
version: 1.0
last_updated: 2026-05-29
---

# BUILDUP PROCESS — 0에서 현재까지의 진화 순서

## PHASE 진화 (실제 빌드 순서, 재현 시 참고)
1. **P1 데이터 시드**: 인수인계 자료(.txt/구두) → 도메인 용어·T-Code·프로세스 추출 → 첫 아티클 작성. 카테고리 골격(기초용어/프로세스/기술설정/트러블슈팅) 확정.
2. **P2 단일 HTML화**: 아티클을 `<article id data-tags>` 규격으로 통일. 인라인 CSS 컴포넌트(박스/배지/표/플로우바) 정립. 사이드바 nav + 카운트.
3. **P3 인덱스 분리**: HTML이 커지자 매 세션 전체 읽기 비효율 → `archive-structure.md` 도입(id·제목·라인번호·카운트·CSS레퍼런스). **규칙: 편집 후 3곳 동기화.**
4. **P4 검증/정제**: 외부지식·웹서치와 충돌·중복·공백 점검. 발견 이슈 예) TYPE P 기본길이 오류, SI 투입취소 순서 아티클 간 충돌, UKM 사용여부 미확인.
5. **P5 인테이크 알고리즘**: 신규 정보 자동 분기 요구 → `archive-intake.py`(동의어확장→검색→충돌패턴감지→카테고리분류→중복도). CLI.
6. **P6 계층 탐색 UI**: `archive-menu.py` — 검색/인테이크/현황/빠른참조 4계층 TUI. breadcrumb.
7. **P7 로컬 AI 검색**: `archive-server.py` — HTTP 서버가 HTML 서빙 + `/query`에서 관련 아티클 추출→`claude -p` 호출. 우측 AI 패널 주입.
8. **P8 검색 품질 튜닝**: 빈 결과 문제(질의어≠아카이브용어) → 동의어맵 + 제목/태그 ×3 가중 + 짧은 ASCII코드 단어경계 매칭(RE/CR/DR 노이즈 제거).
9. **P9 네비게이션 결합**: 답변→해당 아티클 자동 스크롤 + 하이라이트 + 출처 버튼. 시스템 프롬프트에 "이동 불가라고 말하지 말 것" 명시.
10. **P10 LAN 공유**: `--share`(0.0.0.0 바인딩) + fetch를 `window.location.origin` 상대경로화 + 방화벽 규칙 안내.

## 반복적으로 마주친 함정 (FIX 패턴)
- **Windows 인코딩**: 한글 print → CP949 에러. FIX: stdout UTF-8 wrap; cmd 경유 출력은 `chcp 65001` + 다중 인코딩 폴백 디코드. CLI 인자에 한글 직접 전달 금지 → 임시파일/stdin.
- **좀비 서버**: 백그라운드 재기동 누적 → 포트 점유. FIX: 재기동 전 `netstat -ano|findstr :PORT`로 PID 추출 후 taskkill. `allow_reuse_address=True`.
- **claude 경로**: PATH에 없을 수 있음. FIX: which→APPDATA npm→glob 3단 폴백.
- **하드코딩 URL**: `localhost:5174`는 타 PC에서 자기자신 가리킴. FIX: 상대경로.
- **검색 0건**: 질의어와 아카이브 용어 불일치. FIX: 동의어맵 + 제목 가중치.

## 작업 규율 (매 편집 시)
- 아티클 추가/삭제 → 3곳 동기화(nav·카운트·structure.md).
- 인테이크 전 `archive-intake.py`로 중복·충돌 검사.
- 민감정보 저장 금지(비밀번호·IP·계정·인증서경로).
- 인코딩 변경/도구 수정 후 직접 실행 검증(테스트 케이스 ≥3).
- T-Code 표기는 항상 `코드 — 화면명`.
