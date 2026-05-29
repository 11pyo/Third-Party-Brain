---
doc_type: ai_reference
topic: change_log
purpose: "아카이브의 프로그램·알고리즘·구조 변경 이력. 콘텐츠(아티클) 변경은 여기 기록하지 않음 — archive-structure.md 소관."
scope: "program | algorithm | structure | encoding | deployment 변경만"
last_updated: 2026-05-29
rule: "신규 항목은 맨 위. 형식 고정: 날짜 / 분류 / 변경 / 영향파일 / 이유. (B)분류 변경 시 MANDATORY SYNC에 따라 이 파일 + 해당 .ai/.human 문서 동시 갱신."
---

# CHANGELOG (프로그램·알고리즘·구조)

> 분류 태그: `[STRUCTURE]` 파일/구성 · `[ALGO]` 검색/인테이크 로직 · `[ENCODING]` 인코딩 · `[DEPLOY]` 실행/배포/공유 · `[DOC]` 블루프린트 문서.

## 2026-05-29
- `[STRUCTURE]` **블루프린트 폴더 이동** — `C:\Users\<user>\Documents\Third-Party-Brain` → `C:\My-Projects\Third-Party-Brain`. 동기화 체인 참조 경로(`SAP SD AI Indexable Archive\.claude\CLAUDE.md`의 블루프린트 경로) 1곳 갱신. 동기화 끊김 없음 검증 완료.
  - 영향: 폴더 전체 위치, `…\.claude\CLAUDE.md`(블루프린트 경로)
  - 이유: 사용자 프로젝트를 `C:\My-Projects` 컨테이너로 통합.
  - 참고: 블루프린트 `canonical_example`(원본 아카이브 경로)는 아카이브 미이동이라 불변.
- `[STRUCTURE][DEPLOY]` **대화 로그 기능 추가** — `/query` 처리 시 질문/답변/시각/접속IP/참조아티클을 `conversations.jsonl`(BASE 디렉토리, 1줄=1대화 JSONL)에 append. `log_conversation()` 추가, do_POST에서 호출. 실패해도 검색 서비스에 영향 없음(try/except pass). 공유 검증 시 전임자 등 접속자의 모든 질의응답을 호스트 PC에서 사후 검토 가능.
  - 영향: `archive-server.py`(log_conversation, do_POST, CONV_LOG 상수, datetime import), 신규 산출물 `conversations.jsonl`
  - 이유: 공유 검증 중 접속자 대화가 어디에도 안 남아(일회성 claude -p, 브라우저 메모리만) 피드백 검토 불가했음.
  - 주의: 로그에 입력 내용 그대로 저장됨 → 민감정보 입력 금지 원칙 유지. 로그는 호스트 PC 로컬 파일.
- `[ALGO]` **동의어맵에 월 단위 정기업무 보강** — `월초/월별/정기/매달/이번달` 추가, 모두 `월별 오더생성(ZRSD0700)` + `월말결산(ZRSD1430, 결산)`을 함께 끌어오도록 매핑. 기존엔 "월초에 할 일" 질의가 `#sm-order-flow`만 반환하고 `#month-end-closing` 누락 → 답변에서 월말결산 빠짐. 수정 후 월초/월간/정기/이번달 질의 모두 top3에 `#month-end-closing` 포함.
  - 영향: `archive-server.py::SEARCH_SYNONYMS`
  - 이유: "월초/월간 할 일" 류 정기업무 질의가 결산을 못 끌어와 답변 누락 발생.
- `[DEPLOY]` 공유 모드(`--share`) 기동 시 **브라우저 자동 열기 주소를 localhost → LAN IP**로 변경. `browse_host = ip if cli.share else "localhost"`. 호스트 본인 브라우저에도 동료에게 줄 공유 링크(`http://{lan_ip}:5174`)가 바로 떠서 링크 복사 혼선 제거.
  - 영향: `archive-server.py`(open_browser)
  - 이유: 공유 모드인데 브라우저가 localhost로 열려, 그 주소를 동료에게 줘도 접속 안 되는 혼선 발생.
- `[DOC][STRUCTURE]` 블루프린트에 **MANDATORY SYNC 지침** + 이 CHANGELOG 신설. INV7(인코딩)·INV8(동기화)·INV9(상대경로 fetch) 추가. ARTIFACT MAP에 배치파일 5종 반영.
  - 영향: `00-INDEX.ai.md`, `00-INDEX.human.md`, `CHANGELOG.*`
  - 이유: 프로그램/구조 변경이 블루프린트에 자동 반영되지 않아 실제 구현과 문서가 어긋날 위험. 모든 AI 대상 강제 규칙화.
- `[DEPLOY][STRUCTURE]` **실행/종료 배치파일 5종 추가** — 1_개인모드, 2_공유모드, 3_개인종료, 4_공유종료, 5_전체종료. 개인=127.0.0.1 / 공유=0.0.0.0 바인딩 주소로 모드별 선택 종료(netstat `tokens=5`→taskkill, PID 0 제외).
  - 영향: `1~5_*.bat`(신규)
  - 이유: 비개발자도 더블클릭으로 서버 운용. 모드별 독립 종료 요구.
- `[ENCODING]` 배치파일 **CP949 인코딩 + 리다이렉션 제거** 확정. 한국어 cmd 기본 CP949에서 UTF-8 배치는 한글 줄이 명령으로 오인되어 깨짐. 또한 린터가 `>nul`→`>/dev/null`(Unix)로 변형 → cmd에서 실패. 해결: 배치는 CP949로 저장 + `>nul` 미사용(출력 약간 verbose 허용). 기동 배치는 python 직전 `chcp 65001`, 종료 후 `chcp 949`.
  - 영향: `1~5_*.bat`, 블루프린트 INV7
  - 이유: 한국어 Windows 호환 + 린터 변형 회피.
- `[DEPLOY]` `archive-server.py` **`--share` 플래그(LAN 공유)** 추가 — `0.0.0.0` 바인딩, 기동 시 LAN IP 링크·방화벽(netsh) 안내 출력. `allow_reuse_address=True`.
  - 영향: `archive-server.py`
  - 이유: 같은 네트워크 선임자 검증·협업.
- `[ALGO]` 프론트 fetch URL을 `http://localhost:5174/query` → **`window.location.origin + '/query'`** 상대경로화.
  - 영향: `archive-server.py`(AI 패널 JS)
  - 이유: LAN 공유 시 타 PC 브라우저에서 localhost가 자기자신을 가리켜 실패. INV9.
- `[ALGO]` 검색 품질 개선 — **동의어맵 확장**(`SEARCH_SYNONYMS`: 월간↔월말↔마감↔결산 등) + **제목/태그 히트 ×3 가중** + **짧은 ASCII코드(RE/CR/DR) 단어경계 매칭**(영어단어 substring 노이즈 제거). 빈 결과(질의어≠아카이브용어) 문제 해소.
  - 영향: `archive-server.py::search_relevant`, `load()`(tags 추출 추가)
  - 이유: "월간 작업" 질의가 "월말 결산" 아티클을 못 찾던 누락.
- `[STRUCTURE]` 페이지 내 자동 네비게이션 — 답변 후 첫 출처 아티클로 **자동 스크롤 + 하이라이트 플래시**, 출처 버튼, "페이지에서 이 내용 보기" 버튼. 시스템 프롬프트에 "이동 불가라고 말하지 말 것" 명시.
  - 영향: `archive-server.py`(AI 패널 JS/CSS, build_prompt)
  - 이유: 챗봇이 사이트 임베드 JS이므로 실제 페이지 제어 가능 — UX 개선.

## (이전) 블루프린트 v1.0 최초 작성 — 2026-05-29
- 5개 주제 × (ai/human) 10개 문서 + README 작성. 당시 구현 스냅샷 기준. 상세 빌드업은 `02-buildup-process.ai.md` P1~P10 참조.
