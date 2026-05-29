---
doc_type: ai_reference
topic: overview_architecture_techstack
version: 1.0
last_updated: 2026-05-29
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
│  Python 도구 계층 (stdlib만, 외부 의존성 0) │
│  - archive-intake.py  : 인테이크 판별 CLI    │
│  - archive-menu.py    : 계층형 TUI          │
│  - archive-server.py  : 로컬 AI 검색 HTTP 서버│
└─────────────────────────────────────────┘
      │
      │ subprocess: claude -p - (stdin)
      ▼
[Claude Code CLI]  ── 로컬 세션 인증, API 키 불요
```

## TECH STACK (의도적으로 최소)
- 데이터/프론트: **순수 HTML5 + 인라인 CSS + 바닐라 JS**. 빌드 스텝 없음. 프레임워크 없음.
- 도구: **Python 3 stdlib만** (`re`, `http.server`, `subprocess`, `json`, `pathlib`, `socket`). pip 설치 0.
- AI: **Claude Code CLI** (`claude -p`), 로컬 로그인 세션 재사용.
- 저장소: 파일시스템. DB 없음.
- 인코딩 정책: 파일 UTF-8. Windows 콘솔 출력은 stdout을 UTF-8 wrap. cmd.exe 경유 출력은 `chcp 65001` 강제 + UTF-8/CP949 폴백 디코딩.

## archive.html 내부 구조
- `<head>`: 인라인 `<style>` 전부. 색상/배지/카드/플로우바 클래스 정의.
- `<nav id="sidebar">`: 카테고리별 아티클 링크. 카테고리당 `<span class="cnt">N</span>` 카운트.
- `<article id="{stable-id}" data-tags="공백구분 키워드">`: 아티클 1개. 헤더(`.ah`>`.at` 제목, `.badge` 카테고리, `.db` 날짜), 태그(`.tags`), 본문 섹션(`.sec`>`.st` 섹션제목 + 내용).
- 카테고리 5종: 기초용어 / 프로세스 / 기술설정 / 트러블슈팅 / 운영참조매뉴얼.
- 재사용 CSS 컴포넌트: `.hl-box`(강조) `.warn-box`(경고) `.info-box`(정보) `.note-box`(참고) `.tip`(팁) `.formula-box`(코드) `.flow-bar`+`.fb`(프로세스 흐름) `.tbl`(표) `.tc`/`.tc-z`(T-Code 인라인) `.term-grid`+`.tc-card`(용어 카드).

## archive-server.py 내부 파이프라인
```
POST /query {query}
  → search_relevant(query)
      → 키워드 추출(정규식) → expand_query(동의어맵) → 본문 정규식 히트 점수
      → 제목/태그 히트 ×3 가중 → 짧은 ASCII코드는 단어경계 매칭 → top_n=3
  → build_prompt(query, contexts)  ── 시스템 규칙 주입 (T-Code 표기법, 미보유 명시, 자동 스크롤 안내)
  → call_claude(prompt)  ── 임시파일 UTF-8 저장 → `chcp 65001 && claude -p -` stdin 파이프
  → JSON {answer, sources[]}
GET /  → archive.html + AI 패널(HTML/CSS/JS) 주입(</body> 직전)
```
- 프론트 패널: 우측 슬라이드 패널. `fetch(window.location.origin + '/query')`. 답변 후 첫 source로 `scrollToArticle()` 자동 스크롤 + 하이라이트 플래시.
- LAN 공유: `--share` 플래그 → `0.0.0.0` 바인딩 → `http://{lan_ip}:5174`. 방화벽 규칙 안내 포함.

## DESIGN RATIONALE
- 단일 HTML: 이메일/USB/파일공유로 즉시 배포, 오프라인 동작, 버전관리 단순.
- stdlib만: 인수인계 받는 비개발자도 `python x.py` 한 줄로 실행 가능.
- 로컬 claude: 사내 데이터가 외부 API로 안 나감 + 비용 0.
