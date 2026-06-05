---
doc_type: ai_reference
topic: change_log
purpose: "아카이브의 프로그램·알고리즘·구조 변경 이력. 콘텐츠(아티클) 변경은 여기 기록하지 않음 — archive-structure.md 소관."
scope: "program | algorithm | structure | encoding | deployment 변경만"
last_updated: 2026-06-05
rule: "신규 항목은 맨 위. 형식 고정: 날짜 / 분류 / 변경 / 영향파일 / 이유. (B)분류 변경 시 MANDATORY SYNC에 따라 이 파일 + 해당 .ai/.human 문서 동시 갱신."
---

# CHANGELOG (프로그램·알고리즘·구조)

> 분류 태그: `[STRUCTURE]` 파일/구성 · `[ALGO]` 검색/인테이크 로직 · `[ENCODING]` 인코딩 · `[DEPLOY]` 실행/배포/공유 · `[DOC]` 블루프린트 문서.

## 2026-06-05
- `[DOC]` **운영 레이어·자동화 챕터 2개 신설** — `05-operational-layer.*`(무서버 대시보드·충돌없는 append-only id-merge 로그·AI유지 조직맵, INV-OL1~4), `06-automation-and-ops-model.*`(자가갱신 잠긴 스프레드시트 생성기·read-structure/guide-prod 모델·cross-repo 업적적재·공개수준 계층).
  - 영향: `05-*`, `06-*`(신규), `00-INDEX.*`(read_order·agent instructions·아티클수 de-stale), `README.md`(구조 트리)
  - 이유: 블루프린트가 코어(HTML+도구3)만 커버 → 실제로 더 크게 자란 운영/자동화 레이어 누락. 공개 sanitize 후 일반 패턴 추가.
- `[DOC]` 커스텀 코드 식별자 일반화(공개 sanitize) + 아티클 수 하드코딩 de-stale(03·00-INDEX). 06-02 알고리즘 개선 push.

## 2026-06-02
- `[ALGO]` **검색 컨텍스트 발췌를 '글 맨 앞 1800자'→'키워드 매칭 위치 주변 발췌'로 변경.** `search_relevant`가 본문을 `[:1800]`(항상 글 머리)로 잘라 넘기던 것을 신설 `extract_passage()`로 교체 — 키워드 첫 매칭 위치(−400/+1600) 발췌 + 글 머리(제목/도입 300자) 동봉, 상한 ~2200자. 매칭이 머리(≤300자)면 앞에서부터(기존 동일). `make_pattern()`을 search_relevant 내부 중첩 → 모듈 레벨로 승격(extract_passage와 공유).
  - 영향: `archive-server.py`(extract_passage 신규, make_pattern 모듈화, search_relevant 본문 추출부)
  - 이유: 아티클이 길어지며(특히 ops-cts-procedure에 SR처리유형분기·테스트결과서양식·②변경필요 입력가이드 등 누적) **뒤쪽 최근 추가 내용이 검색에 걸려도 컨텍스트에서 잘려** Claude가 못 보던 문제. 스모크테스트: "테스트 결과서 양식"/"SR 변경 불필요"/"반제" 질의에서 깊은 내용 포함 확인.
  - 계약 유지: `search_relevant(query)->[ctx]` 시그니처·컨텍스트 포맷(`[아티클: #id — title (cat)]\n{body}`) 불변 → 서버/프롬프트/자동스크롤 영향 없음(00-INDEX 불변식 무관).
- `[ALGO]` **검색 동의어맵 확장** — `SEARCH_SYNONYMS`에 최근 핵심어 14개 키 추가(반제/차변/대변/전표흐름/배차/테스트결과서/적용승인/적용관리/판매단가/NETPR/수금계획/계산서/SR/CTS). data-tags ×3 가중치만 의존하던 신규 주제어 질의 보강.
  - 영향: `archive-server.py::SEARCH_SYNONYMS`
  - 이유: 최근 추가 아티클(회계기초·반품취소②·CTS절차 확장)의 핵심어가 동의어맵에 없어 표현 차이로 누락 위험.
- `[ALGO]` **인테이크 정의-불일치 휴리스틱 추가** (archive-intake.py). 기존 `detect_conflict`(순서역전 4쌍)는 정의 충돌(한 코드가 글마다 'CR/DR이력'↔'반품이력'으로 어긋난 류)을 못 잡았음 → `detect_definition_divergence()` 신설: **사전 아티클(DICT_ARTICLES 9종)끼리** 같은 코드 뒤 '설명'을 글자 bigram Jaccard<0.18로 비교 → `[?] 정의 불일치 의심`. `_looks_definitional()`로 산문·링크 조각 제외, `_def_snippet()`은 CR/DR·I/O의 '/'를 보존. CONFLICT_PAIRS에 VF11→VL09·회계먼저/재고먼저 2쌍 추가.
  - 영향: `archive-intake.py`(CODE_RE, DICT_ARTICLES, _def_snippet, _char_bigrams, _looks_definitional, detect_definition_divergence, run STEP 3b, CONFLICT_PAIRS)
  - 이유: 정의 충돌(같은 코드 다른 설명)이 인테이크에서 안 잡혀 사람이 일일이 비교해야 했음. 사전끼리로 스코프를 좁혀 오탐 최소화.
  - 검증: 단위테스트(사전끼리 충돌 검출 / 사전vs산문 무시 / 일관케이스 무플래그) + 실데이터(예시 코드 다수 오탐 0). 한계: 표현차·교차언급에 잔여 advisory 1~2건 가능(정밀도 한계, '오탐 가능' 라벨).
- `[DOC]` 03-algorithms-scaling.*(검색 A절 발췌방식·인테이크 B절 3b·현재 N=58) 갱신.
  - 영향: `03-algorithms-scaling.ai.md`, `03-algorithms-scaling.human.md`
  - 참고: 본 변경들은 알고리즘 내부 개선으로 ARTIFACT MAP·CORE INVARIANTS 불변 → 00-INDEX 갱신 불요.

## 2026-05-29
- `[STRUCTURE]` **블루프린트 폴더 이동** — `C:\Users\<user>\Documents\Third-Party-Brain` → `C:\My-Projects\Third-Party-Brain`. 동기화 체인 참조 경로(`SAP SD AI Indexable Archive\.claude\CLAUDE.md`의 블루프린트 경로) 1곳 갱신. 동기화 끊김 없음 검증 완료.
  - 영향: 폴더 전체 위치, `…\.claude\CLAUDE.md`(블루프린트 경로)
  - 이유: 사용자 프로젝트를 `C:\My-Projects` 컨테이너로 통합.
  - 참고: 블루프린트 `canonical_example`(원본 아카이브 경로)는 아카이브 미이동이라 불변.
- `[STRUCTURE][DEPLOY]` **대화 로그 기능 추가** — `/query` 처리 시 질문/답변/시각/접속IP/참조아티클을 `conversations.jsonl`(BASE 디렉토리, 1줄=1대화 JSONL)에 append. `log_conversation()` 추가, do_POST에서 호출. 실패해도 검색 서비스에 영향 없음(try/except pass). 공유 검증 시 전임자 등 접속자의 모든 질의응답을 호스트 PC에서 사후 검토 가능.
  - 영향: `archive-server.py`(log_conversation, do_POST, CONV_LOG 상수, datetime import), 신규 산출물 `conversations.jsonl`
  - 이유: 공유 검증 중 접속자 대화가 어디에도 안 남아(일회성 claude -p, 브라우저 메모리만) 피드백 검토 불가했음.
  - 주의: 로그에 입력 내용 그대로 저장됨 → 민감정보 입력 금지 원칙 유지. 로그는 호스트 PC 로컬 파일.
- `[ALGO]` **동의어맵에 월 단위 정기업무 보강** — `월초/월별/정기/매달/이번달` 추가, 모두 `월별 오더생성(커스텀 T-Code)` + `월말결산(결산 T-Code)`을 함께 끌어오도록 매핑. 기존엔 "월초에 할 일" 질의가 `#sm-order-flow`만 반환하고 `#month-end-closing` 누락 → 답변에서 월말결산 빠짐. 수정 후 월초/월간/정기/이번달 질의 모두 top3에 `#month-end-closing` 포함.
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
