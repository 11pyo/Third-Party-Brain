---
doc_type: ai_reference
topic: overview_architecture_techstack
version: 1.1
last_updated: 2026-07-24
---

# OVERVIEW · ARCHITECTURE · TECH STACK

## SYSTEM SHAPE
```
[archive.html]  ── 단일 파일 지식베이스 (data + UI + CSS + JS, 전부 인라인)
      ▲
      │ 읽기/편집
      │
[archive-structure.md]  ── 경량 인덱스 (LLM이 전체 HTML 안 읽도록)
      ▲
      │ 참조
      │
┌─────┴───────────────────────────────────┐
│  Python 도구 계층 (stdlib 우선 + 선택적 pip) │
│  - archive-intake.py  : 인테이크 판별 CLI    │
│  - archive-menu.py    : 계층형 TUI          │
│  - archive-server.py  : 로컬 AI 검색 HTTP 서버│
└─────────────────────────────────────────┘
      │
      │ ① API 키 있으면: anthropic SDK 직접 호출(더 빠름, prompt caching)
      │ ② 키 없거나 ①실패: subprocess: claude -p - (stdin) 로 자동 폴백
      ▼
[Claude API 또는 Claude Code CLI]  ── ①은 API 키 필요·과금, ②는 로컬 세션 인증·API 키 불요
```

## TECH STACK (의도적으로 최소)
- 데이터/프론트: **순수 HTML5 + 인라인 CSS + 바닐라 JS**. 빌드 스텝 없음. 프레임워크 없음.
- 도구: **Python 3 stdlib 우선** (`re`, `http.server`, `subprocess`, `json`, `pathlib`, `socket`). 검색 랭킹 고도화(`rank_bm25`)와 API 직접호출(`anthropic`)은 선택적 pip 패키지 — 미설치 시 각각 term-count 스코어링·claude -p CLI로 graceful fallback(필수 아님).
- AI: **Claude API 직접호출(anthropic SDK) 우선 + Claude Code CLI(`claude -p`) 폴백**. API 키 없거나 호출 실패 시 자동으로 CLI(로컬 로그인 세션 재사용)로 전환 — 사용자 체감상 항상 응답이 온다. 강제 CLI 전용 모드는 `ARCHIVE_SERVER_FORCE_CLI=1`.
- 저장소: 파일시스템. DB 없음.
- 인코딩 정책: 파일 UTF-8. Windows 콘솔 출력은 stdout을 UTF-8 wrap. cmd.exe 경유 출력은 `chcp 65001` 강제 + UTF-8/CP949 폴백 디코딩.

## archive.html 내부 구조
- `<head>`: 인라인 `<style>` 전부. 색상/배지/카드/플로우바 클래스 정의.
- `<nav id="sidebar">`: 카테고리별 아티클 링크. 카테고리당 `<span class="cnt">N</span>` 카운트.
- `<article id="{stable-id}" data-tags="공백구분 키워드">`: 아티클 1개. 헤더(`.ah`>`.at` 제목, `.badge` 카테고리, `.db` 날짜), 태그(`.tags`), 본문 섹션(`.sec`>`.st` 섹션제목 + 내용).
- 카테고리 5종: 기초용어 / 프로세스 / 기술설정 / 트러블슈팅 / 운영참조매뉴얼.
- 재사용 CSS 컴포넌트: `.hl-box`(강조) `.warn-box`(경고) `.info-box`(정보) `.note-box`(참고) `.tip`(팁) `.formula-box`(코드) `.flow-bar`+`.fb`(프로세스 흐름) `.tbl`(표) `.tc`/`.tc-z`(T-Code 인라인) `.term-grid`+`.tc-card`(용어 카드).

### 탐색 층(Navigator) — 파일을 쪼개지 않고 다중 페이지처럼 (2026-08-20~)
아티클이 100개를 넘으면 롱페이지 하나로는 사람이 못 찾는다. 그렇다고 정본을 파일 여러 개로 쪼개면
"수기 이중 유지"가 생겨 AI 작업이 느려지고 드리프트가 난다. → **정본은 한 벌, 보기만 여러 개**로 해결한다.
`</body>` 직전에 `<style>`+`<script>` 한 블록으로 붙는다(기존 마크업 라인 번호 불변 = `archive-structure.md` 무손상).
- **3 모드** (body 클래스로만 표현): `mode-hub`(색인) / `mode-doc`(한 편만, `:target` 기반 → 딥링크·뒤로가기 유지) / `mode-all`(기존 롱페이지). 검색어 입력 시 `mode-all` 자동 전환.
- **허브 색인 5탭** — 케이스(트러블슈팅 카드) · T-Code · 테이블 · 주제·분류 · 최근. **전부 로드 시 DOM에서 계산**하고 파일에 쓰지 않는다 → 아티클을 추가해도 사람이 갱신할 목록이 0개.
  - T-Code/테이블 역인덱스: 본문·태그를 정규식으로 훑어 수집(`\bZ[A-Z]{1,3}\d{3,4}[A-Z]?\b` + 표준 T-Code/테이블 화이트리스트). `ZT*`=테이블, 그 외 Z=T-Code/프로그램으로 자동 분기.
  - 주제 클러스터: **제목 + 사람이 붙인 태그칩(`.tags .tag`)** 으로 매칭. `data-tags`(AI 검색용 키워드 덤프)로 매칭하면 한 주제가 전체의 절반을 삼켜 색인 구실을 못 한다(실측: 매출품의 62/110 → 33/110).
- **불변식**: ① 주입 DOM은 전부 `data-noexport`(편집·저장 루틴이 제거) ② 상태는 클래스로만(`nav-hide`/`nav-f-hide`/`nav-collapsed`/`nav-on` + body `mode-*`, 저장 시 전부 strip) ③ 아티클 HTML은 한 글자도 건드리지 않는다 ④ 초기화 실패해도 try/catch로 기존 전체 보기 유지.
- **자식 결합자(`>`) 사용 금지**: 아티클이 잘못 닫힌 인라인 태그 안에 중첩될 수 있다(실제 사고: `</strong>`을 `</a>`로 닫아 19개가 `<strong>` 안으로 들어감). `#content article.article` 형태의 후손 선택자를 쓴다.

## archive-server.py 내부 파이프라인
```
POST /query {query, history[]}
  → search_relevant(query)  ── BM25(char-2gram) 랭킹(history 미반영 — 검색 정확도 실측 보존)
      → 키워드 추출(정규식) → expand_query(동의어맵, 발췌 단계에서만 사용)
      → extract_passage top_n=3
  → build_user_content(query, contexts)  ── 질의별 가변 부분(발췌+질문)만
  → call_claude(query, contexts, history)  ── SYSTEM_PROMPT(고정 지침, 캐싱 대상)와 분리해 오케스트레이션:
      ① FORCE_CLI 아니면 call_claude_api() 시도 — anthropic SDK, cache_control ephemeral
      ② 키 없음/실패/빈응답 시 call_claude_cli() 폴백 — 임시파일 UTF-8 저장 →
         `chcp 65001 && claude -p -` stdin 파이프(history는 텍스트로 직렬화해 프롬프트에 포함)
  → JSON {answer, sources[]}
GET /  → archive.html + AI 패널(HTML/CSS/JS) 주입(</body> 직전) — 패널 JS가 최근 3턴(6메시지)을
         conversationHistory에 유지해 후속질문에 맥락 전달(탭 새로고침 시 초기화, 서버측 세션 없음)
```
- 프론트 패널: 우측 슬라이드 패널. `fetch(window.location.origin + '/query')`. 답변 후 첫 source로 `scrollToArticle()` 자동 스크롤 + 하이라이트 플래시.
- LAN 공유: `--share` 플래그 → `0.0.0.0` 바인딩 → `http://{lan_ip}:5174`. 방화벽 규칙 안내 포함.

## DESIGN RATIONALE
- 단일 HTML: 이메일/USB/파일공유로 즉시 배포, 오프라인 동작, 버전관리 단순.
- stdlib만: 인수인계 받는 비개발자도 `python x.py` 한 줄로 실행 가능.
- 로컬 claude(CLI) 기본: 별도 API 키·과금 없이 즉시 동작. API 직접호출은 사용자가 명시적으로 키를 설정해야만 켜지는 선택적 고속 경로(그 경우 Anthropic API 과금 발생) — 기본값은 항상 무과금 CLI.
