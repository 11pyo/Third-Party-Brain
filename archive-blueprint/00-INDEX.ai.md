---
doc_type: ai_reference
audience: llm_agent
purpose: "검색 가능한 운영 지식 아카이브를 0에서 구축·운영·복제하기 위한 방법론 청사진의 진입점(index)"
canonical_example: "C:/Users/<user>/Documents/SAP SD AI Indexable Archive"
version: 2.0
last_updated: 2026-06-24
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
| `archive-structure.md` | 경량 인덱스 (세션마다 전체 HTML 안 읽도록) | id·제목·라인·카운트 |
| `archive-intake.py` | 신규 정보 인테이크 — 중복·충돌·배치 자동 판별 CLI | 동의어확장·충돌패턴·카테고리분류 |
| `archive-menu.py` | 계층형 대화 메뉴 (검색/인테이크/현황/참조) | TUI |
| `archive-server.py` | 로컬 AI 검색 서버 (Claude API 우선+CLI 폴백 이중경로, BM25 랭킹) | 기본=API 키 불요(claude -p CLI). `ANTHROPIC_API_KEY`(env 또는 로컬 전용 키파일) 설정 시 API 직접호출로 더 빠르게 동작, 실패/미설정 시 자동 CLI 폴백(`ARCHIVE_SERVER_FORCE_CLI=1`로 CLI 강제 가능). rank_bm25 의존(미설치 시 term-count fallback). `--share`로 LAN 공유. 개인=127.0.0.1, 공유=0.0.0.0 바인딩 |
| `1_서버_개인모드.bat` | 개인 모드 기동 (localhost) | CP949 인코딩 / 더블클릭 실행 |
| `2_서버_공유모드.bat` | 공유 모드 기동 (`--share`) | 콘솔에 LAN 링크·방화벽 안내 표시 |
| `3_종료_개인모드.bat` | 개인 모드만 종료 (127.0.0.1:5174) | netstat→taskkill |
| `4_종료_공유모드.bat` | 공유 모드만 종료 (0.0.0.0:5174) | netstat→taskkill |
| `5_종료_전체.bat` | 켜진 서버 전부 종료 (:5174) | netstat→taskkill |
| `conversations.jsonl` | 대화 로그 (자동 생성) — 질문/답변/시각/IP/참조 | 1줄=1대화 JSONL. 검증 대화 사후 검토용. 민감정보 미입력 원칙 |
| `task-board.html` | (운영레이어) 무서버 대시보드 — 칸반 3보드(일회성·정기·문의), 정본 `tasks.md` 미러 | 상세 05·07 |
| `tasks.md` | (운영레이어) 프로젝트 태스크 정본 — 마크다운 칸반·상세 | 상세 07 |
| `inquiry-log.js` | (운영레이어) 문의이력 데이터 — append-only id-merge push-log | ⚠️ 헬퍼 전용. 상세 05·07 |
| `log-inquiry.py` | (운영레이어) 문의 로그 헬퍼 CLI — 1줄 append + id-merge + OS락 | 상세 07 |

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

## SCALING TRIGGERS (요약 — 상세는 03 문서)
- N≤200 아티클: BM25(char-2gram) 인메모리 랭킹 (현재 방식) 충분.
- N>200: 동의어맵 유지보수 부담 ↑ → 카테고리 인덱스 분리 검토.
- N>500: 단일 HTML 로딩/검색 비용 ↑ → SQLite FTS5 백엔드로 이전.
- N>1000 또는 의미검색 요구: 임베딩 기반 시맨틱 검색(벡터 인덱스)로 전환 검토. ⚠️단, 실측(2026-07-24, N=96) 결과 범용 다국어 임베딩을 BM25와 대등 결합하면 오히려 R@1 악화(70%→50%) — 이 도메인(Z코드·전문용어 밀도 높은 짧은 글)엔 일반 임베딩이 부적합할 수 있음. 도입 전 자체 라벨셋으로 회귀 테스트 필수(상세: `03-algorithms-scaling.ai.md` §A-1).
