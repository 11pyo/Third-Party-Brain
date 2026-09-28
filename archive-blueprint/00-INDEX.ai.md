---
doc_type: ai_reference
audience: llm_agent
purpose: "검색 가능한 운영 지식 아카이브를 0에서 구축·운영·복제하기 위한 방법론 청사진의 진입점(index)"
canonical_example: "C:/Users/<user>/Documents/SAP SD AI Indexable Archive"
version: 2.5
last_updated: 2026-09-22
read_order: [00-INDEX, 01-overview-architecture, 02-buildup-process, 03-algorithms-scaling, 04-replication-playbook, 05-operational-layer, 06-automation-and-ops-model, 07-dashboard-operating-guide, CHANGELOG]
pairing: "각 문서는 .ai.md(에이전트용) + .human.md(사람용) 쌍으로 존재. 동일 내용의 다른 표현."
governance: "아카이브의 프로그램·알고리즘·구조 변경 시 이 블루프린트 동기화 + CHANGELOG 기록 의무 (아래 MANDATORY SYNC 참조)"
---

# ARCHIVE BLUEPRINT — AI ENTRY POINT

## ⛔ MANDATORY SYNC DIRECTIVE (아카이브를 수정하는 모든 AI 필독·필수)
**범위 구분:**
- (A) **지식/콘텐츠 변경** (아티클 추가·수정·삭제 = `archive.html` 내용) → 이 블루프린트 동기화 **불요**. `archive-structure.md`만 갱신.
- (B) **프로그램·알고리즘·구조 변경** (`archive-server.py`/`archive-intake.py`/`archive-menu.py` 로직, 검색·인테이크 알고리즘, 파일 구성, 빌드/실행 방식, 인코딩 정책, 배포 방식 등) → **이 블루프린트 동기화 의무.**

**(B)에 해당하면 같은 작업 내에서 반드시:**
1. 영향받는 블루프린트 문서(.ai.md + .human.md 쌍)를 **함께** 갱신 — 예: 알고리즘 변경 → `03-*`, 구조/파일 변경 → `01-*`·`02-*`·이 파일의 ARTIFACT MAP, 복제절차 영향 → `04-*`.
2. `CHANGELOG.ai.md` + `CHANGELOG.human.md` 에 **항목 추가** (날짜·분류·변경내용·영향파일·이유). 최신 항목이 맨 위.
3. 변경이 INVARIANT를 건드리면 CORE INVARIANTS 절도 갱신.
4. `version` / `last_updated` 갱신.

> 이 지침을 어기면 블루프린트가 실제 구현과 어긋나 다음 세션 AI가 잘못된 전제로 작업하게 된다. 동기화는 선택이 아니라 작업의 일부다.

## WHAT THIS IS
이 폴더(`archive-blueprint/`)는 **"AI가 색인·검색 가능한 단일 HTML 운영 지식 아카이브"** 패턴을
재현하기 위한 자기완결적(self-contained) 방법론이다. 원본 사례는 SAP SD 운영 아카이브 (예시 도메인).
다른 도메인(다른 ERP 모듈, 다른 회사, 일반 사내 위키)에도 그대로 응용 가능하다.

## IF YOU ARE AN AGENT, DO THIS
0. **빠른 온보딩** → 루트 `AGENTS.md`(기능·룰·방향 한 장; Claude Code는 `CLAUDE.md` 자동 로드→여기로 유도) 먼저. 실행 가능한 동작본 = `reference-implementation/archive/`(아카이브 엔진: BM25 검색서버·인테이크·TUI + 샘플 `archive.html`) · `reference-implementation/dashboard/`(대시보드 — **별도 전용 레포 `11pyo/ai-collab-dashboard`**).
1. 사용자가 "새 아카이브 만들어줘" / "이런 거 또 만들어줘" → `04-replication-playbook.ai.md` 로 점프.
2. 사용자가 기존 아카이브를 수정/확장 → `03-algorithms-scaling.ai.md`(인테이크 규칙) + 원본 `archive-structure.md` 먼저 읽기.
3. 구조/기술 이해 필요 → `01-overview-architecture.ai.md`.
4. "어떻게 만들어졌나" 이력 → `02-buildup-process.ai.md`.
5. 대시보드/문의로그/조직맵 (개념) → `05-operational-layer.ai.md`. 정형보고 자동화/읽기전용 운영시스템 가이드/업적적재 → `06-automation-and-ops-model.ai.md`.
6. 대시보드 **운영 규칙·CLI 사용법** (실무 매뉴얼) → `07-dashboard-operating-guide.ai.md`. 실행 가능한 익명 동작본(더블클릭 실행) → `reference-implementation/dashboard/`.
7. 사용자가 "범용 LLM‑위키(예: Karpathy LLM Wiki·에이전트 `wiki` 스킬)와의 차이/결합"을 물으면 → 보조 노트 `COMPARISON-llm-wiki.md`(번호 챕터 아님; 비교 + 2단 scratch→canonical 승격 게이트 매핑[NEW/UPDATE/CONFLICT/REVIEW]).

## ARTIFACT MAP (원본 아카이브 구성물)
| 파일 | 역할 | 비고 |
|------|------|------|
| `archive.html` | 단일 HTML 지식 베이스 (전체 데이터+UI+CSS+JS 인라인) | 수십~수백 아티클 / 5 카테고리(예시 도메인, 계속 증가). AI 패널은 서버가 런타임 주입. **탐색 층**(색인·문서·전체 3모드 + 런타임 역인덱스)이 `</body>` 직전 블록으로 내장 — 상세 `01-*` |
| `archive-structure.md` | 경량 인덱스 (세션마다 전체 HTML 안 읽도록) | id·제목·키워드·카운트. **라인 열 없음**(2026-09-07 폐지 — 수기 라인은 반드시 낡는다; 위치는 `grep -n 'id="…"'`). **헤더 변경이력도 별도 파일로 분리**(2026-09-22 — 「최종 업데이트」 한 줄이 43KB까지 자란 걸 발견해 `archive-structure-changelog.md`로 이관, 헤더엔 최신 1건 요약만) |
| `archive-intake.py` | 신규 정보 인테이크 — 중복·충돌·배치 자동 판별 CLI | 동의어확장·충돌패턴·카테고리분류 |
| `archive-menu.py` | 계층형 대화 메뉴 (검색/인테이크/현황/참조) | TUI |
| `archive-note.py` | 기존 아티클에 날짜별 후속 한 줄 추가(「📌 후속 기록」) — 태그 짝·아티클 수 검사·백업 | 안전 편집 |
| `archive-server.py` | 로컬 AI 검색 서버 (Claude API 우선+CLI 폴백 이중경로, BM25 랭킹) | 기본=API 키 불요(claude -p CLI). `ANTHROPIC_API_KEY`(env 또는 로컬 전용 키파일) 설정 시 API 직접호출로 더 빠르게 동작, 실패/미설정 시 자동 CLI 폴백(`ARCHIVE_SERVER_FORCE_CLI=1`로 CLI 강제 가능). rank_bm25 의존(미설치 시 term-count fallback). `--share`로 LAN 공유. 개인=127.0.0.1, 공유=0.0.0.0 바인딩 |
| `1_서버_개인모드.bat` | 개인 모드 기동 (localhost) | CP949 인코딩 / 더블클릭 실행 |
| `2_서버_공유모드.bat` | 공유 모드 기동 (`--share`) | 콘솔에 LAN 링크·방화벽 안내 표시 |
| `3_종료_개인모드.bat` | 개인 모드만 종료 (127.0.0.1:5174) | netstat→taskkill |
| `4_종료_공유모드.bat` | 공유 모드만 종료 (0.0.0.0:5174) | netstat→taskkill |
| `5_종료_전체.bat` | 켜진 서버 전부 종료 (:5174) | netstat→taskkill |
| `conversations.jsonl` | 대화 로그 (자동 생성) — 질문/답변/시각/IP/참조 | 1줄=1대화 JSONL. 검증 대화 사후 검토용. 민감정보 미입력 원칙 |
| `task-board.html` | (운영레이어) 무서버 대시보드 — 칸반 3보드(일회성·정기·문의), 정본 `tasks.md` 미러 | 상세 05·07 |
| `tasks.md` | (운영레이어) 프로젝트 태스크 정본 — 마크다운 칸반·상세 | 상세 07. 규모 커지면 아래 인덱스 생성기 병행(2026-08-25~) |
| `inquiry-log.js` | (운영레이어) 문의이력 데이터 — append-only id-merge push-log | ⚠️ 헬퍼 전용. 상세 05·07 |
| `metrics.html` | (운영레이어) 실증지표 — `inquiry-log.js`를 읽어 문의 처리 건수·소요 등을 브라우저에서 자동 집계(폴링 없음, 완료 기록 시 새로고침만) | 상세 05·07. 2026-09-07 총점검 F2로 등재 |
| `log-inquiry.py` | (운영레이어) 문의 로그 헬퍼 CLI — 1줄 append + id-merge + OS락 | `--new` 는 락을 쥔 채 빈 id 선택(같은 초 겹침 시 1초씩 밀기 — 병합 방지). 상세 07 |
| `board-saver.py` | (운영레이어) 대시보드 저장 서버 — 브라우저 💾 저장을 받아 `task-board.html`·`inquiry-log.js` 원본을 **경로 대화상자 없이 그 자리에 덮어쓰기** | **127.0.0.1 전용 쓰기 API — LAN 공개 금지.** 검증(TASKS 배열·문서끝·크기 50%↓ 차단)+백업(.prev/일자별)+원자적 교체. 꺼져 있으면 브라우저 FSA 저장으로 폴백. 상세 07·CHANGELOG 2026-09-08 |
| `intake-server.py` | (운영레이어) **사내망 문의 접수 서버** — 현업이 브라우저로 직접 등록(「문의하기」 — 글 사이 스크린샷 입력칸)하고 「내 문의함」에서 **본인 문의만** 대화 턴으로 조회·추가 질문. 포트 5179 · 0.0.0.0 | **쓰기는 신규 등록·본인 추가 질문 둘뿐**(스크린샷은 이 두 요청에 함께 실림 · 수정·상태변경·삭제 엔드포인트 없음). 스크린샷은 공유본 밖 저장·종결 시 삭제. 담당자 대시보드·`inquiry-log.js` 원본은 **서빙하지 않는다**. 기록은 `log-inquiry.py` 경유. 등록·추가 질문·그림 정리는 쓰기 잠금 하나로 직렬화. 상세 07 R10·R11·R15 |
| `vacation/mode.py` | (운영레이어) 부재중 모드(원표봇) 원클릭 on/off — 처리 기준(`seen.json`, 켜기 전 미답변 = backlog) 먼저 심기 → ①두 서버(접수·저장) 기동 ②PC 무중단 설정 ③감시자 기동 / resume(로그인 시 — 켜져 있을 때만 두 서버·감시자) / off 시 설정 원복·복귀 보고서(서버는 끄지 않음) | 보고서는 journal 기반(LLM 호출 없음) — 「담당자용 메모」·「담당자가 답했던 건에 붙은 추가 질문」 포함. 상세 07 R14 |
| `vacation/watcher.py` | (운영레이어) 감시자 — 로그 파일 변경 이벤트(45초 디바운스)로만 헤드리스 에이전트(읽기 도구만 · 스크린샷은 Read 로 직접 봄) 호출 → 판정 JSON | 대기 중 비용 0. 처리 대상 = 물은 만큼 답하지 못한 건(턴 수). 시도는 내용 한 벌당 3회. 로그 쓰기 없음(게이트 경유). 두 서버 health_check(창 없이 되살림). 담당자 판정 되먹임 — 매 호출 프롬프트에 「선례 판정 · 교정 노트」(보완·틀림 메모 · 맞음 목록 · 처리 문의의 이전 판정). 조사 순서에 관련 작업 카드(키워드 검색 → 인덱스 라인범위로 bounded read, R21) 포함. 행동 로그(stream-json → runs · journal behavior) · 호출 격리(전용 설정 파일: 훅 끔 + 셸·쓰기·하위 에이전트·개발계 100 차단 · 웹 조사는 제한 허용 — 검색어 점검). 상세 07 R18 · R19 · R21 |
| `vacation/servers.py` | (운영레이어) 두 서버(접수 5179 · 저장 5178)를 창 없이 띄우는 한 곳 — 켜기·재개·감시자 점검이 모두 부른다 | 부팅 자동시작 없음 — 서버는 휴가모드가 켜고 지킨다. 출력은 런타임 로그 파일(부른 쪽 파이프를 물려받지 않게). 상세 07 R17 |
| `vacation/ledger.py` | (운영레이어) 원표봇 답변 검증 장부 — journal `answered` + 문의의 판정(`botgrade` 맞음·보완·틀림)으로 현업 문의 기준 정확도 산출 → 런타임 `원표봇_검증장부.md` | 읽기 전용(장부 파일만 씀) · LLM 호출 없음 · 판정은 현업 화면에 안 나감 · 판정 입력 = 대시보드 수정폼 또는 기록 도구 `--grade`. 권한 확대의 근거 — 설정 `stages` 로 지금 단계·다음 단계까지 남은 것 계산(승격은 사람). 시험 = 담당자 본인 + `test_reqs`. 상세 07 R18 · R20 |
| `vacation/engines.py` | (운영레이어) **엔진 어댑터** — 실행 인자·환경·전용 설정 파일 생성, 출력 정규화(기존 스트림 결과와 같은 모양), 논리 도구 이름 ↔ 엔진별 실제 이름 매핑, 격리 증명 관문 | 기본 엔진은 종전과 **바이트 동일**(골든 시험이 대조). 미증명 엔진은 `check_usable` 이 기동 거부. 상세 07 R22 |
| `vacation/answer_schema.py` · `vacation/schemas/` | (운영레이어) 답 JSON 규격·정규화 — 모델별 변형(최상위 배열·판정 현지어·본문 줄 배열) 흡수 | 규격 밖은 버리지 않고 문제로 기록(journal) · 모르는 판정은 보류로 안전하게. 외부용 JSON Schema 파일 생성. 상세 07 R22 |
| `vacation/tools/mcp_fs_readonly.py` | (운영레이어) 읽기 전용 파일 도구 MCP 서버(read_file·grep·glob) | 쓰기·실행 도구 **미구현** · 허용 폴더 밖은 실제 경로로 차단 · 줄/바이트 상한. 어느 모델이든 같은 도구·같은 제한. 상세 07 R22 |
| `vacation/probe_isolation.py` · `vacation/tests/` | (운영레이어) 격리 실측 도구 + 시험 모음(`run_all.py` 한 줄로 전체) | 격리는 **말이 아니라 흔적**으로 판정(파일이 실제로 생겼는지). 시험은 임시폴더에서 돌아 공유본을 더럽히지 않는다. 상세 07 R22 |
| `vacation/policies/` · `vacation/tests/unit_gemini.py` | (운영레이어) 대체 엔진 격리 정책(기본 거부 + 읽기·찾기·웹만 허용, 최상위 등급으로 주입) + 그 경로 회귀 시험 | 시험이 매번 「권한 생략 옵션 없음」·「허용 목록 밖 도구 0」을 단언한다. 정책을 넓히려면 격리 실측부터 다시. |
| `_gen_host_rules.py` | (운영레이어) 규칙 정본 → 모델 독립 정본 + 호스트별 규칙 파일 **생성** | 손으로 맞추면 낡는다(실측 4건 누락) → 생성물로 전환하고 점검 스크립트가 신선도를 막는다. 상세 07 R22 |
| `vacation/apply_answer.py` | (운영레이어) 쓰기 게이트 — 원표봇 판정을 `inquiry-log.js` 에 기록하는 유일한 통로 | 표기 강제·항상 「대기」·재조회 확인·journal. note 는 답변에 붙이지 않음(journal → 복귀 보고서 「담당자용 메모」). 접수 확인은 답변란이 빌 때만. 내부 식별자(작업카드·문의·추적 번호) 패턴이 공개 답변에 남으면 정규식으로 걸러 표준 문구로 되돌림(R21). `log-inquiry.py` 경유. 상세 07 R14 · R21 |
| `vacation/config.json` · `vacation/sysmode.ps1` | (운영레이어) 부재중 모드 설정(디바운스·배치·일일 한도·재시도·타임아웃) + PC 무중단 스크립트(AC 절전 해제·자동 업데이트/재부팅 차단 — 변경 전 백업, off 시 원복) | 상세 07 |
| `dashboard-panel.pyw` | (운영레이어) 바탕화면 제어판 — 접수·저장 서버 켜기/끄기 + 휴가모드 시작/복귀 버튼 + 링크·방화벽 상태·문의 건수 | 자식 프로세스는 `python.exe` 로 기동. 부팅 자동시작 토글 없음(두 서버는 휴가모드 몫). 방화벽 표시는 있음/없음/확인 못 함 3상태. 상세 07 |
| `_gen_tasks_index.py` | (운영레이어) `tasks.md` 경량 인덱스 생성기 — 살아있는 카드 목록+카드별 라인범위 추출 + 「대기 근거」 행 파싱 → 「📤 회신·응답 대기」 표(회신기한 경과 감지) | `tasks.md`가 세션 컨텍스트에 안 들어갈 만큼 커졌을 때 도입. 상세 CHANGELOG 2026-08-25 |
| `tasks-index.md` | (운영레이어) 위 생성기의 산출물 — 경량 인덱스 | 세션은 `tasks.md` 전체 대신 이것부터 읽고, 필요한 카드만 라인범위로 부분 읽기 |
| `_check_board_sync.py` | (운영레이어) `tasks.md`↔`task-board.html`(`const TASKS`) **두 벌** 동기화 + **`tasks-index.md` 신선도** 점검 CLI | 누락·잔재·상태불일치·인덱스 낡음 보고, 불일치 시 종료코드 1(자동수정 없음). 인덱스 판정은 mtime + 인덱스 머리말의 글자수/줄수 대조 2중(생성기와 **같은 계산식** 사용). 상세 CHANGELOG 2026-08-25·2026-09-01 |

> **`reference-implementation/`** (이 저장소의 공개 동작본): `archive/`(위 도구들의 익명 실행본 — `archive-server.py`·`archive-intake.py`·`archive-menu.py` + 샘플 `archive.html` 9art/5cat) · `dashboard/`(운영레이어 동작본). 데이터는 전부 가상 샘플. 대시보드는 **별도 전용 레포 `11pyo/ai-collab-dashboard`** 로도 존재. 루트 `AGENTS.md`·`CLAUDE.md`가 새 AI 세션 자동 온보딩을 담당.

## CORE INVARIANTS (절대 깨지면 안 되는 규칙)
- INV1: 데이터 = 단일 HTML. 외부 DB 없음. 이식성·오프라인성 최우선.
- INV2: 아티클은 `<article id="..." data-tags="...">` 구조. id는 안정적·불변(앵커·검색 키).
- INV3: 아티클 추가/삭제 시 3곳 동기화 — ① 사이드바 nav ② 카테고리 카운트 ③ `archive-structure.md`.
- INV4: 민감정보(비밀번호·IP·인증서·계정) 아카이브 저장 금지.
- INV5: 인테이크 전 중복·충돌 검사 (`archive-intake.py`).
- INV6: AI 검색은 기본적으로 로컬 `claude -p` 사용(API 키 불필요) — 사용자가 `ANTHROPIC_API_KEY`를 설정하면 Claude API 직접호출로 전환 가능(선택적, 그 경우 별도 API 과금 발생). 두 경로 모두 결국 Anthropic 서비스로 요청이 나감(로컬 완결 처리가 아님) — "외부 유출 없음"은 "제3의 서비스·별도 계정 불필요"라는 뜻이지 오프라인 처리를 의미하지 않음.
- INV7: **인코딩** — 텍스트/HTML/파이썬 = UTF-8. **Windows 배치(.bat) = CP949 인코딩 + `>nul`/`>/dev/null` 등 리다이렉션 미사용**(린터가 `>/dev/null`로 변형해 cmd에서 깨짐). 파이썬 콘솔 출력은 stdout UTF-8 wrap, cmd 경유 출력은 `chcp 65001` + UTF-8/CP949 폴백 디코드. 한글을 CLI argv로 직접 전달 금지(임시파일/stdin 경유).
- INV8: **블루프린트 동기화** — 프로그램·알고리즘·구조 변경 시 이 블루프린트 + CHANGELOG 동기화 (위 MANDATORY SYNC).
- INV9: 프론트 fetch는 `window.location.origin` 상대경로 (하드코딩 localhost 금지 — LAN 공유 시 타 PC에서 깨짐).
- INV10: **탐색 층은 생성물을 남기지 않는다.** 색인(T-Code·테이블·주제·최근)은 로드 시 DOM에서 계산하고 파일에 쓰지 않는다. 주입 DOM은 전부 `data-noexport`, 뷰 상태는 클래스로만(저장 시 strip) — **정본은 한 벌, 보기만 여러 개**. 색인을 파일로 뽑아 사람이 손으로 유지하는 순간 이 불변식이 깨진다(드리프트·AI 속도 저하의 원인).
- INV11: **무인 AI 에이전트는 직접 쓰지 않는다.** 부재중 모드(원표봇)의 에이전트는 읽기 도구 + 판정 JSON 만, 기록은 단일 쓰기 게이트(표기 강제·항상 「대기」·재조회 확인) 한 곳. 처리 대상은 건별 상태(물은 만큼 답했는가)로 판정한다 — 기준선 id 는 seen 유실 시 이미 답한 건의 이중 답변 방지에만 쓴다. 트리거는 이벤트 — 대기 중 LLM 호출 0. 상세 `07-*` R14.
- INV13: **엔진은 격리를 증명한 것만 쓴다.** 무인 실행 엔진을 바꿀 때는 셸·파일쓰기 차단이 그 엔진에서 실제로 먹는지 **시켜 보고 흔적으로 확인**한 뒤에만 연다(자동 개방 금지 — 확인 도구가 틀렸을 때 아무도 모르게 열린다). 엔진 교체 리팩토링의 제1 제약은 기존 경로 **바이트 동일**이며, 골든 스냅샷으로 매 단계 대조한다. 상세 `07-*` R22. **보강(2026-09-22)**: 격리 시험 코드를 바꾸면 그 시험 결과는 증거가 아니다 — 판정 보정으로 통과시키지 말 것. 시간초과·한도 소진은 「판정 불가」이지 통과·실패가 아니다. 권한 확인을 생략하는 실행 옵션은 격리 0으로 간주.
- INV12: **공개 답변에는 사내 내부 식별자를 남기지 않는다.** 원표봇이 참고 자료(선례·작업 카드)에서 얻은 번호·추적 ID·요청자 이름은 판단에만 쓰고 공개 답변에 옮기지 않는다(프롬프트 지시). 쓰기 게이트가 패턴 매칭으로 한 번 더 막아, 지시를 빠뜨려도 표준 문구로 대체된다. 상세 `07-*` R21.

## SCALING TRIGGERS (요약 — 상세는 03 문서)
- N≤200 아티클: BM25(char-2gram) 인메모리 랭킹 (현재 방식) 충분.
- N>200: 동의어맵 유지보수 부담 ↑ → 카테고리 인덱스 분리 검토.
- N>500: 단일 HTML 로딩/검색 비용 ↑ → SQLite FTS5 백엔드로 이전.
- N>1000 또는 의미검색 요구: 임베딩 기반 시맨틱 검색(벡터 인덱스)로 전환 검토. ⚠️단, 실측(2026-07-24, N=96) 결과 범용 다국어 임베딩을 BM25와 대등 결합하면 오히려 R@1 악화(70%→50%) — 이 도메인(Z코드·전문용어 밀도 높은 짧은 글)엔 일반 임베딩이 부적합할 수 있음. 도입 전 자체 라벨셋으로 회귀 테스트 필수(상세: `03-algorithms-scaling.ai.md` §A-1).
